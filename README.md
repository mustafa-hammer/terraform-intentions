# terraform-intentions

An **advisory** [HCP Terraform / Terraform Cloud](https://developer.hashicorp.com/terraform/cloud-docs)
run task that checks whether a Terraform plan provisions *more* than its pull request says it
will — and warns when the plan and the PR's stated intent don't line up.

## The problem

A PR says "add an S3 bucket," but the plan it produces also stands up an RDS instance, an IAM
role, and a security group. Plan output is long and easy to rubber-stamp, so reviewers skim the
description, approve, and the extra infrastructure slips through. "What the PR claims" and "what
the plan does" quietly drift apart.

`terraform-intentions` compares the two automatically at plan time and surfaces a warning in the
Terraform Cloud UI when the plan creates resources the PR never mentioned.

## How it works

```
HCP Terraform run reaches post-plan
   └─ POST (HMAC-signed) ──▶ this webhook
                               ├─ verify X-Tfc-Task-Signature (HMAC-SHA512)
                               ├─ read the PR body  (configuration-version ingress-attributes)
                               ├─ read the plan     (plan JSON → compact change summary)
                               ├─ compare intent vs. plan       (LLM verdict — in progress)
                               └─ POST advisory result ──▶ Terraform Cloud
```

It's an **advisory** run task by design: a mismatch shows up as a warning and never blocks an
apply, so there's zero risk to real applies while it iterates.

## Usage

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                   # install
cp .env.example .env                      # then fill in the secrets below
TFI_TFC_HMAC_KEY=... TFI_TFC_TEAM_TOKEN=... \
  uv run uvicorn terraform_intentions.app:app --port 8000
```

Two secrets (see `.env.example`):

- `TFI_TFC_HMAC_KEY` — shared with the run task; verifies each request's signature.
- `TFI_TFC_TEAM_TOKEN` — a TFC team token with admin on the workspace; reads the plan JSON and
  the PR body.

Then expose the server (e.g. a tunnel) and register it as an **advisory, post-plan** run task in
Terraform Cloud. Full step-by-step (tunnel + TFC setup, troubleshooting): see
[`docs/RUNNING_LOCALLY.md`](docs/RUNNING_LOCALLY.md).

## Status

Built in thin vertical slices (see [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md)):

- ✅ **Webhook round-trip** — signature verification, immediate 200, async result callback
- 🚧 **Fetch inputs** — read the PR body and reduce the plan to a change summary
- ⬜ **Intention check** — LLM verdict mapping mismatches to an advisory warning
- ⬜ Evals, hardening, deploy

## Tech

Python 3.12 · FastAPI · pydantic · httpx · LangChain *(planned)*. Tooling: uv, ruff, mypy,
pytest. It's also a deliberate learning project for Claude Code, Skills, and LangChain.

## Contributing

Branch naming and Conventional Commits are documented in
[`CONTRIBUTING.md`](CONTRIBUTING.md).
