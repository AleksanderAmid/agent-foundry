# Repository workflow

## Inspect before changing structure

Read the target's applicable instructions, native package/build manifests, and
existing test entry points. Run the bounded inspector, then read relevant files
yourself. A filename scan cannot identify all components, generated files, or
build dependencies. It deliberately skips dependency/build directories and
does not parse arbitrary project scripts.

Choose modules around meaningful public behavior and ownership. Keep Go packages,
Cargo workspaces, Maven modules, game engine directories, and other native
conventions. The common interface describes the project; it does not replace it.

## Add the smallest interface

For a project without an existing interface:

```text
python <skill-dir>/scripts/foundry.py init --root <project> --name <project-name>
python <skill-dir>/scripts/foundry.py init --root <project> --name <project-name> --apply
```

The first call plans three files. The second writes them exclusively:
`AGENTS.md`, `.agent/repository.json`, and its schema. Existing source files stay
where they are. Any destination-file conflict blocks generation before writing.
For existing AGENTS.md, integrate the small discovery bridge yourself while
preserving applicable guidance; do not remove it to make the generator succeed.

Generated command lists are intentionally empty: discover real commands from the
project, then configure them. Example command record:

```json
{
  "id": "test",
  "argv": ["python", "-m", "unittest", "discover", "-s", "tests"],
  "cwd": ".",
  "purpose": "Run the project's unit tests"
}
```

This example is appropriate only for a project using that test runner. Use the
actual native command. Arguments are arrays, paths are relative POSIX strings,
and `verification` lists required command IDs. Shell operators in an argv array
are literal arguments, not shell syntax. A command requiring a shell needs an
explicit, reviewed shell invocation; Foundry does not execute it for you.

## Verify operational readiness

```text
python <skill-dir>/scripts/foundry.py validate --root <project>
python <skill-dir>/scripts/foundry.py command --root <project> --id test
```

`valid` means the contract matches this version's profile and its declared paths
exist. `ready` means there are no structural readiness warnings. Neither means
the commands ran, the tests discovered cases, or the application is correct.
Run appropriate checks with the agent host, inspect actual outcomes, and preserve
the distinction between pre-existing failures and failures introduced by changes.

## Scaling and Git

Start with the root module. Split only when boundaries improve change planning.
Derive dependency indexes from native tooling rather than maintaining a second
manual graph. For very large projects, partition retrieval outside this minimal
manifest instead of making every agent read thousands of module entries.

Use one task worktree per simultaneous writer when needed. Worktrees do not
isolate ports, databases, external services, or secrets; allocate those separately.
Keep run artifacts out of versioned source. A commit ID alone does not identify
dirty working-tree content: include the actual diff/input identity in verification
evidence when correctness depends on the exact state.

Structural refactoring, dependency installation, publishing, and policy changes
need to remain within the current user's requested scope. Do not infer them from
the presence of this skill.
