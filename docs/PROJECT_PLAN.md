# Terraform Plan ↔ PR Intention Checker — Project Plan

A TFC post-plan **run task** webhook that checks whether a Terraform plan provisions
more infrastructure than the corresponding GitHub PR description implies, and returns
an **advisory** warning to TFC when it does.

Learning goals threaded through the build: **Claude Code**, **Skills**, **LangChain**.

---

## Guiding principles

- **Thin vertical slices.** Every slice ends in a working, committable, demoable state.
- **Public-repo quality bar.** Conventional commits, CI green, tests, README that explains *why*, not just *how*.
- **Advisory only (for now).** Advisory run tasks can't block a run — a "fail" surfaces as a warning. Zero risk of blocking real applies while iterating.
- **Honesty about tools.** This is essentially one structured LLM call. LangChain isn't load-bearing; we use it deliberately because learning it is a goal, and we say so in the README.

---

## Architecture (the corrected mental model)

```
TFC run reaches post-plan
        │  POST run task payload (HMAC-signed)
        ▼
   Your webhook  ── respond 200 immediately ──▶ TFC (else TFC retries)
        │
        ├─ verify X-Tfc-Task-Signature (HMAC-SHA512)
        ├─ GET plan_json_api_url            → what the plan changes
        ├─ GET configuration-versions/{cv}/ingress-attributes
        │                                   → repo + PR number + PR BODY
        ├─ summarize plan changes (pre-LLM reduction)
        ├─ LangChain chain: PR body + plan summary → structured verdict
        └─ POST verdict to task_result_callback_url (passed / failed + outcomes)
```

Key payload fields you receive at post-plan: `access_token`, `plan_json_api_url`,
`configuration_version_id`, `task_result_callback_url`, `task_result_enforcement_level`,
`run_id`, `vcs_branch`, `is_speculative`.

**The important discovery:** the PR description comes straight from TFC's
`ingress-attributes` (`pull-request-body`). No GitHub API needed for v1 — just a TFC
team token to read that endpoint.

---

## Risks / unknowns to settle early

1. **Token (decided).** Use a dedicated **TFC team token** (scoped to read the relevant
   workspace) to read `/configuration-versions/{cv}/ingress-attributes` — not the run-task
   token. Team token over personal: it isn't tied to an individual and survives them leaving.
   Slice 2 spike = confirm that token can read the endpoint on your workspace. This pulls
   **secrets handling forward into Slice 2.**
2. **Stale PR body.** `pull-request-body` is captured when a configuration version is
   ingressed from VCS — i.e. on a **new commit/push** to the PR branch. So a normal
   "edited the PR, pushed a fix" flow refreshes it automatically. But a plain TFC UI
   "re-run" on the same config version reuses the old body, and editing the description
   *without* pushing usually won't trigger a run at all. Fine for v1 (you want the
   description as of the plan). Live fetch from GitHub (using the `identifier` + PR number
   TFC gives you) is a clean v2 — but only worth building if your team edits descriptions
   without pushing, which may be rare enough to skip.
3. **Non-PR / speculative runs.** `is-pull-request` can be false (direct push, manual run).
   Handle gracefully → pass with "no PR to compare."
4. **Async callback + retries.** Respond 200 to the initial POST fast; do the real work and
   post the verdict to the callback URL after. Non-200 on the initial hook makes TFC retry.

---

## Slice 0 — Scaffolding & the quality bar

Set the tone from commit #1.

- [ ] Public repo, LICENSE, README skeleton, `.gitignore`
- [ ] Python project (`uv` + `pyproject.toml`, `src/` layout)
- [ ] Lint/format/type: `ruff` (lint + format) + `mypy`, wired into `pre-commit`
- [ ] CI: GitHub Actions running lint + tests on PR
- [ ] Conventional Commits convention documented in CONTRIBUTING / README
- [ ] `CLAUDE.md` capturing stack, commands, conventions, and guardrails
- [ ] A `commit` **skill** at `.claude/skills/commit/SKILL.md` for conventional commits

**Claude Code:** run `/init` to draft `CLAUDE.md` (keep it short — ~30 lines it'll actually
follow). In current Claude Code, custom commands *are* skills, so make the commit helper a
skill at `.claude/skills/commit/SKILL.md` — it's both `/commit` on demand and auto-invokable.
Optional but slick: a `PostToolUse` hook in `.claude/settings.json` that runs `ruff format`
after each edit, so formatting is never a manual step. **Done when:** empty app, green CI,
clean first commit.

## Slice 1 — Webhook round-trip (no intelligence yet)

- [ ] FastAPI endpoint accepting the run task POST, returns 200 immediately
- [ ] Verify `X-Tfc-Task-Signature` (HMAC-SHA512 of raw body)
- [ ] Parse payload into a typed pydantic model
- [ ] Post a hardcoded `passed` to `task_result_callback_url`
- [ ] Run locally behind a tunnel (cloudflared/ngrok); create the run task in TFC as **advisory**

**Done when:** a real TFC plan triggers your webhook and you see a green advisory check in
the TFC UI. *This is the riskiest integration moment — get it green before adding logic.*

## Slice 2 — Fetch the real inputs

- [ ] Spike: confirm the TFC **team token** can read `ingress-attributes` on your workspace
- [ ] Store the team token + HMAC key as local secrets (env / `.env`, git-ignored)
- [ ] Fetch plan JSON from `plan_json_api_url`
- [ ] Fetch `ingress-attributes` → `pull-request-body`, `pull-request-number`, `identifier`, `is-pull-request`
- [ ] Handle the non-PR case → pass with a note
- [ ] Reduce plan JSON to a compact change summary (`resource_changes` with create/update/delete/replace), dropping no-ops

**Done when:** for a real run, the webhook logs the PR body and the list of resource changes.
Pre-LLM reduction keeps tokens sane and is just good engineering.

## Slice 3 — The naive diff (LangChain enters, deliberately dumb)

- [ ] Define the verdict as a pydantic model: `matches: bool`, `unexpected_resources: list`, `reasoning: str`, `severity`
- [ ] One LangChain chain: (PR body + plan summary) → structured verdict via `with_structured_output`
- [ ] Keep the prompt simple; don't optimize yet
- [ ] Map verdict → callback: matches → `passed`; extra infra → `failed` (advisory warning) with a message
- [ ] Add one or two TFC `outcomes` so findings render nicely in the UI

**Done when:** a PR whose description says "add an S3 bucket" but whose plan *also* creates
an RDS instance produces an advisory warning in TFC that names the RDS instance.

**LangChain note:** introduce LCEL and structured output here. This is the "learn LangChain"
payoff — and the right place in the README to be honest that the SDK alone would also do it.

## Slice 4 — Make it actually good

- [ ] Sharpen the prompt: updates vs creates, tag-only/no-op changes, data sources, replacements
- [ ] **Evals:** a fixtures set of `(description, plan, expected verdict)` run under pytest to catch regressions
- [ ] Robustness: timeouts, retries, idempotency, clean error paths
- [ ] Structured logging / a trace of each decision
- [ ] Richer per-resource `outcomes`

**Done when:** the eval set passes and you trust the verdicts enough to consider mandatory.

## Slice 5 — Skills, deploy, polish

- [ ] **Build a Claude Code Skill that earns its place** — e.g. "scaffold a new eval fixture
      from a real run ID," or "add a new TFC fetcher following our conventions"
- [ ] Containerize; deploy to your target (Cloud Run / Fly / Lambda)
- [ ] Move secrets from local `.env` to your platform's secret store (HMAC key + TFC team token)
- [ ] README finish: architecture diagram, setup, the honest "why LangChain" section

**Done when:** it runs deployed against a real workspace and the repo reads like something
you'd link on a résumé.

---

## How the learning goals map to slices

| Goal | Where it shows up |
|------|-------------------|
| Claude Code | Slice 0 (`CLAUDE.md` via `/init`, the commit skill, a `ruff format` hook); throughout for tests/commits and plan mode |
| LangChain | Slice 3 (LCEL + structured output), deepened in Slice 4 (evals) |
| Skills | From Slice 0 — in current Claude Code, custom commands *are* skills (`.claude/skills/<name>/SKILL.md`); deepened in Slice 5 |

## Suggested first session

Slice 0 end-to-end, then the Slice 1 webhook skeleton up to the first 200 response — stop
before TFC wiring. That's two clean commits and a running server, with the integration
risk quarantined to its own session.
