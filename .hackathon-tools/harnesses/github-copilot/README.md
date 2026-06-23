# GitHub Copilot Adapter

Use this adapter when a team wants GitHub Copilot to understand the hackathon tools.

## Install

Copy or merge:

```text
harnesses/github-copilot/.github/copilot-instructions.md
```

into the team project at:

```text
.github/copilot-instructions.md
```

If the project already has `.github/copilot-instructions.md`, preserve the existing project guidance and add a short hackathon section from this adapter.

Do not add other Copilot-specific prompt files. For this hackathon tooling, rely only on `.github/copilot-instructions.md`.

If `.gitignore` exists, ask for approval to add `.hackathon/` and `.hackathon-tools/` if either entry is missing. If setup creates a Copilot-specific hidden folder only for hackathon tooling, ask approval to add that folder too. Do not create `.gitignore` solely for adapter setup.

## Invocation

Copilot should use these instructions as project context. Teams can ask for the three workflows manually:

```text
Run setup-hackathon using the project-local .hackathon-tools folder.
```

```text
Run run-readiness-review using the project-local .hackathon-tools folder.
```

```text
Run prepare-hackathon-submission using the project-local .hackathon-tools folder.
```
