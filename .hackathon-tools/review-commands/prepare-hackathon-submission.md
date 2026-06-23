# prepare-hackathon-submission

## Purpose

Team-facing command run near the end of the hackathon. It creates or updates team metadata, generates machine-readable evidence files, and exports a sanitized review bundle for organizers.

## Invocation

```text
prepare-hackathon-submission
```

## Idempotency Rules

- If `.hackathon/` is missing, ask the team to run `setup-hackathon` first.
- If files exist, parse current values and show them before prompting.
- Let the operator keep existing values.
- Rewrite generated files deterministically.
- Do not require JSON hand-editing.
- Do not overwrite `review-criteria-concern.md`; copy it only if present.
- Export can overwrite the target bundle after regenerating from current `.hackathon/` values.

## Owned Files

Creates or updates in `.hackathon/`:

- `team-profile.md`
- `learning-notes.md`
- `evidence-manifest.json`
- `repo-summary.json`
- `changed-files.txt`

Reads:

- `epic.md`
- `readiness-review.md` if present
- `review-criteria-concern.md` if present

Exports to:

```text
~/dev/hackathon-submissions/team-slug__epic-slug/
```

## Bundle Contents

```text
epic.md
team-profile.md
learning-notes.md
evidence-manifest.json
repo-summary.json
changed-files.txt
review-criteria-concern.md   # only if present
```

Do not include `diff.patch` in v1.

Do not copy arbitrary project artifacts by default.

## Team Profile Prompting

Create or update `team-profile.md` using `templates/hackathon/team-profile.md`.

Required values:

- Team name.
- Team slug.
- Primary contact.
- Team members.
- Epic selected.
- Epic source.
- Products / areas touched.
- Project repo.
- Branch.
- Preferred review path.
- Reuse/release interest.
- AI experience mix.
- Primary tools used.
- Primary goal.
- Biggest constraint.
- Safety and data statements.
- Notes for reviewers.

Allowed values:

- Epic source: `RTS`, `EnterpriseOS`, `Custom`
- Preferred review path: `Live demo`, `Recorded demo`, `Static artifact review`
- Reuse/release interest: `Yes`, `No`, `Maybe`
- AI experience mix: `Mostly new`, `Mixed`, `Mostly comfortable`, `Mostly advanced`

Do not collect AI team lead or model names by default.

Explain AI experience mix:

> Pick the option that best describes the team overall. This is not used to penalize anyone; it helps reviewers interpret learning notes and team workflow.

## Learning Notes Prompting

Create or update `learning-notes.md` using `templates/hackathon/learning-notes.md`.

Say:

> Short answers are fine. You do not need to paste transcripts.

Required sections:

- AI Usage Summary.
- Useful AI Help.
- Human Review And Corrections.
- Iteration Or Pivot.
- With One More Day.

## Repo Access

Repo and branch are normally required. Ask:

> Can organizers access this repo and branch?

If no, capture `repo_access.organizers_can_access = false` and require `repo_access.access_notes`.

## Repo Summary

Generate `repo-summary.json` and `changed-files.txt` with `scripts/generate-repo-summary.py` when available. The command may be run repeatedly; it rewrites both outputs from the current repo state.

Example:

```bash
scripts/generate-repo-summary.py \
  --repo . \
  --out .hackathon/repo-summary.json \
  --changed-files-out .hackathon/changed-files.txt \
  --base-ref main \
  --head-ref HEAD \
  --primary-path README.md \
  --primary-path reports/example-output.md \
  --verification-command "go test ./..."
```

Use one `--primary-path` for each artifact path the team expects reviewers to inspect. Use `--verification-command` for commands the team actually wants recorded, such as tests, linters, smoke runs, or sample generation. If a command cannot be run in the current environment, record that in `verification.notes` rather than inventing a passing result.

If Git is available:

- Record repo root.
- Record branch.
- Record base/head refs where practical. Use `--base-ref` and `--head-ref` when the intended comparison is known.
- Record changed files. If a base ref is supplied, record changed files between base and head; otherwise record the visible project file list.
- Record line additions/deletions where practical. If a base ref is supplied, use diff stats; otherwise use cumulative repo log stats.
- Include untracked relevant files.

If Git is unavailable:

- Walk the project folder.
- Exclude noisy paths.
- Mark `"git.available": false`.

Record verification:

- `verification.commands_run`: every command attempted, with `passed`, `failed`, or `not-run`.
- `verification.commands_failed`: failed command strings.
- `verification.notes`: prerequisites, skipped commands, or environment limitations.

Warn when:

- A primary artifact path is missing.
- A primary artifact path exists but is ignored by Git.
- A primary artifact path exists but is not tracked or otherwise visible to the generated file list.
- Tests are present but no test or smoke command was recorded.

Common noisy paths:

- `.git/`
- `.hackathon/private/`
- `node_modules/`
- `vendor/`
- `dist/`
- `build/`
- `.venv/`
- `__pycache__/`
- `.DS_Store`

After generation, validate:

```bash
scripts/validate-review-json.py repo-summary .hackathon/repo-summary.json
```

## Evidence Manifest

Generate `evidence-manifest.json` using `schemas/evidence-manifest.schema.json`.

Include:

- Team identity.
- Epic identity.
- Repo and branch.
- Bundle creation date.
- Reviewer notes.
- Repo access.
- Artifact paths.
- Readiness review presence.
- Safety statements.
- Known gaps.

Use `reviewer_notes`, not `demo_notes`.

Do not include a readiness review timestamp.

## Success Criteria

- `.hackathon/team-profile.md` exists.
- `.hackathon/learning-notes.md` exists.
- `.hackathon/evidence-manifest.json` validates against the schema.
- `.hackathon/repo-summary.json` validates against the schema.
- `.hackathon/changed-files.txt` exists.
- Exported bundle exists at `~/dev/hackathon-submissions/team-slug__epic-slug/`.
- Bundle includes the expected files and does not include `.hackathon/private/`.
