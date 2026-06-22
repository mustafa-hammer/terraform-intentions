# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A TFC post-plan **run-task webhook** that checks whether a Terraform plan provisions more
infrastructure than the corresponding GitHub PR description implies, and returns an **advisory**
verdict to Terraform Cloud. The PR body comes straight from TFC's `ingress-attributes`
(`pull-request-body`) — no GitHub API needed for v1.

Learning goals threaded through the build: **Claude Code**, **Skills**, **LangChain**. Read
`docs/PROJECT_PLAN.md` for the full architecture and the thin-vertical-slice roadmap (Slice 0–5);
it is the source of truth for what to build next and why. The README is honest that this is
essentially one structured LLM call and LangChain isn't load-bearing — keep that framing.

## Commands

Uses [`uv`](https://docs.astral.sh/uv/) + Python 3.12 (pinned in `.python-version`).

```bash
uv sync                        # create .venv, install dev tools, provision Python 3.12
uv run ruff check .            # lint
uv run ruff format .           # format (CI uses --check)
uv run mypy                    # strict type check
uv run pytest                  # all tests
uv run pytest tests/test_x.py::test_name   # a single test
uv run pre-commit install      # enable local ruff + mypy hooks (one-time)
```

CI (`.github/workflows/ci.yml`) runs ruff check, ruff format --check, mypy, and pytest on every PR
and push to `main`; all four must pass. pytest is **CI-only** — pre-commit runs ruff + mypy.

## Conventions

- `src/` layout; package is `terraform_intentions` (importable as `from terraform_intentions import ...`).
- mypy is `strict`; the package ships typed (`py.typed`). Keep new code fully annotated.
- **Branches** and **commits** follow `CONTRIBUTING.md` (`feature/`/`fix/`/`chore/`/`docs/`;
  Conventional Commits). Use the `/branch` and `/commit` skills (`.claude/skills/`) so this stays
  consistent — don't commit directly to `main`.

## Guardrails

- The run task is **advisory only** — a "failed" verdict surfaces as a warning, never blocks an apply.
- Respond `200` to TFC's initial POST immediately; do the real work and POST the verdict to
  `task_result_callback_url` afterward (a non-200 makes TFC retry).
- Verify `X-Tfc-Task-Signature` (HMAC-SHA512 of the raw body) before trusting any payload.
- Handle non-PR / speculative runs gracefully → pass with "no PR to compare."
- Secrets (TFC team token, HMAC key) live in a git-ignored `.env` locally; never commit them.
