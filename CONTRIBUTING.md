# Contributing

Thanks for contributing! This project holds a public-repo quality bar: green CI,
typed code, and a clean, readable git history.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
uv sync                  # create the venv and install dev tools (provisions Python 3.12)
uv run pre-commit install  # enable local ruff + mypy hooks
```

Run the checks locally any time:

```bash
uv run ruff check .          # lint
uv run ruff format .         # format (use --check in CI)
uv run mypy                  # strict type check
uv run pytest                # tests
```

## Branch naming

Branch off `main` using a type prefix that matches the work:

| Prefix     | Use for                                          | Example                       |
| ---------- | ------------------------------------------------ | ----------------------------- |
| `feature/` | new functionality                                | `feature/webhook-endpoint`    |
| `fix/`     | bug fixes                                         | `fix/hmac-signature-check`    |
| `chore/`   | tooling, deps, scaffolding, non-shipping changes | `chore/project-scaffolding`   |
| `docs/`    | documentation only                               | `docs/readme-architecture`    |

## Conventional Commits

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <subject>
```

Use the imperative mood in the subject ("add", not "added"). Allowed types:

- `feat` — a new feature
- `fix` — a bug fix
- `chore` — tooling, deps, or other non-shipping changes
- `docs` — documentation only
- `refactor` — code change that neither fixes a bug nor adds a feature
- `test` — adding or fixing tests
- `ci` — CI configuration changes
- `perf` — performance improvements
- `style` — formatting only (no behaviour change)

Examples:

```
feat(webhook): verify X-Tfc-Task-Signature on incoming run tasks
fix(plan): drop no-op resource changes from the summary
chore: scaffold uv project with ruff, mypy, and pytest
docs: document branch naming and Conventional Commits
```

## CI

Every pull request runs `ruff check`, `ruff format --check`, `mypy`, and `pytest`
via GitHub Actions. All four must pass before merge.
