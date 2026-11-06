---
{
  "name": "agent-foundry",
  "description": "Design, scaffold, or audit agent-first repositories and reusable agent skills. Use when creating a machine-readable repository interface, improving agent context and verification workflows, or packaging a skill from a proven procedure. Excludes ordinary feature implementation and generic code review.",
  "license": "MIT",
  "metadata": {
    "version": "1.0.0"
  }
}
---

# Agent Foundry

Turn a repository or recurring procedure into an interface an agent can discover,
operate, and verify. Preserve the user's native language layout and intended scope.
The bundled helpers require Python 3.11+ and the standard library only.

## Choose the job

- **Repository setup or audit:** read [repository.md](references/repository.md).
  Inspect first; identify actual modules, commands, and acceptance checks.
- **Skill creation or improvement:** read [skills.md](references/skills.md).
  Extract a concrete missing procedure; test positive and negative use cases.
- **Installation or another host:** read [installation.md](references/installation.md).
- **Comparing quality or claiming an improvement:** read
  [evaluation.md](references/evaluation.md). Structural checks are not performance evidence.

## Working sequence

1. Resolve the target workspace, requested outcome, existing instruction files,
   and authorized scope. An ordinary feature request does not require restructuring.
2. Locate this installed skill directory. Use its `scripts/foundry.py` by absolute
   path; the user's current directory is not the skill directory.
3. Inspect with `python <skill-dir>/scripts/foundry.py inspect --root <workspace>`.
   This scans a bounded set of filenames and validates an existing Foundry contract;
   it does not read every file or execute repository commands. A truncated scan
   is partial evidence: narrow the target or explicitly increase the limit.
4. Choose the smallest justified change. The helpers offer dry-run plans for
   `init`, `scaffold-skill`, and `install`; pass `--apply` when the task authorizes
   the concrete change. They refuse to overwrite existing files. If a target
   already has AGENTS.md or a different manifest, adapt it carefully in place
   instead of forcing the generator or replacing its instructions.
5. Validate the artifact, then run the project's relevant real checks within the
   authorized environment. `command` resolves a declared command without executing
   it. Inspect the declaration before using the host's execution tool.
6. Report files changed, checks actually run, their results, and remaining gaps.
   Empty command lists mean setup is incomplete. Never turn a structural pass
   into a claim that the application works or the model performs better.

## Interfaces and limits

Use `python <skill-dir>/scripts/foundry.py --help` for exact CLI arguments.
Every operation emits a JSON envelope; failures exit 2. Mutations default to
planning and preserve existing files. Helpers do not install dependencies,
publish repositories, or run commands from a manifest.

`.agent/repository.json` is this project's versioned convention, not a native
agent standard. The skill generator uses a JSON object inside YAML frontmatter,
a strict YAML-compatible authoring profile. `validate-skill` checks that profile
and direct relative Markdown links; it is not an arbitrary YAML validator,
transitive dependency scanner, or behavioral evaluator.

Keep stable repository facts in the contract and reusable procedures in skills.
Keep run logs, secrets, and mutable task state outside reusable packages. Use
actual host permissions and independent checks for enforcement; prose and
metadata cannot grant authority. Read [research.md](references/research.md) only
when rationale or source attribution is needed.
