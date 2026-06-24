# Bob Adapter

Use this adapter when the active harness is IBM Bob.

Bob's native project files are intentionally stored at:

```text
.hackathon-tools/.bob/
```

Do not look for a second copy under `harnesses/bob/`. This folder exists only as a discovery pointer so Bob can find the Bob-specific setup path when scanning `harnesses/`.

If `.hackathon-tools/.bob/` is missing, the tools package was probably copied without hidden folders. Ask the operator for the original `hackathon-tools` source path and recopy the whole folder including hidden entries before continuing.

## Install

From the team project root, create or refresh root `.bob/` from `.hackathon-tools/.bob/`.

Copy these hackathon-managed directories:

```text
.hackathon-tools/.bob/commands/      -> .bob/commands/
.hackathon-tools/.bob/agents/        -> .bob/agents/
.hackathon-tools/.bob/context/       -> .bob/context/
.hackathon-tools/.bob/prompts/       -> .bob/prompts/
.hackathon-tools/.bob/templates/     -> .bob/templates/
.hackathon-tools/.bob/schemas/       -> .bob/schemas/
.hackathon-tools/.bob/scripts/       -> .bob/scripts/
.hackathon-tools/.bob/workflows/     -> .bob/workflows/
.hackathon-tools/.bob/rules-ask/     -> .bob/rules-ask/
.hackathon-tools/.bob/rules-plan/    -> .bob/rules-plan/
.hackathon-tools/.bob/rules-code/    -> .bob/rules-code/
.hackathon-tools/.bob/rules-advanced/ -> .bob/rules-advanced/
```

Keep setup idempotent. On repeat setup, refresh the same hackathon-managed directories instead of appending duplicate files or creating nested copies.

Do not require Python, npm, or another runtime just to install these files.

If `.gitignore` exists in the project root, ask the operator for approval to add these entries if they are missing:

```gitignore
.hackathon/
.hackathon-tools/
```

If this setup created `.bob/` only for hackathon tooling, ask approval to add `.bob/` too. If `.bob/` already existed for the real project, do not add it to `.gitignore` unless the operator confirms it is only for hackathon tooling.

The default recommendation is yes. Do not create `.gitignore` solely for Bob harness setup; if no `.gitignore` exists, tell the operator `/setup-hackathon` will ask again when it creates hackathon context.

## Invocation

After installation, Bob should expose:

```text
/setup-hackathon
/run-readiness-review
/prepare-hackathon-submission
```

Bob should also be able to use the `readiness-coach` agent directly.

## Workflow Note

Files under `.bob/workflows/` are passive reference/context files. They are not slash commands.
