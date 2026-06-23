# Bob Slash Commands

Bob discovers project slash commands from:

```text
.bob/commands/
```

Bob also discovers project agent definitions from:

```text
.bob/agents/
```

These command and agent files are included here so a team can install hackathon-specific Bob behavior into the root of its project.

## Install Into A Team Project

Install the hackathon-managed `.bob/` subdirectories from `.hackathon-tools/.bob/` into the project root `.bob/` folder:

- `.bob/commands/`
- `.bob/agents/`
- `.bob/context/`
- `.bob/prompts/`
- `.bob/templates/`
- `.bob/schemas/`
- `.bob/scripts/`
- `.bob/workflows/`
- `.bob/rules-*`

This should be idempotent. On repeat setup, refresh those hackathon-managed directories from `.hackathon-tools/.bob/` instead of appending duplicate content. Do not require Python, npm, or another runtime just to install these files.

If a directory already exists because of a previous hackathon tools install, replace that hackathon-managed directory with the current copy from `.hackathon-tools/.bob/`. Preserve unrelated root project files and preserve root project guidance such as `AGENTS.md`.

If `.gitignore` exists in the project root, ask the operator for approval to add `.hackathon/` and `.hackathon-tools/` if either entry is missing. If this setup created `.bob/` only for hackathon tooling, ask approval to add `.bob/` too. If `.bob/` already existed for the real project, do not add it unless the operator confirms it is only for hackathon tooling. The default recommendation is yes. Do not create `.gitignore` solely for Bob harness setup; if no `.gitignore` exists, tell the operator `/setup-hackathon` will ask again when it creates hackathon context.

After that, Bob should expose:

- `/setup-hackathon`
- `/run-readiness-review`
- `/prepare-hackathon-submission`

Bob should also be able to use the `readiness-coach` agent directly:

```text
Use the readiness-coach agent to check my progress.
```

The command files assume the hackathon tools pack exists in the same project at:

```text
.hackathon-tools/
```

## What Lives Here

- `commands/`: slash commands for participant workflows.
- `agents/`: Bob-native agent personas.
- `context/`: shared hackathon context and file map.
- `prompts/`: reusable prompts for setup, readiness review, and submission.
- `templates/`: Bob-native mirrors of participant Markdown templates.
- `schemas/`: Bob-native mirrors of review JSON schemas.
- `scripts/`: Bob-native mirrors of helper scripts.
- `workflows/`: passive reference files Bob can use as context when a user asks it to follow a workflow. These are not slash commands.
- `rules-*`: Bob mode-specific guidance.
