# Installation and host boundaries

Agent Foundry is self-contained. From a downloaded/cloned release:

```text
python skills/agent-foundry/scripts/foundry.py install --host codex
python skills/agent-foundry/scripts/foundry.py install --host codex --apply
```

The first command previews the destination. The second stages, validates, and
installs a fresh copy. It refuses to replace an existing skill. Codex defaults to
`$CODEX_HOME/skills/agent-foundry`, or `~/.codex/skills/agent-foundry` when unset,
matching the bundled installer used for this release. Some newer host profiles
also discover `~/.agents/skills`; `--host agents` targets that portable root.
Use one effective installation, not duplicate copies in multiple discovered roots.

`--host claude` targets `~/.claude/skills`. `--destination <skills-root>` overrides
the parent destination for a managed or project-specific deployment. The host
parameter selects a path; it does not emulate the host or verify discovery.

The shared package uses standard metadata and ordinary Markdown. Its Codex UI
adapter is `agents/openai.yaml`; implicit selection remains enabled. Claude Code
and other agents can consume the shared body where they support Agent Skills,
but their invocation, permissions, and cloud availability must be checked in the
actual host. This release does not claim live integration testing on every host.

After installation, start a new turn and invoke `$agent-foundry` in Codex or
`/agent-foundry` in Claude Code. If the running host has cached its catalog, start
a fresh session or use its documented refresh mechanism.

For upgrades, inspect and back up local modifications, then replace the package
through the host's managed installer or an explicitly authorized file operation.
The bundled installer intentionally has no destructive force-update option.

Official references:
- [Codex skill authoring](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Agent Skills format](https://agentskills.io/specification)
