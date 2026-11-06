# Skill authoring workflow

## Identify the missing procedure

Start from a recurring task, a concrete failure, or an actual required workflow.
Record the intended inputs, outputs, nearest confusing tasks, available tools,
and evidence for the procedure. If fixing a tool or adding one repository fact
solves the problem, prefer that smaller intervention.

Write a description that names the intended outcome and distinguishes the nearest
alternative. Test direct requests, paraphrases, missing inputs, negation, and
near misses. Mentioning the same technology is not sufficient reason to activate.

## Write an operational body

Include applicability, input resolution, a short default procedure, conditional
references, completion evidence, and bounded recovery. Specify actual invariants;
leave flexible decisions to the model. Do not add generic programming tutorials.

Use helpers for deterministic parsing, validation, and transformations. References
should say when they are needed. A skill containing network or external mutations
must explain its effect and preserve the user's actual authorization boundaries.

## Generate a real package

Write the actual procedure into a UTF-8 file first. Then:

```text
python <skill-dir>/scripts/foundry.py scaffold-skill --destination <skills-root> --name <name> --description "Specific task and applicability" --procedure-file <procedure.txt>
```

Inspect the plan and add `--apply` when authorized. This creates a complete
instruction-only SKILL.md, not a placeholder workflow. Add references or scripts
only when useful; link references directly from the body.

Foundry writes frontmatter as JSON between `---` delimiters. JSON objects are
valid YAML mappings, so the result uses the Agent Skills format while allowing
dependency-free strict validation. Our profile limits optional metadata to a
version string. This profile is narrower than the open standard; existing YAML
skills are not invalid simply because this validator does not accept them.

```text
python <skill-dir>/scripts/foundry.py validate-skill --path <skills-root>/<name>
```

The check validates metadata, folder naming, direct relative Markdown links,
Python syntax, package limits, and absence of links/junctions. It does not run
helpers or follow every nested reference. For other frontmatter profiles, use
the host's validator instead of converting or deleting supported metadata.

## Establish usefulness

Exercise the real procedure in an isolated workspace. Compare representative
tasks with and without the skill using the same environment and model. Use the
evaluation reference for stronger claims. Keep generated hypotheses separate
from measured results. The generator does not certify model behavior.
