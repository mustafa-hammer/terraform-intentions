---
name: setup-hackathon
description: Use when a hackathon team has chosen an RTS, EnterpriseOS, or custom epic and needs to create or update the local .hackathon/epic.md review context. Normalizes official epics, interviews for custom epics and stories, recommends stretch goals and a Review Checklist, and keeps the setup idempotent.
---

# setup-hackathon

Use this skill to create or update a team's local `.hackathon/epic.md` after the team decides what it will work on.

## Required References

Read these before acting:

- `review-commands/setup-hackathon.md`
- `templates/hackathon/epic.md`
- Current epic catalog files from `rts-epics/*.md` and `enterpriseos-epics/*.md` as needed.

## Workflow

1. Follow `review-commands/setup-hackathon.md`.
2. Create `.hackathon/` and `.hackathon/private/` if missing.
3. Ask before adding `.hackathon/` to `.gitignore`, default yes. At the same step, if `.hackathon-tools/` exists in the project, add `.hackathon-tools/` too unless it is already present.
4. For official epics, list matching catalog files, let the operator choose, normalize the selected epic, and rename `Review Checklist` consistently.
5. For custom epics, interview for epic fields and detailed story descriptions, then map stories into the required fields.
6. Use only the allowed enum values from the command spec.
7. Generate stretch goals and Review Checklist items in the style of the existing epics.
8. If the team disputes the Review Checklist, create or update `.hackathon/review-criteria-concern.md`.
9. Write `.hackathon/epic.md` deterministically using the template.
10. Create or update `.hackathon/hackathon-tooling-guide.md` so the team understands what the active harness handles automatically and what they should invoke manually.

## Constraints

- Do not create transcript folders.
- Do not ask teams to save or share AI session transcripts.
- Do not use score, ranking, or leaderboard language.
- Keep the workflow idempotent: show existing values, let the operator keep them, and avoid duplicate sections.
