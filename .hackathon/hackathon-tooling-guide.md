# Hackathon Tooling Guide

## Harness

- Harness: IBM Bob
- Setup status: Installed
- Commands available: `/setup-hackathon`, `/run-readiness-review`, `/prepare-hackathon-submission`
- Agents available: `readiness-coach`

## What Happens Automatically

Bob automatically loads and exposes hackathon tooling from the project's `.bob/` directory:

- **Slash commands** from `.bob/commands/` are available as `/setup-hackathon`, `/run-readiness-review`, and `/prepare-hackathon-submission`
- **Agent persona** from `.bob/agents/readiness-coach.md` can be invoked directly (e.g., "Use the readiness-coach agent to check my progress")
- **Context files** from `.bob/context/` provide Bob with hackathon overview and file mapping guidance
- **Prompts** from `.bob/prompts/` help structure workflow execution
- **Templates** from `.bob/templates/` provide markdown templates for hackathon artifacts
- **Schemas** from `.bob/schemas/` validate JSON outputs
- **Scripts** from `.bob/scripts/` support repo summary generation and validation
- **Workflows** from `.bob/workflows/` are passive reference files (not slash commands)
- **Rules** from `.bob/rules-*` provide mode-specific guidance for Ask, Plan, Code, and Advanced modes

## What You Run Manually

You decide when to run each hackathon workflow:

| When | Tool | How To Run | What It Produces |
|---|---|---|---|
| After choosing an epic | setup-hackathon | `/setup-hackathon` | `.hackathon/epic.md` |
| During build work | run-readiness-review | `/run-readiness-review` | `.hackathon/readiness-review.md` |
| Near the end | prepare-hackathon-submission | `/prepare-hackathon-submission` | review bundle in `~/dev/hackathon-submissions/` |

## Recommended Flow

1. Run `/setup-hackathon` to choose your epic and create `.hackathon/epic.md`
2. Build your project according to the epic requirements
3. Run `/run-readiness-review` periodically to check completeness and get feedback
4. When ready to submit, run `/prepare-hackathon-submission` to generate the review bundle

## Notes

- Use fake data only
- Do not expose customer data
- Do not expose secrets, tokens, or credentials
- Keep participant-facing outputs score-free and review-focused
- The `.hackathon/` and `.hackathon-tools/` folders should be git-ignored
- Workflow files under `.bob/workflows/` are reference context, not executable commands