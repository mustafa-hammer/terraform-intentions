# run-readiness-review

## Purpose

Team-facing command that runs Readiness Coach against the current project and updates `.hackathon/readiness-review.md`.

This command is for iterative completeness checks. It does not produce a score, ranking, award, or cross-team comparison.

## Invocation

```text
run-readiness-review [--repo-path /path/to/repo]
```

If `--repo-path` is omitted, use the current working directory.

## Idempotency Rules

- If `.hackathon/epic.md` is missing, tell the team to run `setup-hackathon` first.
- If `.hackathon/readiness-review.md` exists, replace it with the current review.
- Do not append duplicate sections.
- Do not mutate `epic.md`, `team-profile.md`, or `learning-notes.md`.

## Review Process

1. Read `.hackathon/epic.md`.
2. Read `.hackathon/team-profile.md` and `.hackathon/learning-notes.md` if present.
3. Inspect relevant repo files and artifacts.
4. Check Definition of Done and stories against visible evidence.
5. Check primary artifact paths for missing, ignored, or untracked files when Git is available.
6. Check whether tests, smoke commands, generated reports, or examples are present and current enough to support review.
7. Check for real secrets, real customer data, unsafe automation, or unsupported product claims.
8. Write `.hackathon/readiness-review.md`.

## Output

Write:

```text
.hackathon/readiness-review.md
```

Use the format in `review-agents/readiness-coach.md`.

## Success Criteria

- `.hackathon/readiness-review.md` exists.
- It has an overall readiness label.
- It lists Definition of Done and story evidence.
- It includes missing evidence and safety notes.
- It does not include a score, ranking, award, or cross-team comparison.
