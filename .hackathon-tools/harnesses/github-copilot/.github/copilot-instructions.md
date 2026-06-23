# RTS AI Hackathon Participant Tooling

This project may include the hackathon tools pack at:

```text
.hackathon-tools/
```

Use these tools only for participant-facing hackathon setup, readiness review, and submission preparation. Do not run organizer-only review, scoring, awards, ranking, or cross-team comparison workflows.

## Available Participant Workflows

When asked to run a workflow, read and follow the matching files:

- `setup-hackathon`: read `.hackathon-tools/skills/setup-hackathon/SKILL.md` and `.hackathon-tools/review-commands/setup-hackathon.md`
- `run-readiness-review`: read `.hackathon-tools/skills/run-readiness-review/SKILL.md`, `.hackathon-tools/review-commands/run-readiness-review.md`, and `.hackathon-tools/review-agents/readiness-coach.md`
- `prepare-hackathon-submission`: read `.hackathon-tools/skills/prepare-hackathon-submission/SKILL.md` and `.hackathon-tools/review-commands/prepare-hackathon-submission.md`

## Required Local Outputs

- `setup-hackathon` creates or updates `.hackathon/epic.md`, `.hackathon/private/scratch.md`, and `.hackathon/hackathon-tooling-guide.md`.
- `run-readiness-review` creates or replaces `.hackathon/readiness-review.md`.
- `prepare-hackathon-submission` creates or updates `.hackathon/team-profile.md`, `.hackathon/learning-notes.md`, `.hackathon/evidence-manifest.json`, `.hackathon/repo-summary.json`, `.hackathon/changed-files.txt`, and exports a sanitized submission bundle.

## Harness Behavior Guide

When setting up the tools, create or update `.hackathon/hackathon-tooling-guide.md`. Explain that GitHub Copilot loads this `.github/copilot-instructions.md` project guidance automatically, but the three hackathon workflows are manually invoked by asking Copilot to run them.

## Git Ignore

If `.gitignore` exists, ask for approval before adding these entries when missing:

```gitignore
.hackathon/
.hackathon-tools/
```

Do not create `.gitignore` solely for hackathon tooling setup.

If setup creates a harness-specific hidden folder only for hackathon tooling, ask before adding that folder too. Do not ignore an existing project-owned harness folder unless the operator confirms it is only for hackathon tooling.

## Language And Safety

Use review, readiness, completeness, evidence, and learning language. Avoid score, grade, judge, ranking, leaderboard, winner, loser, or award language in participant-facing outputs.

Use fake data. Do not expose customer data, secrets, tokens, credentials, private keys, or sensitive internal details. Do not ask teams to save or share AI session transcripts.
