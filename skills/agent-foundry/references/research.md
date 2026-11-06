# Research translated into engineering decisions

This implementation synthesizes two research reports prepared on 6 November
2026: *Agent-first workspace and Git repository organization* and *Creating
optimized skills for LLM agents*. The implementation is an original minimal
framework, not an established universal standard or a proven performance optimum.

| Finding or design concern | Implementation decision |
| --- | --- |
| Native build conventions carry useful meaning | Describe modules; do not move source folders |
| Agents need observable operational facts | A small versioned manifest with explicit argv commands |
| More instruction text is not automatically better | A brief skill entry with conditional references |
| Discovery and execution fail differently | Separate routing cases from functional helper tests |
| Schema validity is weaker than correctness | Report validity, readiness, and behavioral evidence separately |
| Local permissions are not portable | No invented permission-granting metadata or automatic execution |
| Generated prose can add no value | Require a real procedure before scaffolding a skill |

Primary sources worth checking when extending the framework:

- [Agent Skills specification](https://agentskills.io/specification)
- [Skill creation practices](https://agentskills.io/skill-creation/best-practices)
- [Evaluating skill output](https://agentskills.io/skill-creation/evaluating-skills)
- [Codex skill documentation](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI: systematic skill evaluations](https://developers.openai.com/blog/eval-skills)
- [Claude Code skill behavior](https://code.claude.com/docs/en/skills)
- [SkillsBench v4](https://arxiv.org/abs/2602.12670v4)
- [SWE-Skills-Bench v2](https://arxiv.org/abs/2603.15401v2)
- [SkillRouter v5](https://arxiv.org/abs/2603.22455v5)
- [Git worktree documentation](https://git-scm.com/docs/git-worktree)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)

These studies use different tasks, scoring units, models, and invocation methods.
Do not pool their headline gains or claim this implementation reproduces them.
Measure marginal value for the specific model, host, tools, and task distribution.
