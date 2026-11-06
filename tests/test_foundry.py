"""Functional tests use isolated workspaces and never install into a real home."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills/agent-foundry"
SCRIPT = PACKAGE / "scripts/foundry.py"
spec = importlib.util.spec_from_file_location("foundry", SCRIPT)
foundry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(foundry)


class FoundryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="foundry tests ")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args):
        proc = subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True, timeout=20)
        self.assertFalse(proc.stderr, proc.stderr)
        return proc.returncode, json.loads(proc.stdout)

    def initialize(self):
        foundry.init_repository(self.root, "sample-project", True)
        return self.root / ".agent/repository.json"

    def update_manifest(self, update):
        path = self.initialize()
        data = json.loads(path.read_text())
        update(data)
        path.write_text(json.dumps(data))
        return data

    def test_dry_run_has_no_filesystem_effect(self):
        target = self.root / "new repo"
        code, result = self.run_cli("init", "--root", target, "--name", "sample-project")
        self.assertEqual(code, 0)
        self.assertEqual(len(result["data"]["files"]), 3)
        self.assertFalse(target.exists())

    def test_init_preserves_native_source_and_reports_setup_needed(self):
        source = self.root / "main.rs"
        source.write_text("fn main() {}\n")
        code, _ = self.run_cli("init", "--root", self.root, "--name", "sample-project", "--apply")
        self.assertEqual(code, 0)
        self.assertEqual(source.read_text(), "fn main() {}\n")
        report = foundry.validate_repository(self.root)
        self.assertTrue(report["valid"])
        self.assertFalse(report["ready"])
        self.assertEqual(len(report["warnings"]), 2)

    def test_conflict_does_not_partially_create_manifest(self):
        instructions = self.root / "AGENTS.md"
        instructions.write_text("Preserve these instructions.")
        code, result = self.run_cli("init", "--root", self.root, "--name", "sample-project", "--apply")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(instructions.read_text(), "Preserve these instructions.")
        self.assertFalse((self.root / ".agent").exists())

    def test_rolls_back_files_created_before_write_error(self):
        original = Path.open
        def failing_open(path, *args, **kwargs):
            if path.name == "second.txt":
                raise OSError("simulated write failure")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", failing_open):
            with self.assertRaises(OSError):
                foundry.write_new_files(self.root, {"first.txt":"one", "second.txt":"two"}, True)
        self.assertFalse((self.root / "first.txt").exists())

    def test_inspection_finds_nested_ecosystems_without_reading_code(self):
        (self.root / "pyproject.toml").write_text("deliberately invalid TOML")
        (self.root / "web").mkdir()
        (self.root / "web/package.json").write_text("not JSON")
        (self.root / "node_modules").mkdir()
        (self.root / "node_modules/package.json").write_text("ignored")
        report = foundry.inspect(self.root)
        self.assertEqual({m["ecosystem"] for m in report["native_manifests"]}, {"python", "javascript"})
        self.assertEqual(len(report["native_manifests"]), 2)

    def test_inspection_limit_is_explicit(self):
        for n in range(3):
            (self.root / f"{n}.txt").write_text("x")
        report = foundry.inspect(self.root, 2)
        self.assertEqual(report["files_examined"], 2)
        self.assertTrue(report["truncated"])

    def test_unknown_manifest_fields_rejected(self):
        self.update_manifest(lambda d: d.update(unexpected=True))
        with self.assertRaises(foundry.FoundryError):
            foundry.validate_repository(self.root)

    def test_traversal_paths_rejected(self):
        for path in ("../escape", "/tmp/escape", "C:/escape", "..\\escape"):
            with self.subTest(path=path), self.assertRaises(foundry.FoundryError):
                foundry.contained(self.root, path)

    def test_duplicate_module_ids_rejected(self):
        self.update_manifest(lambda d: d["modules"].append(d["modules"][0]))
        with self.assertRaises(foundry.FoundryError):
            foundry.validate_repository(self.root)

    def test_missing_context_rejected(self):
        self.update_manifest(lambda d: d.update(context=["missing.md"]))
        with self.assertRaises(foundry.FoundryError):
            foundry.validate_repository(self.root)

    def test_unknown_verification_command_rejected(self):
        self.update_manifest(lambda d: d.update(verification=["nonexistent"]))
        with self.assertRaises(foundry.FoundryError):
            foundry.validate_repository(self.root)

    def test_command_resolution_never_executes_payload(self):
        marker = self.root / "must-not-exist"
        def configure(data):
            data["commands"] = [{"id":"test", "cwd":".", "purpose":"Fixture",
                                 "argv":[sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"]}]
            data["verification"] = ["test"]
        self.update_manifest(configure)
        code, report = self.run_cli("command", "--root", self.root, "--id", "test")
        self.assertEqual(code, 0)
        self.assertFalse(report["data"]["executed"])
        self.assertFalse(marker.exists())
        self.assertTrue(foundry.validate_repository(self.root)["ready"])

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(foundry.FoundryError):
            foundry.parse_json('{"name":"a","name":"b"}')

    def test_nonfinite_json_rejected(self):
        with self.assertRaises(foundry.FoundryError):
            foundry.parse_json('{"value":NaN}')

    def test_schema_unknown_keyword_not_silently_ignored(self):
        with self.assertRaises(foundry.FoundryError):
            foundry.check_schema({}, {"type":"object", "madeUp":True})

    def test_scaffold_requires_real_procedure(self):
        with self.assertRaises(foundry.FoundryError):
            foundry.scaffold_skill(self.root, "test-skill", "Useful description", "", True)
        self.assertFalse((self.root / "test-skill").exists())

    def test_generated_skill_validates_with_quoted_punctuation(self):
        foundry.scaffold_skill(self.root, "contract-review", 'Review contracts: "required" fields.',
                               "# Review\n\nCompare the supplied snapshots and cite changed fields.", True)
        report = foundry.validate_skill(self.root / "contract-review")
        self.assertTrue(report["valid"])
        self.assertEqual(report["behavioral_evaluation"], "not_run")

    def test_missing_relative_reference_rejected(self):
        foundry.scaffold_skill(self.root, "test-skill", "Review contracts", "Read [rules](references/missing.md).", True)
        with self.assertRaises(foundry.FoundryError):
            foundry.validate_skill(self.root / "test-skill")

    def test_other_yaml_profile_reported_as_unsupported(self):
        package = self.root / "test-skill"
        package.mkdir()
        (package / "SKILL.md").write_text("---\nname: test-skill\ndescription: Works\n---\nInstructions\n")
        code, result = self.run_cli("validate-skill", "--path", package)
        self.assertEqual(code, 2)
        self.assertEqual(result["issue"]["code"], "unsupported_frontmatter")

    def test_broken_python_script_rejected(self):
        foundry.scaffold_skill(self.root, "test-skill", "Review contracts", "Instructions", True)
        (self.root / "test-skill/helper.py").write_text("def invalid(:")
        with self.assertRaises(SyntaxError):
            foundry.validate_skill(self.root / "test-skill")

    def test_install_roundtrip_and_existing_install_preservation(self):
        dest = self.root / "managed skills"
        plan = foundry.install(dest, "codex", False)
        self.assertFalse(dest.exists())
        self.assertFalse(plan["applied"])
        foundry.install(dest, "codex", True)
        installed = dest / "agent-foundry"
        self.assertTrue(foundry.validate_skill(installed)["valid"])
        before = (installed / "SKILL.md").read_bytes()
        with self.assertRaises(foundry.FoundryError):
            foundry.install(dest, "codex", True)
        self.assertEqual(before, (installed / "SKILL.md").read_bytes())
        self.assertFalse(list(dest.glob(".foundry-stage-*")))

    def test_missing_root_returns_machine_readable_failure(self):
        code, result = self.run_cli("inspect", "--root", self.root / "absent")
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "failed")
        self.assertIsNotNone(result["issue"])

    def test_invalid_names_rejected(self):
        for name in ("Upper", "../escape", "a--b", "-first", "x"*65):
            with self.subTest(name=name), self.assertRaises(foundry.FoundryError):
                foundry.valid_name(name)

    def test_repository_and_release_package_valid(self):
        self.assertTrue(foundry.validate_skill(PACKAGE)["valid"])
        self.assertTrue(foundry.validate_repository(ROOT)["ready"])


if __name__ == "__main__":
    unittest.main()
