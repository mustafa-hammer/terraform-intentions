# Claude Code Adapter

Use this adapter when a team wants Claude Code to expose project-local slash commands for the hackathon tools.

## Install

Copy or refresh:

```text
harnesses/claude-code/.claude/commands/
```

into the team project at:

```text
.claude/commands/
```

If the project already has `CLAUDE.md`, preserve it. Add the short hackathon section from `harnesses/claude-code/CLAUDE.md` instead of overwriting existing guidance.

If `.gitignore` exists, ask for approval to add `.hackathon/` and `.hackathon-tools/` if either entry is missing. If this setup created `.claude/` only for hackathon tooling, ask approval to add `.claude/` too. If `.claude/` already existed for the real project, do not add it unless the operator confirms it is only for hackathon tooling. Do not create `.gitignore` solely for adapter setup.

## Invocation

After installation, teams can ask Claude Code to run:

```text
/setup-hackathon
/run-readiness-review
/prepare-hackathon-submission
```

If project-local slash commands are not available in the local Claude Code setup, ask Claude Code to read `.hackathon-tools/AGENTS.md` and run the matching workflow by name.
