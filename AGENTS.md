# Agent Foundry

The operational contract is `.agent/repository.json`. Source lives in
`skills/agent-foundry/`; the static website lives in `docs/`.

Run `python -B -m unittest discover -s tests -v` for behavior changes. Validate
the repository and skill with the commands listed in the contract. The runtime
requires Python 3.11+ and the standard library only. Do not introduce a new
runtime dependency without a concrete need.

Keep the installed skill self-contained. The runtime validator intentionally
supports our documented JSON-in-YAML metadata profile, not arbitrary YAML or
all JSON Schema keywords. Preserve that boundary in docs and error messages.

Helpers must not execute commands discovered in a target repository. Mutations
are explicit, refuse overwrites, and must retain the dry-run behavior. Test
invalid inputs and existing-file preservation when changing generators.

The website is plain HTML, CSS, JS, and SVG. Maintain keyboard access, reduced
motion support, and useful content without JavaScript. No analytics or trackers.
