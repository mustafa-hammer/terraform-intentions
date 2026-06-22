---
name: branch
description: Create a new git branch using this project's naming convention (feature/, fix/, chore/, docs/). Use when the user asks to start a branch, begin new work, or when work is starting on the default branch and should move to its own branch.
---

# branch

Create a branch that follows the project's naming convention (see `CONTRIBUTING.md`). Branches are cut from an up-to-date `main`.

## Steps

1. **Check state:** `git status` and `git branch --show-current`. If there are uncommitted changes that belong with the new work, they can be carried over (a new branch keeps the working tree); otherwise commit or stash first.
2. **Pick the prefix** by the type of work (table below).
3. **Name the branch:** `<prefix>/<short-kebab-description>` — lowercase, hyphen-separated, concise (2–4 words). Describe the *what*, not the ticket number alone.
4. **Create from a fresh `main`:**
   ```bash
   git switch main && git pull --ff-only
   git switch -c <prefix>/<description>
   ```
   If carrying uncommitted work, skip the `main` switch and branch directly: `git switch -c <prefix>/<description>`.
5. Confirm with `git branch --show-current`. Do not push unless asked.

## Prefixes

| Prefix     | Use for                                          | Example                       |
| ---------- | ------------------------------------------------ | ----------------------------- |
| `feature/` | new functionality                                | `feature/webhook-endpoint`    |
| `fix/`     | bug fixes                                         | `fix/hmac-signature-check`    |
| `chore/`   | tooling, deps, scaffolding, non-shipping changes | `chore/project-scaffolding`   |
| `docs/`    | documentation only                               | `docs/readme-architecture`    |

## Guidelines

- One branch per logical change; keep it focused so the eventual PR is reviewable.
- Match the prefix to the dominant change type — it should line up with the Conventional Commit `type` used on the branch (see the `commit` skill).
- Avoid committing directly to `main`; cut a branch first.
