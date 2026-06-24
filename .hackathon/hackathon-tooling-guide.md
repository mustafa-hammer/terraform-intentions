# Hackathon Tooling Guide

## Harness

- Harness: Bob (IBM Bob)
- Setup status: ✅ Complete — commands, agents, and context installed
- Epic: TF-INTENT-001 — Terraform Plan Intention Checker
- Commands available: `/setup-hackathon`, `/run-readiness-review`, `/prepare-hackathon-submission`
- Agents available: `readiness-coach`

## What Happens Automatically

Bob loads the following from the project root `.bob/` directories without any extra steps:

- **Slash commands** from `.bob/commands/` — Bob exposes `/setup-hackathon`, `/run-readiness-review`, and `/prepare-hackathon-submission`.
- **Agent persona** from `.bob/agents/` — Bob uses `readiness-coach` automatically via `/run-readiness-review`, or directly when asked.
- **Context files** from `.bob/context/` — Bob references `hackathon-overview.md`, `file-map.md`, and `harness-behavior.md` when answering hackathon questions.
- **Reusable prompts** from `.bob/prompts/` — Templates for each workflow.
- **Reference workflow** from `.bob/workflows/` — `hackathon-participant-flow.md` is passive context (not a slash command).
- **Mode rules** from `.bob/rules-ask/`, `.bob/rules-plan/`, `.bob/rules-code/`, `.bob/rules-advanced/` — Applied automatically per Bob mode.

## What You Run Manually

Bob does not trigger these automatically. You choose when to run each.

| When | Tool | How To Invoke | What It Produces |
|---|---|---|---|
| Epic finalized (done ✅) | `setup-hackathon` | `/setup-hackathon` | `.hackathon/epic.md`, `.hackathon/private/scratch.md` |
| At any point during build | `run-readiness-review` | `/run-readiness-review` | `.hackathon/readiness-review.md` |
| Near submission time | `prepare-hackathon-submission` | `/prepare-hackathon-submission` | submission bundle at `~/dev/hackathon-submissions/terraform-intentions__tf-intent-001/` |

You can also invoke the readiness-coach agent directly at any time:

```text
Act as the readiness-coach agent and review my project progress.
```

## Recommended Flow for This Project

1. **Now** — Epic is set. Start building Slice 0 or Story 1 (Webhook Foundation).
2. **After each slice** — Run `/run-readiness-review` to check completeness against the Definition of Done.
3. **Near the end** — Run `/prepare-hackathon-submission` to generate `evidence-manifest.json`, `repo-summary.json`, and the submission bundle.

## What Not To Expect

- Bob will not submit anything automatically.
- `.bob/workflows/hackathon-participant-flow.md` is reference context — not a runnable command.
- No scores, rankings, or awards from any participant tool.
- Do not paste AI session transcripts — that is not required or requested.

## Notes

- `.hackathon/` is local working context — add to `.gitignore` when prompted.
- `.hackathon-tools/` is the local tools pack — add to `.gitignore` at the same time.
- `.bob/` was created for hackathon tooling only in this project — consider adding to `.gitignore` too.
- Use fake data. Do not expose customer data or secrets.
- Keep all participant outputs score-free and review-focused.
