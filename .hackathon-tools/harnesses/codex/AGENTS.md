# RTS AI Hackathon Participant Tooling

This project may include hackathon tools at:

```text
.hackathon-tools/
```

Use the tools only when asked for participant-facing hackathon setup, readiness review, or submission preparation.

## Workflows

For `setup-hackathon`, read:

- `.hackathon-tools/AGENTS.md`
- `.hackathon-tools/skills/setup-hackathon/SKILL.md`
- `.hackathon-tools/review-commands/setup-hackathon.md`

For `run-readiness-review`, read:

- `.hackathon-tools/AGENTS.md`
- `.hackathon-tools/skills/run-readiness-review/SKILL.md`
- `.hackathon-tools/review-commands/run-readiness-review.md`
- `.hackathon-tools/review-agents/readiness-coach.md`

For `prepare-hackathon-submission`, read:

- `.hackathon-tools/AGENTS.md`
- `.hackathon-tools/skills/prepare-hackathon-submission/SKILL.md`
- `.hackathon-tools/review-commands/prepare-hackathon-submission.md`

## Harness Behavior Guide

When setting up the tools, create or update `.hackathon/hackathon-tooling-guide.md`. Explain that Codex uses this `AGENTS.md` guidance as project context, but the three hackathon workflows are manually invoked by asking Codex to run them.

If `.gitignore` exists during setup, ask before adding `.hackathon/` and `.hackathon-tools/`. If setup creates a Codex-specific hidden folder only for hackathon tooling, ask before adding that folder too. Do not create `.gitignore` solely for hackathon tooling setup.

## Safety

Do not run organizer-only review, scoring, awards, ranking, or cross-team comparison workflows.

Use review, readiness, completeness, evidence, and learning language. Use fake data. Do not expose customer data or secrets. Do not ask teams to save or share AI session transcripts.
