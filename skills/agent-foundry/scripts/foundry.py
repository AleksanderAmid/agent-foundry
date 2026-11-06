#!/usr/bin/env python3
"""Agent Foundry: deterministic repository and skill-package tools. Python 3.11+."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile

VERSION = "1.0.0"
PACKAGE = Path(__file__).resolve().parents[1]
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SKIP = {".git", ".hg", ".svn", "node_modules", ".venv", "venv", "__pycache__",
        "dist", "build", ".next", ".cache", ".aws", ".ssh", "vendor", "target"}
NATIVE = {"pyproject.toml": "python", "package.json": "javascript",
          "Cargo.toml": "rust", "go.mod": "go", "pom.xml": "java",
          "build.gradle": "java", "CMakeLists.txt": "cmake", "Gemfile": "ruby",
          "composer.json": "php", "Package.swift": "swift", "pubspec.yaml": "dart"}


class FoundryError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def require(condition, message, code="invalid_input"):
    if not condition:
        raise FoundryError(code, message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(text):
    def invalid_constant(value):
        raise FoundryError("invalid_input", f"Non-finite JSON number: {value}")
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def read_json(path):
    require(path.stat().st_size <= 2_000_000, f"JSON file too large: {path.name}")
    return parse_json(path.read_text(encoding="utf-8-sig"))


def dump(data):
    return json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def valid_name(value):
    require(isinstance(value, str) and 1 <= len(value) <= 64 and NAME.fullmatch(value),
            "Name must contain lowercase ASCII words separated by single hyphens (1-64 characters).")
    return value


def checked_relative(value):
    require(isinstance(value, str) and value and "\\" not in value and ":" not in value,
            f"Expected a repository-relative POSIX path: {value!r}")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts and "\x00" not in value,
            f"Unsafe relative path: {value!r}")
    return path


def is_link(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def contained(root, relative, must_exist=False):
    rel = checked_relative(relative)
    root = root.resolve()
    current = root
    for part in rel.parts:
        current = current / part
        require(not is_link(current), f"Links/junctions are not supported in this path: {relative}")
    resolved = current.resolve()
    require(resolved.is_relative_to(root), f"Path escapes root: {relative}")
    require(not must_exist or resolved.exists(), f"Missing path: {relative}")
    return resolved


def check_schema(value, schema, location="$", document=None):
    """Validate the closed subset used by our bundled schemas; not a general engine."""
    document = schema if document is None else document
    supported = {"$schema", "$id", "title", "description", "$defs", "$ref", "type",
                 "properties", "required", "additionalProperties", "items", "minItems",
                 "maxItems", "uniqueItems", "minLength", "maxLength", "pattern", "enum", "const"}
    require(set(schema) <= supported, "Unsupported keyword in bundled schema", "schema_error")
    if "$ref" in schema:
        ref = schema["$ref"]
        require(ref.startswith("#/$defs/"), "Only local definition references are supported", "schema_error")
        return check_schema(value, document["$defs"][ref.split("/")[-1]], location, document)
    if "const" in schema:
        require(value == schema["const"], f"{location}: incorrect constant")
    if "enum" in schema:
        require(value in schema["enum"], f"{location}: value is not allowed")
    types = {"object": lambda v: type(v) is dict, "array": lambda v: type(v) is list,
             "string": lambda v: type(v) is str, "boolean": lambda v: type(v) is bool,
             "null": lambda v: v is None}
    if "type" in schema:
        require(schema["type"] in types, "Unsupported schema type", "schema_error")
        require(types[schema["type"]](value), f"{location}: expected {schema['type']}")
    if type(value) is dict:
        require(set(schema.get("required", [])) <= value.keys(), f"{location}: missing required properties")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            require(value.keys() <= props.keys(), f"{location}: unknown properties {sorted(value.keys() - props.keys())}")
        for key in value:
            if key in props:
                check_schema(value[key], props[key], f"{location}.{key}", document)
    if type(value) is list:
        require(len(value) >= schema.get("minItems", 0), f"{location}: too few items")
        require(len(value) <= schema.get("maxItems", sys.maxsize), f"{location}: too many items")
        if schema.get("uniqueItems"):
            require(len({json.dumps(v, sort_keys=True) for v in value}) == len(value), f"{location}: duplicate items")
        for index, item in enumerate(value):
            if "items" in schema:
                check_schema(item, schema["items"], f"{location}[{index}]", document)
    if type(value) is str:
        require(len(value) >= schema.get("minLength", 0), f"{location}: string too short")
        require(len(value) <= schema.get("maxLength", sys.maxsize), f"{location}: string too long")
        if "pattern" in schema:
            require(re.search(schema["pattern"], value) is not None, f"{location}: incorrect string format")


def schema(name):
    return read_json(PACKAGE / "assets" / f"{name}.schema.json")


def validate_repository(root):
    root = root.resolve(strict=True)
    manifest_path = contained(root, ".agent/repository.json", True)
    manifest = read_json(manifest_path)
    check_schema(manifest, schema("repository"))
    valid_name(manifest["name"])
    ids = set()
    for module in manifest["modules"]:
        valid_name(module["id"])
        require(module["id"] not in ids, f"Duplicate module id: {module['id']}")
        ids.add(module["id"])
        require(contained(root, module["path"], True).is_dir(), f"Module is not a directory: {module['path']}")
    commands = set()
    for command in manifest["commands"]:
        valid_name(command["id"])
        require(command["id"] not in commands, f"Duplicate command id: {command['id']}")
        commands.add(command["id"])
        require(contained(root, command["cwd"], True).is_dir(), f"Command cwd is not a directory: {command['cwd']}")
        require(all(arg.strip() and "\x00" not in arg for arg in command["argv"]), "Command has empty or NUL argument")
    require(set(manifest["verification"]) <= commands, "Verification references an unknown command")
    for path in manifest["context"]:
        contained(root, path, True)
    warnings = []
    if not manifest["commands"]:
        warnings.append("No project commands configured. Add real argv commands before claiming operational readiness.")
    if not manifest["verification"]:
        warnings.append("No verification commands selected. Structural validity does not prove project correctness.")
    if not (root / "AGENTS.md").is_file():
        warnings.append("No root AGENTS.md discovery bridge.")
    return {"valid": True, "ready": not warnings, "warnings": warnings, "manifest": manifest,
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()}


def inspect(root, limit=2000):
    root = root.resolve(strict=True)
    require(root.is_dir(), "Workspace root must be a directory")
    discovered, count, truncated = [], 0, False
    def walk_error(error):
        raise FoundryError("filesystem_error", f"Cannot inspect a directory: {error.strerror}")
    for current, directories, filenames in os.walk(root, followlinks=False, onerror=walk_error):
        directories[:] = sorted(d for d in directories if d not in SKIP and not is_link(Path(current) / d))
        for filename in sorted(filenames):
            path = Path(current) / filename
            if is_link(path):
                continue
            count += 1
            if filename in NATIVE:
                discovered.append({"path": path.relative_to(root).as_posix(), "ecosystem": NATIVE[filename]})
            if count >= limit:
                truncated = True
                break
        if truncated:
            break
    contract = None
    if (root / ".agent/repository.json").exists():
        contract = validate_repository(root)
    return {"native_manifests": discovered, "files_examined": count, "truncated": truncated,
            "instructions_present": (root / "AGENTS.md").is_file(), "contract": contract,
            "next_step": "Review existing instructions and native commands; preserve the source layout."}


def write_new_files(root, files, apply=False):
    root = root.resolve()
    require(not root.exists() or root.is_dir(), "Destination must be a directory")
    resolved = {relative: contained(root, relative) for relative in files}
    conflicts = [name for name, path in resolved.items() if path.exists()]
    require(not conflicts, "Existing paths would be overwritten: " + ", ".join(conflicts), "conflict")
    plan = {"applied": apply, "files": sorted(files), "overwrite": False}
    if not apply:
        return plan
    created = []
    try:
        for relative, path in resolved.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            # Recheck the path immediately before exclusive creation.
            contained(root, relative)
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                created.append(path)
                handle.write(files[relative])
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return plan


def init_repository(root, name, apply=False):
    valid_name(name)
    manifest = {"schema_version": "1.0.0", "name": name,
                "modules": [{"id": "root", "path": ".", "purpose": "Primary project module"}],
                "commands": [], "verification": [], "context": []}
    instructions = (
        "# Repository operations\n\n"
        "Read `.agent/repository.json` for module paths, explicit command arguments, "
        "and selected verification checks. Preserve the native source layout.\n\n"
        "Commands are declarations, not authorization. Use the task's authorized scope. "
        "An empty command or verification list means setup is incomplete; discover the "
        "real native commands and configure them before claiming verified completion.\n\n"
        "Record checks actually executed and unresolved failures with each change. "
        "Keep transient run logs and credentials out of source history.\n"
    )
    return write_new_files(root, {"AGENTS.md": instructions,
        ".agent/repository.json": dump(manifest),
        ".agent/schemas/repository.schema.json": dump(schema("repository"))}, apply)


def skill_frontmatter(path):
    text = path.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", text, re.S)
    require(match is not None, "SKILL.md requires a frontmatter block and body")
    try:
        meta = parse_json(match.group(1))
    except json.JSONDecodeError:
        raise FoundryError("unsupported_frontmatter", "This validator checks Foundry's JSON-in-YAML frontmatter profile. Use the host's YAML validator for other skill formats.")
    check_schema(meta, schema("skill-metadata"))
    valid_name(meta["name"])
    require(meta["name"] == path.parent.name, "Skill name must match its folder")
    require(bool(match.group(2).strip()), "Skill instructions cannot be empty")
    return meta, match.group(2)


def validate_skill(root):
    root = root.resolve(strict=True)
    meta, body = skill_frontmatter(contained(root, "SKILL.md", True))
    refs = []
    for target in re.findall(r"\]\(([^)]+)\)", body):
        if re.match(r"https?://", target) or target.startswith("#"):
            continue
        relative = target.split("#", 1)[0]
        require(contained(root, relative, True).is_file(), f"Reference is not a file: {relative}")
        refs.append(relative)
    files = []
    for current, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            require(not is_link(Path(current) / name), "Skill package contains a link/junction")
        for name in sorted(names):
            path = Path(current) / name
            require(path.stat().st_size <= 2_000_000, "Skill file exceeds 2 MB package limit")
            relative = path.relative_to(root).as_posix()
            if name.endswith(".py"):
                compile(path.read_text(encoding="utf-8"), relative, "exec")
            files.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    require(len(files) <= 200, "Skill package exceeds 200-file limit")
    return {"valid": True, "name": meta["name"], "description_characters": len(meta["description"]),
            "body_words": len(body.split()), "references": refs, "files": sorted(files, key=lambda f: f["path"]),
            "behavioral_evaluation": "not_run"}


def scaffold_skill(destination, name, description, procedure, apply=False):
    valid_name(name)
    require(1 <= len(description.strip()) <= 1024, "Description must be 1-1024 characters")
    require(procedure.strip(), "Supply a real procedure; blank scaffolds are not generated")
    root = destination / name
    meta = {"name": name, "description": description, "metadata": {"version": "0.1.0"}}
    body = "---\n" + dump(meta) + "---\n\n" + procedure.strip() + "\n"
    return write_new_files(root, {"SKILL.md": body}, apply)


def install(destination, host, apply=False):
    report = validate_skill(PACKAGE)
    root = destination.expanduser().resolve()
    target = root / report["name"]
    require(not target.exists() and not is_link(target), "Skill destination already exists; no files were replaced", "conflict")
    plan = {"applied": apply, "host": host, "destination": str(target),
            "files": [f["path"] for f in report["files"]], "version": VERSION}
    if not apply:
        return plan
    root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".foundry-stage-", dir=root))
    staged_skill = stage / report["name"]
    try:
        shutil.copytree(PACKAGE, staged_skill, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        validate_skill(staged_skill)
        require(not target.exists(), "Destination appeared during installation", "conflict")
        staged_skill.rename(target)
    finally:
        # Only remove the temporary directory created by this invocation.
        require(stage.parent == root and stage.name.startswith(".foundry-stage-"), "Unexpected staging path")
        shutil.rmtree(stage)
    return plan


def default_install_root(host):
    if host == "codex":
        return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills"
    if host == "claude":
        return Path.home() / ".claude/skills"
    return Path.home() / ".agents/skills"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("inspect", "validate", "command"):
        p = sub.add_parser(action)
        p.add_argument("--root", type=Path, required=True)
        if action == "inspect":
            p.add_argument("--limit", type=int, default=2000)
        if action == "command":
            p.add_argument("--id", required=True)
    p = sub.add_parser("init")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--apply", action="store_true")
    p = sub.add_parser("validate-skill")
    p.add_argument("--path", type=Path, required=True)
    p = sub.add_parser("scaffold-skill")
    p.add_argument("--destination", type=Path, required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--procedure-file", type=Path, required=True)
    p.add_argument("--apply", action="store_true")
    p = sub.add_parser("install")
    p.add_argument("--host", choices=["codex", "claude", "agents"], default="codex")
    p.add_argument("--destination", type=Path)
    p.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "inspect":
            require(1 <= args.limit <= 100_000, "Limit must be between 1 and 100000")
            data = inspect(args.root, args.limit)
        elif args.action == "validate":
            data = validate_repository(args.root)
        elif args.action == "init":
            data = init_repository(args.root, args.name, args.apply)
        elif args.action == "command":
            manifest = validate_repository(args.root)["manifest"]
            found = [c for c in manifest["commands"] if c["id"] == args.id]
            require(bool(found), f"Unknown command id: {args.id}")
            data = {**found[0], "resolved_cwd": str(contained(args.root, found[0]["cwd"])), "executed": False}
        elif args.action == "validate-skill":
            data = validate_skill(args.path)
        elif args.action == "scaffold-skill":
            data = scaffold_skill(args.destination, args.name, args.description,
                                  args.procedure_file.read_text(encoding="utf-8"), args.apply)
        else:
            data = install(args.destination or default_install_root(args.host), args.host, args.apply)
        print(dump({"schema_version": "1.0.0", "tool": "agent-foundry", "version": VERSION,
                    "status": "completed", "operation": args.action, "data": data, "issue": None}), end="")
        return 0
    except (FoundryError, OSError, ValueError, SyntaxError) as error:
        code = error.code if isinstance(error, FoundryError) else "invalid_input"
        print(dump({"schema_version": "1.0.0", "tool": "agent-foundry", "version": VERSION,
                    "status": "blocked" if code in {"conflict", "unsupported_frontmatter"} else "failed",
                    "operation": args.action, "data": None,
                    "issue": {"code": code, "message": str(error)}}), end="")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
