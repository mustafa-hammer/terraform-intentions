---
name: run-readiness-review
description: Use during the hackathon to run the team-facing Readiness Coach against the current repo and update .hackathon/readiness-review.md without producing scores, rankings, or awards.
---

# run-readiness-review

Use this skill when a team wants an iterative, score-free completeness check before preparing a submission.

## Required References

Read these before acting:

- `review-commands/run-readiness-review.md`
- `review-agents/readiness-coach.md`

## Workflow

1. Follow `review-commands/run-readiness-review.md`.
2. If `.hackathon/epic.md` is missing, stop and tell the team to run `setup-hackathon`.
3. Inspect the repo and the current `.hackathon/` context.
4. Check Definition of Done, stories, evidence, artifact paths, tests or smoke commands, and safety concerns.
5. Write or replace `.hackathon/readiness-review.md`.

## Constraints

- Do not produce a score.
- Do not produce awards.
- Do not rank or compare teams.
- Do not mutate `.hackathon/epic.md`, `team-profile.md`, or `learning-notes.md`.
- Keep humor optional, positive, and safe.
