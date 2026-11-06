# Evaluation, with claims proportional to evidence

Test these separately:

1. **Package:** parsing, resources, paths, dependency availability, helper behavior.
2. **Host:** discovery at the intended root, correct name/version, invocation,
   actual permissions, and resource availability on that product surface.
3. **Routing:** realistic requests with positive, negative, and overlapping skills.
4. **Execution:** explicitly load the skill to isolate whether its procedure helps.
5. **End to end:** natural discovery plus the actual workflow and verification.

Use paired task states, repeat stochastic runs, and retain infrastructure failures
instead of silently counting only completed runs. Keep hidden evaluation material
outside the task agent's readable environment. A folder named `hidden` provides
no protection. Use deterministic checks when they express the objective.

Track completion, appropriate activation, missed activation, required workflow
fidelity, time, tokens, retries, and unacceptable side effects. Define success
before tuning. Separate correct tool execution from domain findings: a comparison
can finish correctly while detecting a breaking change.

Retest after a model, host, tool, or description change. Re-run the no-skill
baseline: a new model may make an old procedure redundant. Evaluate a skill with
the library it will actually join; overlapping packages can change routing.

The repository's `evaluations/routing.json` is a public development set of prompts
and expected decisions. It is not a benchmark result. The unit tests exercise
deterministic helper behavior. Do not describe either as proof of improved LLM
task completion without actually running the corresponding experiments.
