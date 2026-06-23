# Hackathon Tooling Guide

This project is set up for the RTS AI Hackathon tools, and contributors use **two harnesses**:
IBM Bob and Claude Code. The same three participant workflows are available in both.

## Harnesses

| Harness | Setup status | Where it loads from | Commands |
|---|---|---|---|
| IBM Bob | Installed | `.bob/` (commands, agents, context, prompts, templates, schemas, scripts, workflows, rules-*) | `/setup-hackathon`, `/run-readiness-review`, `/prepare-hackathon-submission` |
| Claude Code | Installed | `.claude/commands/` + hackathon section in `CLAUDE.md` | `/setup-hackathon`, `/run-readiness-review`, `/prepare-hackathon-submission` |

Both harnesses read the shared tools pack at `.hackathon-tools/` (skills, review-commands,
review-agents, epics, templates, schemas, scripts). That folder is the source of truth — the
harness adapters under `.bob/` and `.claude/commands/` point back into it.

## What Happens Automatically

**Bob** loads and exposes hackathon tooling from `.bob/`:

- Slash commands from `.bob/commands/`
- The `readiness-coach` agent persona from `.bob/agents/` (e.g. "Use the readiness-coach agent to check my progress")
- Context, prompts, templates, schemas, scripts, and `rules-*` provide supporting guidance
- Files under `.bob/workflows/` are passive reference context — **not** slash commands

**Claude Code** discovers project slash commands from `.claude/commands/`, and `CLAUDE.md` carries
a short hackathon section telling it to read `.hackathon-tools/AGENTS.md` when running a workflow.
If project-local slash commands aren't available in your Claude Code setup, ask Claude Code to read
`.hackathon-tools/AGENTS.md` and run the workflow by name.

## What You Run Manually

You decide when to run each workflow. Invocation is the same in both harnesses:

| When | Tool | How To Run | What It Produces |
|---|---|---|---|
| After choosing an epic | setup-hackathon | `/setup-hackathon` | `.hackathon/epic.md` (+ `.hackathon/private/scratch.md`) |
| During build work | run-readiness-review | `/run-readiness-review` | `.hackathon/readiness-review.md` (score-free) |
| Near the end | prepare-hackathon-submission | `/prepare-hackathon-submission` | review bundle in `~/dev/hackathon-submissions/` |

## Recommended Flow

1. Run `/setup-hackathon` to choose your epic and create `.hackathon/epic.md`.
2. Build your project according to the epic requirements.
3. Run `/run-readiness-review` periodically to check completeness and get feedback.
4. When ready to submit, run `/prepare-hackathon-submission` to generate the review bundle.

## Notes

- Use fake data only. Do not expose customer data, secrets, tokens, or credentials.
- Keep participant-facing outputs score-free and review-focused (no rankings, awards, or
  cross-team comparisons).
- This project commits its hackathon tooling (`.bob/`, `.claude/commands/`, `.hackathon/`) so that
  both Bob and Claude Code contributors get it on clone. Whether `.hackathon-tools/` itself is
  committed or git-ignored is a per-project choice — see the project's `.gitignore`.
