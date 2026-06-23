# setup-hackathon

## Purpose

Team-facing command run after a team decides what it will work on. It creates or updates the local `.hackathon/epic.md` file and prepares the team to use Readiness Coach.

## Invocation

```text
setup-hackathon
```

## Idempotency Rules

- If `.hackathon/` is missing, create it.
- If `.hackathon/epic.md` exists, parse current values and show them before prompting.
- Let the operator keep existing values.
- Rewrite `.hackathon/epic.md` deterministically.
- Do not append duplicate sections.
- Preserve fields not owned by this command when possible.
- Ask before modifying `.gitignore`, default yes.
- If modifying `.gitignore`, add `.hackathon/` only if it is not already present.
- At the same step, if `.hackathon-tools/` exists in the project, add `.hackathon-tools/` only if it is not already present.
- Never create transcript folders.

## Owned Files

Creates or updates:

- `.hackathon/epic.md`
- `.hackathon/private/scratch.md` if missing
- `.hackathon/hackathon-tooling-guide.md`
- `.hackathon/review-criteria-concern.md` only when needed

May update:

- `.gitignore`

## Flow

1. Explain that `.hackathon/` is local working context and should be gitignored. If `.hackathon-tools/` exists in the project, explain that it is also local hackathon tooling and should normally be gitignored after setup.
2. Ask whether the team is using:
   - RTS epic
   - EnterpriseOS epic
   - Custom epic
3. If official epic:
   - List available epic files from `rts-epics/*.md` or `enterpriseos-epics/*.md`.
   - Let operator select one.
   - Normalize source into `.hackathon/epic.md`.
   - Rename source `Review Checklist` to `Review Checklist`.
   - Prompt for `Team Interpretation`.
4. If custom epic:
   - Interview for required epic fields.
   - Collect detailed free-form story descriptions.
   - Map each story into required structured fields.
   - Recommend stretch goals.
   - Generate Review Checklist.
5. Ask whether the generated Review Checklist seems misaligned or unfair.
6. If yes, create or update `review-criteria-concern.md`.
7. Confirm `.hackathon/epic.md` was written and suggest running Readiness Coach.
8. Create or update `.hackathon/hackathon-tooling-guide.md` with a short harness-specific guide:
   - what the harness loads or exposes automatically,
   - what the team must run manually,
   - when to run each tool,
   - how to invoke each tool,
   - what each tool produces.

## Custom Epic Required Fields

- Epic ID and title.
- Epic source: `Custom`.
- Source file or URL, if any.
- Product focus / work area.
- Objective.
- Why It Matters.
- Primary Output.
- Expected PR Shape.
- Definition Of Done.
- Stories.
- Stretch Goals.
- Review Checklist.
- Team Interpretation.

## Expected PR Shape Prompt

Use this exact explanation:

> Describe the kinds of files or evidence reviewers should expect in your final submission. Mention prompts, code, tests, README/demo notes, examples, screenshots, notebooks, generated outputs, or config changes as relevant. This is not a commitment to exact filenames, but it should give reviewers a concrete expectation.

Show examples:

```markdown
Add prompt pack files, fake but realistic Terraform plan snippets, review check cases, a README, and a short demo script or notebook that runs the pack against at least three examples.
```

```markdown
Add Tauri keyring wiring, Go `SecretStore` interface and OS keyring implementation, provider and connector migration code, Secrets UI, one-time config migration, redaction/audit tests, and documentation for local setup and verification.
```

```markdown
Add discovery prompt/workflow, sample interviews, generated briefs, checks, and README.
```

## Story Mapping

Ask for a detailed story description first. Then recommend:

- Story title.
- Difficulty.
- Suggested owner.
- First useful step.
- Building with AI.
- Output.

Allowed `Difficulty` values:

- `Beginner`
- `Beginner to Intermediate`
- `Intermediate`
- `Advanced`

Allowed `Suggested owner` values:

- `New AI user`
- `Comfortable with AI tools`
- `AI Builder Lead`
- `Flex teammate`

Reject enum values outside the lists.

## Review Checklist Control

The team should not normally edit the Review Checklist directly. If the team disagrees with the generated criteria, write the concern to `.hackathon/review-criteria-concern.md`.

Use this file shape:

```markdown
# Review Criteria Concern

## Concern

## Suggested Adjustment

## Organizer Resolution

Pending.
```

## Success Criteria

- `.hackathon/epic.md` exists and follows `templates/hackathon/epic.md`.
- `.hackathon/private/scratch.md` exists.
- `.hackathon/hackathon-tooling-guide.md` exists and explains automatic versus manual tooling for the active harness.
- `.gitignore` includes `.hackathon/` if the operator approved.
- `.gitignore` includes `.hackathon-tools/` if the operator approved and `.hackathon-tools/` exists.
- No transcript folder is created.
