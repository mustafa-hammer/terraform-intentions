---
name: prepare-hackathon-submission
description: Use near the end of the hackathon to create or update team-profile.md and learning-notes.md, generate evidence-manifest.json, repo-summary.json, and changed-files.txt, and export a sanitized review bundle. Designed to be idempotent and team-facing.
---

# prepare-hackathon-submission

Use this skill to prepare a team's final review bundle from the local `.hackathon/` working context.

## Required References

Read these before acting:

- `review-commands/prepare-hackathon-submission.md`
- `templates/hackathon/team-profile.md`
- `templates/hackathon/learning-notes.md`
- `schemas/evidence-manifest.schema.json`
- `schemas/repo-summary.schema.json`
- `scripts/generate-repo-summary.py`

## Workflow

1. Follow `review-commands/prepare-hackathon-submission.md`.
2. If `.hackathon/epic.md` is missing, stop and tell the team to run `setup-hackathon`.
3. Create or update `.hackathon/team-profile.md` and `.hackathon/learning-notes.md`.
4. Generate `.hackathon/evidence-manifest.json`.
5. Generate `.hackathon/repo-summary.json` and `.hackathon/changed-files.txt`, preferably with `scripts/generate-repo-summary.py`.
6. Export the bundle to `~/dev/hackathon-submissions/team-slug__epic-slug/`.
7. Copy `review-criteria-concern.md` only if it exists.
8. Validate generated JSON with `scripts/validate-review-json.py` when possible.

## Constraints

- Do not include `diff.patch`.
- Do not copy arbitrary project artifacts by default.
- Do not export `.hackathon/private/`.
- Do not ask for AI session transcripts.
- Use `reviewer_notes`, not `demo_notes`.
- Record verification commands and whether they passed, failed, or could not be run.
- Warn when expected review artifacts are missing, ignored by Git, or not visible in generated file lists.
- Keep the workflow idempotent: show existing values, let the operator keep them, and rewrite generated files deterministically.
