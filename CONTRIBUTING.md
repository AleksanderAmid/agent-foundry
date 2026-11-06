# Contributing

Use Python 3.11 or later. There are no runtime dependencies to install.

```sh
python -B -m unittest discover -s tests -v
python -B skills/agent-foundry/scripts/foundry.py validate --root .
python -B skills/agent-foundry/scripts/foundry.py validate-skill --path skills/agent-foundry
```

For a change, describe the concrete behavior and its verification. Add focused
tests for semantic or filesystem behavior, especially preservation of existing
files and handling of malformed input. Avoid tests tied only to exact prose.

Keep the portable skill self-contained. Document any change to its metadata
profile or repository contract. The dependency-free validator supports only the
keywords used by the bundled schemas; it must reject unsupported keywords rather
than silently ignore them. Changes to the schemas and runtime checks must agree.

The public site is static under `docs/`. Test narrow screens, keyboard interaction,
copy buttons, anchor links, and reduced-motion behavior. Use original local assets;
avoid tracking scripts or network font dependencies.

Describe evaluations honestly: helper tests are deterministic software checks;
the routing fixtures are not measured LLM evaluation results. Include model,
host, task set, configuration, and uncertainty when contributing behavioral data.
