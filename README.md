# terraform-intentions

A post-plan [HCP Terraform / Terraform Cloud](https://developer.hashicorp.com/terraform/cloud-docs)
run task that checks whether a Terraform plan matches what its pull request says it will do — and
flags it when the plan and the PR's stated intent don't line up.

> [!NOTE]
> **This is a learning project, not a reference implementation.** It exists to explore building
> with AI — Claude Code, Skills, and LangChain — and much of it was written that way. Treat the
> code as illustrative, **not** as a model of Python best practice or production-grade design.
> Don't copy patterns from here expecting them to be idiomatic or hardened.

## The problem

A PR says "add an S3 bucket," but the plan it produces also stands up an RDS instance, an IAM
role, and a security group. Plan output is long and easy to rubber-stamp, so reviewers skim the
description, approve, and the extra infrastructure slips through. "What the PR claims" and "what
the plan does" quietly drift apart.

`terraform-intentions` compares the two automatically at plan time and surfaces a warning in the
Terraform Cloud UI when the plan and the PR description disagree in **either** direction — the plan
creates resources the PR never mentioned, *or* the PR promises resources the plan doesn't create.
It judges *intent*, so the standard supporting resources a described resource implies (an IAM role
and policy attachment for an EC2 instance profile, say) count as in-scope rather than surprises.

## How it works

```
HCP Terraform run reaches post-plan
   └─ POST (HMAC-signed) ──▶ this webhook
                               ├─ verify X-Tfc-Task-Signature (HMAC-SHA512)
                               ├─ read the PR body  (configuration-version ingress-attributes)
                               ├─ read the plan     (plan JSON → compact change summary)
                               ├─ compare intent vs. plan       (LangChain → structured verdict)
                               └─ POST passed/failed result ──▶ Terraform Cloud
```

The webhook just posts an honest `passed`/`failed`. What a `failed` *does* is up to the run task's
**enforcement level**, which you set when you register it in TFC: **advisory** surfaces a warning,
**mandatory** blocks the apply. Advisory is a safe default while you're evaluating the verdicts;
switch to mandatory once you trust it. If the check itself can't run (LLM/TFC error) it **fails
closed** — posting `failed` with an "inconclusive" note rather than a false pass.

## Usage

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                   # install
cp .env.example .env                      # then fill in the secrets below
TFI_TFC_HMAC_KEY=... TFI_TFC_TEAM_TOKEN=... \
  uv run uvicorn terraform_intentions.app:app --port 8000
```

Three secrets (see `.env.example`):

- `TFI_TFC_HMAC_KEY` — shared with the run task; verifies each request's signature.
- `TFI_TFC_TEAM_TOKEN` — a TFC team token with admin on the workspace; reads the plan JSON and
  the PR body.
- `TFI_ANTHROPIC_API_KEY` — Anthropic API key for the intention-check LLM call. The model
  (`TFI_MODEL_ID`, default `claude-sonnet-4-6`), timeout, and retries are configurable.

Then expose the server (e.g. a tunnel) and register it as a **post-plan** run task in Terraform
Cloud, choosing **advisory** or **mandatory** enforcement to taste. Full step-by-step (tunnel + TFC
setup, troubleshooting): see [`docs/RUNNING_LOCALLY.md`](docs/RUNNING_LOCALLY.md).

## Status

Built in thin vertical slices (see [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md)):

- ✅ **Webhook round-trip** — signature verification, immediate 200, async result callback
- ✅ **Fetch inputs** — read the PR body and reduce the plan to a change summary
- ✅ **Intention check** — LangChain chain returns a structured verdict (bidirectional: extra
  *or* missing resources); mismatches post `failed` with a structured outcome
- ⬜ Evals, hardening, deploy

## Tech

Python 3.12 · FastAPI · pydantic · httpx · LangChain (`langchain-anthropic`). Tooling: uv, ruff,
mypy, pytest. It's also a deliberate learning project for Claude Code, Skills, and LangChain.

A note on LangChain, in the interest of honesty: the intention check is essentially **one
structured LLM call** — a prompt plus `with_structured_output(Verdict)`. The Anthropic SDK alone
would do the same job. LangChain isn't load-bearing here; it's in the stack because exercising
LCEL and structured output is one of the project's explicit learning goals.

## Contributing

Branch naming and Conventional Commits are documented in
[`CONTRIBUTING.md`](CONTRIBUTING.md).
