# TF-INTENT-001: Terraform Plan Intention Checker - AI-Powered PR Validation

- Epic source: Custom
- Source file or URL: docs/PROJECT_PLAN.md
- Product focus / work area: Terraform Cloud / Infrastructure as Code Governance
- Team: terraform-intentions

## Objective

Build a TFC post-plan run-task webhook that uses AI to verify whether a Terraform plan's infrastructure changes align with the stated intention in the corresponding GitHub PR description, returning advisory warnings when unexpected resources are detected.

## Why It Matters

Prevents infrastructure drift from stated intentions, catches scope creep early, and provides an AI-powered safety check that helps teams maintain alignment between what they say they're doing and what they're actually provisioning. This creates a feedback loop that encourages better PR descriptions and catches unintended infrastructure changes before they're applied.

## Primary Output

A production-ready FastAPI webhook service that integrates with Terraform Cloud as an advisory run task, using LangChain for structured LLM analysis of plan changes vs PR descriptions.

## Expected PR Shape

Add FastAPI webhook endpoints with HMAC signature verification, TFC API integration for fetching plan JSON and PR descriptions, LangChain-based structured verdict generation, pydantic models for payloads and verdicts, pytest test suite with eval fixtures, deployment configuration (Docker/Cloud Run), comprehensive README with architecture diagrams, and demo/setup documentation.

## Definition Of Done

- Webhook accepts TFC post-plan payloads with HMAC verification
- Fetches plan JSON and PR body from TFC APIs (using team token for ingress-attributes)
- Uses LangChain structured output to compare plan vs intention
- Posts advisory verdicts back to TFC with detailed outcomes
- Handles non-PR runs and speculative runs gracefully
- Includes eval fixtures for regression testing
- CI passes (ruff, mypy, pytest)
- Deployed and working against real TFC workspace
- README explains architecture and "why LangChain" honestly

## Stories

### 1. Webhook Foundation & TFC Integration

- Difficulty: Intermediate
- Suggested owner: Comfortable with AI tools
- First useful step: Set up FastAPI endpoint that accepts POST, verifies HMAC signature, and returns 200 immediately
- Building with AI: Use Claude Code to scaffold FastAPI app with pydantic models for TFC payload, implement HMAC-SHA512 verification, add async callback pattern
- Output: Working webhook that receives TFC run-task POSTs, verifies signatures, responds 200, and posts hardcoded "passed" verdict to callback URL

### 2. TFC Data Fetching & Plan Analysis

- Difficulty: Intermediate
- Suggested owner: Comfortable with AI tools
- First useful step: Spike TFC team token access to ingress-attributes endpoint, then implement fetchers for plan JSON and PR metadata
- Building with AI: Use Claude Code to create typed httpx clients for TFC APIs, implement plan JSON reduction (filter resource_changes to creates/updates/deletes/replaces), handle non-PR cases
- Output: Webhook logs PR body and compact plan change summary for each run

### 3. LangChain Verdict Generation

- Difficulty: Intermediate to Advanced
- Suggested owner: AI Builder Lead
- First useful step: Define pydantic verdict model (matches, unexpected_resources, reasoning, severity), create simple LangChain chain with structured output
- Building with AI: Use Claude Code to implement LCEL chain that takes PR body + plan summary and returns structured verdict, map verdict to TFC outcomes format
- Output: Webhook generates AI verdicts comparing plan to PR intention and posts advisory warnings to TFC when mismatches detected

### 4. Prompt Engineering & Evaluation Suite

- Difficulty: Advanced
- Suggested owner: AI Builder Lead
- First useful step: Create pytest fixtures with (PR description, plan JSON, expected verdict) tuples covering edge cases
- Building with AI: Use Claude Code to refine prompts for nuanced cases (updates vs creates, tag-only changes, data sources, replacements), build eval harness
- Output: Comprehensive eval suite that validates verdict quality and catches regressions

### 5. Production Hardening & Deployment

- Difficulty: Intermediate
- Suggested owner: Flex teammate
- First useful step: Add timeouts, retries, structured logging, and error handling to all external calls
- Building with AI: Use Claude Code to containerize app, set up Cloud Run/Fly deployment, migrate secrets to platform secret store, add health checks
- Output: Production-deployed webhook with monitoring, proper secret management, and deployment documentation

## Stretch Goals

- Live GitHub API integration for fresh PR descriptions (vs cached ingress-attributes)
- Support for multiple LLM providers (OpenAI, Anthropic, local models)
- Configurable severity thresholds and custom rules per workspace
- Web UI for viewing verdict history and debugging mismatches
- Integration with Slack/Teams for real-time notifications
- Support for Terraform Cloud agents and private registries
- Multi-workspace deployment with per-workspace configuration

## Review Checklist

- [ ] FastAPI webhook accepts and validates TFC post-plan payloads with HMAC verification
- [ ] Responds 200 immediately and processes verdict asynchronously
- [ ] Fetches plan JSON from TFC API and reduces to compact change summary
- [ ] Fetches PR metadata from TFC ingress-attributes using team token
- [ ] Handles non-PR runs, speculative runs, and missing data gracefully
- [ ] LangChain chain generates structured verdicts with reasoning
- [ ] Posts verdicts to TFC callback URL with appropriate status and outcomes
- [ ] Eval fixtures cover common and edge cases with expected verdicts
- [ ] All tests pass (pytest with respx for API mocking)
- [ ] CI passes (ruff check, ruff format --check, mypy, pytest)
- [ ] Secrets managed securely (env vars, not committed)
- [ ] README explains architecture, setup, and "why LangChain" honestly
- [ ] Deployed to production environment and tested against real TFC workspace
- [ ] Documentation includes setup guide, deployment instructions, and demo examples
- [ ] Code follows project conventions (src/ layout, strict mypy, conventional commits)

## Team Interpretation

We're building this as a learning project focused on Claude Code, LangChain, and Skills development. The project follows a thin-vertical-slice approach (Slices 0-5 in PROJECT_PLAN.md) where each slice delivers working, committable, demoable functionality. We're being honest that this is essentially one structured LLM call and LangChain isn't strictly necessary - we're using it deliberately as a learning goal. The advisory-only enforcement level means zero risk of blocking real applies while we iterate and learn.