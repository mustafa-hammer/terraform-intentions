# Readiness Review

## Overall Readiness

- Status: Nearly ready
- Confidence: High

**Slice 1 (the webhook round-trip) is complete and demonstrably solid.** The FastAPI app, HMAC
verification, async callback pattern, pydantic models, full test suite, CI pipeline, and local-run
documentation are all in place and pass the quality bar set by the epic. The gap keeping this from
`Ready` is that Slices 2–5 (plan fetching, LangChain verdict generation, eval suite, and deployment)
are not yet built — but that's by design in a slice-based project. The epic's Definition of Done
requires all of them, including a live deployment, for full completion.

---

## Definition Of Done Review

| Requirement | Status | Evidence | Gap / Next Action |
|---|---|---|---|
| Webhook accepts TFC post-plan payloads with HMAC verification | Met | `security.py` + `test_security.py`, `app.py` `verify_signature` path, `test_app.py::test_bad_signature_returns_401` | — |
| Fetches plan JSON and PR body from TFC APIs (using team token) | Not met | No TFC fetcher module exists yet | Build Slice 2: `src/terraform_intentions/fetcher.py` + TFC team token config |
| Uses LangChain structured output to compare plan vs intention | Not met | No LangChain dependency or chain code present | Build Slice 3: add `langchain`/`langchain-openai` to `pyproject.toml`, define verdict model, implement LCEL chain |
| Posts advisory verdicts back to TFC with detailed outcomes | Partially met | `callback.py` posts any status/message; currently hardcoded `passed` stub | Wire real verdict from LangChain chain (Slice 3) |
| Handles non-PR runs and speculative runs gracefully | Not met | `models.py` captures `is_speculative`; no handling logic yet | Add graceful pass-through in Slice 2/3 processing path |
| Includes eval fixtures for regression testing | Not met | `tests/` has unit tests for Slice 1 only; no `(description, plan, expected_verdict)` fixtures | Build Slice 4: `tests/evals/` fixtures + eval harness |
| CI passes (ruff, mypy, pytest) | Met | `.github/workflows/ci.yml` runs all four checks on every PR and push to main | — |
| Deployed and working against real TFC workspace | Not met | `docs/RUNNING_LOCALLY.md` covers local tunnel setup; no production deployment config exists | Build Slice 5: Dockerfile, Cloud Run / Fly config, deployment docs |
| README explains architecture and "why LangChain" honestly | Partially met | `README.md` is a single-line stub; `docs/PROJECT_PLAN.md` + `CLAUDE.md` have the content | Flesh out `README.md` with architecture diagram, setup steps, and honest LangChain framing |

---

## Story Review

| Story | Status | Evidence | Gap / Next Action |
|---|---|---|---|
| 1 · Webhook Foundation & TFC Integration | Met | FastAPI `/run-task` + `/healthz`, HMAC verify, pydantic `RunTaskPayload`, async `post_task_result`, `test_app.py` (4 tests), `docs/RUNNING_LOCALLY.md` end-to-end tunnel guide | Confirmed working; Slice 1 is done |
| 2 · TFC Data Fetching & Plan Analysis | Not met | `models.py` captures `plan_json_api_url` and `configuration_version_id`; no fetcher code | Implement `fetcher.py`: httpx calls to `plan_json_api_url` and `ingress-attributes`; reduce `resource_changes`; handle non-PR case |
| 3 · LangChain Verdict Generation | Not met | `pyproject.toml` has no LangChain dependency | Add `langchain` + provider SDK; define `Verdict` pydantic model; implement LCEL chain; map verdict → TFC callback |
| 4 · Prompt Engineering & Evaluation Suite | Not met | No eval fixtures or eval harness | Create `tests/evals/fixtures/` with `(pr_body, plan_json, expected_verdict)` tuples; build `test_evals.py` |
| 5 · Production Hardening & Deployment | Not met | Timeout is configurable (`request_timeout` in `config.py`); no Dockerfile, no platform deployment, no structured logging beyond `logger.info` | Containerize, deploy to Cloud Run / Fly, move secrets to secret store, add structured logging |

---

## Missing Evidence

- **No LangChain code anywhere.** The core AI capability (Slice 3) is not started; `pyproject.toml` lists no `langchain` or LLM provider dependency.
- **No plan fetcher.** Slice 2 data pipeline (`fetcher.py`, TFC API calls, plan JSON reduction) is absent.
- **No eval fixtures.** `tests/` contains only Slice 1 unit tests; no `(description, plan, expected_verdict)` regression fixtures exist.
- **`README.md` is a single line.** The DoD requires a README that explains architecture and the "why LangChain" framing. Content exists in `CLAUDE.md` and `docs/PROJECT_PLAN.md` but has not been written into the README.
- **No Dockerfile or deployment config.** Nothing in the repo points at a running production deployment.
- **No `team-profile.md` or `learning-notes.md`.** These are optional but useful context for reviewers.
- **Slice 1 live confirmation not in repo.** The RUNNING_LOCALLY guide is thorough, but there's no screenshot, recorded run output, or test fixture capturing a real TFC round-trip. A `docs/demo/` folder with a screenshot or log snippet would strengthen evidence.

---

## Safety And Data Notes

- **Secrets are handled correctly.** `.env.example` documents the pattern; `.env` is listed in `.gitignore`; `config.py` uses `pydantic-settings` with `TFI_` prefix. No secrets appear committed.
- **`access_token` is redacted in logs** via `_SENSITIVE_KEYS` in `app.py`. Good practice, confirmed in `test_redact_masks_access_token`.
- **Advisory-only enforcement is architecturally enforced.** The DoD, CLAUDE.md guardrails, and PROJECT_PLAN.md all document this. A "failed" verdict will never block an apply.
- **No real customer data.** Tests use synthetic payloads (`run-abc`, `tok-123`, placeholder URLs).
- **No unsafe automation.** The app only posts verdicts back to TFC; it does not trigger runs, apply changes, or modify workspace state.
- **One minor concern:** `app.py` uses bare `assert` for the post-verification non-None guarantees (`assert payload.access_token is not None`). These are removed by Python's `-O` flag. Not a security issue given the prior `is_verification_event` guard, but worth replacing with explicit checks before the production slice.

---

## Suggested Next Actions

1. **Build Slice 2 (data fetching).** Create `src/terraform_intentions/fetcher.py` with typed `httpx` calls to `plan_json_api_url` and `configuration-versions/{cv}/ingress-attributes`. Add `TFI_TFC_TEAM_TOKEN` to `config.py`. Handle non-PR and speculative cases. Log PR body + compact plan changes.
2. **Add `langchain` + LLM provider dependency and build Slice 3.** Define `Verdict` pydantic model (`matches`, `unexpected_resources`, `reasoning`, `severity`). Wire LCEL chain. Map verdict to callback status. Add Slice 3 tests with `respx` for the TFC APIs and a mocked LLM.
3. **Write `README.md`.** Architecture diagram (the ASCII one from `PROJECT_PLAN.md` works), setup steps (`uv sync`, `.env`, tunnel, TFC run task), and the honest "why LangChain" section. This is a DoD requirement and a public-quality signal.
4. **Build Slice 4 eval fixtures.** At minimum: a PR description + plan that match (should pass), a plan with extra resources not in the PR (should warn), and an edge case (tag-only change, data source only).
5. **Build Slice 5 deployment.** Add `Dockerfile`, pick a target (Cloud Run is mentioned in the epic), document secrets management, confirm a live advisory check appears in a real TFC UI.
6. **Create `team-profile.md` and `learning-notes.md`** in `.hackathon/`. These give reviewers useful context about your learning goals and team composition.
7. **Replace bare `assert` statements** in `app.py` with explicit `if not` guards to be production-safe under `-O`.

---

## Optional Review Pep Talk

Slice 1 is genuinely clean — the kind of "boring foundation done right" that makes the exciting
slices possible. The checklist is being very pedantic about `README.md` being one line, but it
has a fair point this time. The architecture is sound, the tests are honest, and the project is
exactly as far along as a disciplined thin-vertical-slice approach should be at this stage.
Four slices to go. Go build them.
