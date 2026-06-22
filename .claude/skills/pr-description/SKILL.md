---
name: pr-description
description: Generate a clear pull-request title and description from the branch's commits and diff against main, and optionally open or update the PR. Use when the user asks to open a PR, write a PR description, or prepare a branch for review.
---

# pr-description

Produce a reviewer-friendly PR title and body for the current branch, derived from its actual commits and diff against the base branch (`main`).

## Steps

1. **Gather context** (run in parallel):
   - `git branch --show-current` — the branch (its prefix hints the change type).
   - `git log main..HEAD --oneline` — the commits going into the PR.
   - `git diff --stat main...HEAD` — files and scale of change.
   - `git diff main...HEAD` — the substance, for an accurate summary.
   - `gh pr view --json number,title,body 2>/dev/null` — if a PR already exists, edit it rather than creating a new one.
2. **Write the title:** a single Conventional-Commit-style line (`<type>(scope): subject`), imperative, ≤ ~70 chars — matching the dominant change. See the `commit` skill for types.
3. **Write the body** using the template below. Summarize *why* and *what changed*; ground every claim in the diff — don't invent testing or scope that isn't there.
4. **Apply** (ask which, unless the user already said):
   - New PR: `gh pr create --base main --title "<title>" --body "<body>"`
   - Existing PR: `gh pr edit <number> --title "<title>" --body "<body>"`
   - Pass the body via `--body-file` (a temp file) to preserve markdown/newlines.
5. Print the PR URL.

## Body template

```markdown
## Summary
<1–3 sentences: what this PR does and why it's needed.>

## Changes
- <key change, grouped logically>
- <another change>

## Testing
- <commands run and their result, e.g. `uv run pytest` → green; or "CI covers this">

## Notes
<optional: follow-ups, trade-offs, things reviewers should scrutinise. Omit if none.>
```

## Guidelines

- Keep it scannable — bullets over prose. Scale the body to the change; a one-line fix doesn't need every section.
- The **Testing** section must reflect what was actually run (`ruff`, `mypy`, `pytest`, CI). If nothing was run, say so plainly rather than implying coverage.
- Link related issues with `Closes #N` / `Refs #N` when applicable.
- **No Claude/AI attribution** — do not add a "Generated with Claude Code" footer or any mention of Claude in the title or body.
