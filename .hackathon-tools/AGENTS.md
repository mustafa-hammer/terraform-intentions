# RTS AI Hackathon Tooling Guidance

This folder contains project-local participant workflows for the RTS AI Hackathon.

Use these files only when the user explicitly asks for one of the hackathon participant workflows or asks for help preparing hackathon review context.

## Folder Assumption

In a team project, this folder is expected to live at:

```text
.hackathon-tools/
```

If this folder is named `hackathon-tools/` because it is being viewed as the source repo, treat paths below as relative to this folder.

## Harness Setup

Use the most specific adapter available for the active harness:

- Bob: `.hackathon-tools/harnesses/bob/` for discovery, with native files in `.hackathon-tools/.bob/`
- GitHub Copilot: `.hackathon-tools/harnesses/github-copilot/`
- Claude Code: `.hackathon-tools/harnesses/claude-code/`
- Codex: `.hackathon-tools/harnesses/codex/`

If no adapter exists, use the generic workflow instructions in this file.

For every harness, preserve existing project guidance. Merge hackathon guidance into existing files instead of overwriting them.

If `.gitignore` exists during harness setup, ask the operator for approval to add `.hackathon/` and `.hackathon-tools/` when either entry is missing. If this setup creates a harness-specific hidden folder only for hackathon tooling, such as `.bob/`, `.claude/`, or another harness adapter folder, ask approval to add that folder too. Default recommendation is yes. Do not add an existing project-owned harness folder to `.gitignore` unless the operator confirms it is only for hackathon tooling. Do not create `.gitignore` solely for harness setup; if no `.gitignore` exists, `/setup-hackathon` will ask again when it creates hackathon context.

## Bob Harness Setup

When running in Bob, set up project slash commands in the team project root:

1. Confirm this tools pack exists at `.hackathon-tools/`.
2. Read `.hackathon-tools/harnesses/bob/README.md` if present. It is a discovery pointer to the native Bob files under `.hackathon-tools/.bob/`.
3. Confirm `.hackathon-tools/.bob/` exists. If it is missing, explain that the tools copy likely skipped hidden folders, ask the operator for the original `hackathon-tools` source path, and recopy the whole folder including hidden entries.
4. Create `.bob/` in the project root if missing.
5. Idempotently copy these hackathon-managed directories from `.hackathon-tools/.bob/` into root `.bob/`:
   - `commands/`
   - `agents/`
   - `context/`
   - `prompts/`
   - `templates/`
   - `schemas/`
   - `scripts/`
   - `workflows/`
   - `rules-ask/`
   - `rules-plan/`
   - `rules-code/`
   - `rules-advanced/`
6. On repeat setup, refresh those hackathon-managed `.bob/` directories from `.hackathon-tools/.bob/` instead of appending duplicate files or creating nested directories.
7. Do not require Python, npm, or another runtime just to install the Bob project files. Use normal file operations available to the harness.
8. Preserve existing project guidance such as root `AGENTS.md`; merge hackathon guidance into it rather than overwriting it.
9. Apply the shared `.gitignore` approval rule above.
10. Tell the user that Bob should now expose:
   - `/setup-hackathon`
   - `/run-readiness-review`
   - `/prepare-hackathon-submission`
   - `readiness-coach` agent behavior for direct invocation
11. Create or update `.hackathon/hackathon-tooling-guide.md` using `templates/hackathon/hackathon-tooling-guide.md`.
12. In that guide, explain what Bob will load or expose automatically and what the team should run manually.

Do not leave the only copy of the commands or agents under `.hackathon-tools/.bob/`; Bob expects active project slash commands under the project root `.bob/commands/` and active project agent definitions under `.bob/agents/`.

Bob workflows under `.bob/workflows/` are passive reference/context files. They are not slash commands and should not be described as directly invokable.

## GitHub Copilot Harness Setup

When running with GitHub Copilot:

1. Use only `.github/copilot-instructions.md` for Copilot-specific setup.
2. If project-root `.github/copilot-instructions.md` exists, preserve it and merge in the hackathon section from `.hackathon-tools/harnesses/github-copilot/.github/copilot-instructions.md`.
3. If it does not exist, create it from `.hackathon-tools/harnesses/github-copilot/.github/copilot-instructions.md`.
4. Do not create other Copilot-specific prompt files for this tooling.
5. Apply the shared `.gitignore` approval rule above.
6. Explain in `.hackathon/hackathon-tooling-guide.md` that Copilot loads the instruction file automatically, but teams manually ask Copilot to run `setup-hackathon`, `run-readiness-review`, and `prepare-hackathon-submission`.

## Claude Code Harness Setup

When running with Claude Code:

1. Copy or refresh `.hackathon-tools/harnesses/claude-code/.claude/commands/` into root `.claude/commands/`.
2. Preserve existing `CLAUDE.md`; merge in the hackathon section from `.hackathon-tools/harnesses/claude-code/CLAUDE.md` if useful.
3. Apply the shared `.gitignore` approval rule above.
4. Explain in `.hackathon/hackathon-tooling-guide.md` whether project slash commands are available. If not, tell the team to manually ask Claude Code to read `.hackathon-tools/AGENTS.md` and run the workflow by name.

## Codex Harness Setup

When running with Codex:

1. Preserve existing root `AGENTS.md`; merge in the hackathon section from `.hackathon-tools/harnesses/codex/AGENTS.md`.
2. If no root `AGENTS.md` exists, create it from `.hackathon-tools/harnesses/codex/AGENTS.md`.
3. Do not require a global Codex skill install.
4. Apply the shared `.gitignore` approval rule above.
5. Explain in `.hackathon/hackathon-tooling-guide.md` that Codex uses `AGENTS.md` as project guidance and teams manually ask Codex to run each workflow using `.hackathon-tools/`.

## Harness Tooling Guide

Whenever setting up the hackathon tools in a team project, create or update:

```text
.hackathon/hackathon-tooling-guide.md
```

Use `templates/hackathon/hackathon-tooling-guide.md` as the base.

The guide must be short and harness-specific. It should explain:

- what the harness will load, expose, or invoke automatically,
- which tools the team must run manually,
- when to run each manual tool,
- how to invoke each manual tool in the active harness,
- what each tool produces,
- what not to expect from participant tooling.

For Bob:

- automatic/project setup can expose slash commands from `.bob/commands/`,
- automatic/project setup can expose agent personas from `.bob/agents/`,
- optional Bob support may come from `.bob/context/`, `.bob/prompts/`, `.bob/workflows/`, `.bob/templates/`, `.bob/schemas/`, `.bob/scripts/`, and `.bob/rules-*`,
- `.bob/workflows/` files are reference/context files, not slash commands,
- teams still manually choose when to run `/setup-hackathon`, `/run-readiness-review`, and `/prepare-hackathon-submission`.

For other harnesses:

- explain that the workflows may need prompt-based manual invocation,
- point to the canonical `.hackathon-tools/skills/` and `.hackathon-tools/review-commands/` files.

Do not include organizer-only workflows, scores, rankings, awards, or cross-team comparison language.

### `setup-hackathon`

When the user asks for `setup-hackathon`:

1. Read `skills/setup-hackathon/SKILL.md`.
2. Follow `review-commands/setup-hackathon.md`.
3. Use `templates/hackathon/epic.md`.
4. For RTS epics, use source files under `epics/rts/`.
5. For EnterpriseOS epics, use source files under `epics/enterpriseos/`.
6. Create or update `.hackathon/epic.md` in the team project.
7. Create `.hackathon/private/scratch.md` if missing.
8. Ask before adding `.hackathon/` to `.gitignore`; default yes. If `.hackathon-tools/` exists in the project, add `.hackathon-tools/` at the same time unless it is already present.
9. Create or update `.hackathon/hackathon-tooling-guide.md` if missing or stale.
10. Keep the workflow idempotent.

### `run-readiness-review`

When the user asks for `run-readiness-review`:

1. Read `skills/run-readiness-review/SKILL.md`.
2. Follow `review-commands/run-readiness-review.md`.
3. Act as the Bob agent defined in `.bob/agents/readiness-coach.md` if it is installed.
4. Use `review-agents/readiness-coach.md` as the canonical detailed review contract.
5. Read `.hackathon/epic.md`.
6. Inspect visible repo files and artifacts.
7. Write or replace `.hackathon/readiness-review.md`.

Do not produce a score, ranking, award, or cross-team comparison.

### `prepare-hackathon-submission`

When the user asks for `prepare-hackathon-submission`:

1. Read `skills/prepare-hackathon-submission/SKILL.md`.
2. Follow `review-commands/prepare-hackathon-submission.md`.
3. Use `templates/hackathon/team-profile.md`.
4. Use `templates/hackathon/learning-notes.md`.
5. Generate `.hackathon/evidence-manifest.json`.
6. Generate `.hackathon/repo-summary.json` and `.hackathon/changed-files.txt`.
7. Validate generated JSON when possible with `scripts/validate-review-json.py`.
8. Export the bundle to `~/dev/hackathon-submissions/team-slug__epic-slug/`.

Do not include `.hackathon/private/` in exported bundles.

## Boundaries

This pack is participant-facing only.

Do not run, simulate, or invent organizer-only workflows from this folder:

- `run-submission-review`
- `run-hackathon-chronicle`
- organizer scoring
- organizer-only awards
- cross-team comparisons

## Language Rules

Use review, readiness, completeness, evidence, and learning language.

Avoid score, grade, judge, ranking, leaderboard, winner, loser, or award language in participant-facing outputs.

## Safety Rules

- Use fake data.
- Do not expose customer data.
- Do not expose secrets.
- When the setup workflow updates `.gitignore`, add `.hackathon/` and also `.hackathon-tools/` if that tooling folder exists in the project.
- Do not ask teams to save or share AI session transcripts.
- Warn if expected artifacts appear to be missing, ignored by Git, or not visible to generated file lists.
- Record verification commands honestly as passed, failed, or not run.
