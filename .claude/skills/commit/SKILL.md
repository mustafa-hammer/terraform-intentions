---
name: commit
description: Create a git commit for the current changes using this project's Conventional Commits format. Use when the user asks to commit, save work, or after completing a unit of work that should be committed.
---

# commit

Create a well-formed commit that follows the project's [Conventional Commits](https://www.conventionalcommits.org/) convention (see `CONTRIBUTING.md`).

## Steps

1. **Inspect** the working tree in parallel:
   - `git status` — what's staged/unstaged/untracked
   - `git diff HEAD` — the actual changes
   - `git log --oneline -10` — recent message style to match
2. **Scope the commit.** If unstaged or untracked changes exist, decide what belongs together. Stage with `git add` (prefer explicit paths over `git add -A` when only some changes belong in this commit). One logical change per commit — split unrelated changes into separate commits.
3. **Write the message** in the format below.
4. **Commit**, then run `git status` to confirm a clean result. Do not push unless asked.

## Message format

```
<type>(<optional scope>): <subject>

<optional body — the "why", wrapped at ~72 cols>
```

- **Subject:** imperative mood ("add", not "added"/"adds"), no trailing period, ≤ ~72 chars.
- **Scope:** optional, lowercase, names the area touched (`webhook`, `plan`, `ci`, `deps`).
- **Body:** include when the *why* isn't obvious from the subject. Explain intent and trade-offs, not a restatement of the diff.

### Allowed types

| Type       | Use for                                            |
| ---------- | -------------------------------------------------- |
| `feat`     | a new feature                                      |
| `fix`      | a bug fix                                          |
| `chore`    | tooling, deps, scaffolding, non-shipping changes   |
| `docs`     | documentation only                                 |
| `refactor` | code change that's neither a fix nor a feature     |
| `test`     | adding or fixing tests                             |
| `ci`       | CI configuration changes                           |
| `perf`     | performance improvements                           |
| `style`    | formatting only (no behaviour change)              |

### Examples

```
feat(webhook): verify X-Tfc-Task-Signature on incoming run tasks
fix(plan): drop no-op resource changes from the summary
chore: scaffold uv project with ruff, mypy, and pytest
docs: document branch naming and Conventional Commits
```

## Guidelines

- Match the type to the change; when a commit spans types, it's usually two commits.
- Don't commit secrets, `.env` files, or generated artifacts that should be git-ignored.
- If pre-commit hooks modify files during the commit, re-stage and retry.
- When the commit is authored with Claude Code, keep the trailer the harness adds.
