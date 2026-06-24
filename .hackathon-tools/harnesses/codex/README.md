# Codex Adapter

Use this adapter when a team wants Codex to understand and run the hackathon tools from project-local instructions.

## Install

If the project has no root `AGENTS.md`, copy:

```text
harnesses/codex/AGENTS.md
```

to:

```text
AGENTS.md
```

If the project already has `AGENTS.md`, preserve the existing project guidance and add the hackathon section from this adapter.

Do not require a global Codex skill install. The canonical hackathon instructions live inside `.hackathon-tools/` and can be read directly.

If `.gitignore` exists, ask for approval to add `.hackathon/` and `.hackathon-tools/` if either entry is missing. If setup creates a Codex-specific hidden folder only for hackathon tooling, ask approval to add that folder too. Do not create `.gitignore` solely for adapter setup.

## Invocation

Ask Codex to run one of:

```text
Run setup-hackathon using .hackathon-tools/.
Run run-readiness-review using .hackathon-tools/.
Run prepare-hackathon-submission using .hackathon-tools/.
```

Codex should read the matching `.hackathon-tools/skills/<workflow>/SKILL.md` and `.hackathon-tools/review-commands/<workflow>.md` files before acting.
