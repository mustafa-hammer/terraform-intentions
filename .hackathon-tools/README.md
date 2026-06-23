# RTS AI Hackathon Tools

Participant-facing workflow pack for the RTS AI Hackathon.

This repo/folder is intended to be copied into a team's hackathon project as:

```text
.hackathon-tools/
```

The tools are project-local on purpose. They are useful for the hackathon, but they should not be installed globally or permanently wired into unrelated repos.

## What Is Included

```text
skills/
  setup-hackathon/SKILL.md
  run-readiness-review/SKILL.md
  prepare-hackathon-submission/SKILL.md
review-commands/
  setup-hackathon.md
  run-readiness-review.md
  prepare-hackathon-submission.md
review-agents/
  readiness-coach.md
epics/
  rts/
  enterpriseos/
templates/hackathon/
  epic.md
  hackathon-tooling-guide.md
  team-profile.md
  learning-notes.md
  readiness-review.md
  review-criteria-concern.md
schemas/
  evidence-manifest.schema.json
  repo-summary.schema.json
scripts/
  generate-repo-summary.py
  validate-review-json.py
harnesses/
  bob/
  github-copilot/
  claude-code/
  codex/
AGENTS.md
manifest.json
.bob/
  commands/
    setup-hackathon.md
    run-readiness-review.md
    prepare-hackathon-submission.md
  agents/
    readiness-coach.md
  context/
  prompts/
  templates/
  schemas/
  scripts/
  workflows/
  rules-ask/
  rules-plan/
  rules-code/
  rules-advanced/
```

Organizer-only workflows are intentionally not included.

Not included:

- `run-submission-review`
- `run-hackathon-chronicle`
- submission reviewer agent
- chronicle agent
- organizer scoring schemas or templates

## How Teams Should Use This

1. Open the team project in your AI coding tool.
2. Copy this folder into the project as `.hackathon-tools/`.
3. Ask the tool to read `.hackathon-tools/AGENTS.md` and use the adapter for the active harness.
4. Run the participant workflow you need:
   - `setup-hackathon`
   - `run-readiness-review`
   - `prepare-hackathon-submission`

### Bob Setup

For Bob, ask it to read:

```text
.hackathon-tools/README.md
.hackathon-tools/AGENTS.md
.hackathon-tools/harnesses/bob/README.md
.hackathon-tools/.bob/README.md
```

Bob should create or refresh the hackathon-managed `.bob/` subdirectories idempotently: commands, agents, context, prompts, templates, schemas, scripts, workflows, and rules. Files under `.bob/workflows/` are reference context, not slash commands. Bob should not require Python, npm, or another runtime just to set up these files.

The copied `.hackathon-tools/` folder must include hidden entries, especially `.hackathon-tools/.bob/`. A shell copy such as `cp -R hackathon-tools/* .hackathon-tools/` can skip hidden folders. If `.hackathon-tools/.bob/` is missing, recopy the whole folder including hidden entries before Bob setup continues.

If `.gitignore` already exists, Bob should ask for approval to add `.hackathon/` and `.hackathon-tools/` if either entry is missing. If Bob creates `.bob/` only for hackathon tooling, it should ask approval to add `.bob/` too. If `.bob/` already existed for the real project, Bob should not add it to `.gitignore` unless you confirm it is only for hackathon tooling. If `.gitignore` does not exist yet, Bob should not create one just for tooling setup; `/setup-hackathon` will ask again when it creates hackathon context.

Example Bob prompt:

```text
Read .hackathon-tools/README.md, .hackathon-tools/AGENTS.md, .hackathon-tools/harnesses/bob/README.md, and .hackathon-tools/.bob/README.md. Verify .hackathon-tools/.bob/ exists; if it is missing, tell me the tools copy likely skipped hidden folders and ask for the original hackathon-tools source path so you can recopy it correctly. Set up the Bob project files, ask for approval to add .hackathon/, .hackathon-tools/, and any Bob-only .bob/ folder to .gitignore if .gitignore exists and those entries are missing, then tell me the next command to run. Do not run /setup-hackathon yet.
```

During setup, the agent should also create or update:

```text
.hackathon/hackathon-tooling-guide.md
```

That guide explains which parts of the hackathon tooling the active harness handles automatically and which tools the team should run manually.

## Suggested `.gitignore`

The `.hackathon/` folder is local working context and should usually be ignored by Git. If `.hackathon-tools/` was copied into the project, ignore that too after the project-local tooling is set up:

```gitignore
.hackathon/
.hackathon-tools/
```

The `.hackathon-tools/` folder can be copied into a project for the hackathon. Teams can remove it after the event if the project continues beyond the hackathon.

## Other Harnesses

This pack includes project-local adapter templates for common harnesses:

- `harnesses/bob/`: pointer to the Bob-native files under `.bob/`; use this when Bob scans `harnesses/`.
- `harnesses/github-copilot/`: merge into project-root `.github/copilot-instructions.md`. Do not rely on other Copilot prompt files.
- `harnesses/claude-code/`: copy or refresh project-local `.claude/commands/` and merge the `CLAUDE.md` hackathon section if needed.
- `harnesses/codex/`: merge the hackathon section into root `AGENTS.md`.

For any harness, keep the tools project-local and idempotent. Preserve existing project instructions, merge hackathon guidance instead of overwriting it, and ask before adding `.hackathon/`, `.hackathon-tools/`, and newly created hackathon-only harness folders such as `.bob/` or `.claude/` to `.gitignore` when that file exists.

## Workflow Summary

### `setup-hackathon`

Creates or updates `.hackathon/epic.md` after the team chooses an official or custom epic. Also creates or updates `.hackathon/hackathon-tooling-guide.md` so the team knows how to use the tools in the active harness.

Official epic source files are packaged under:

```text
epics/rts/
epics/enterpriseos/
```

Teams should normally choose from the official RTS or EnterpriseOS folders unless organizers tell them otherwise.

### `run-readiness-review`

Creates or replaces `.hackathon/readiness-review.md` with a score-free completeness review.

### `prepare-hackathon-submission`

Creates or updates team metadata, generates review evidence files, and exports a sanitized review bundle.

## Safety Rules

- Use fake data.
- Do not expose customer data.
- Do not expose secrets, tokens, credentials, private keys, or sensitive internal details.
- Do not ask teams to provide AI session transcripts.
- Do not produce participant-facing scores, rankings, awards, or cross-team comparisons.
- Keep participant-facing language focused on readiness, completeness, review, and learning.
