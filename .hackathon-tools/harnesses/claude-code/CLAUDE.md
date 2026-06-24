# RTS AI Hackathon Participant Tooling

This project may include hackathon tools at `.hackathon-tools/`.

Participant-facing workflows:

- `/setup-hackathon`
- `/run-readiness-review`
- `/prepare-hackathon-submission`

When asked to run one of these workflows, read `.hackathon-tools/AGENTS.md`, then read the matching skill and review-command files under `.hackathon-tools/`.

If `.gitignore` exists during setup, ask before adding `.hackathon/` and `.hackathon-tools/`. If `.claude/` was created only for hackathon tooling, ask before adding `.claude/` too. Do not add an existing project-owned `.claude/` folder unless the operator confirms it is only for hackathon tooling. Do not create `.gitignore` solely for hackathon tooling setup.

Do not run organizer-only review, scoring, award, ranking, or cross-team comparison workflows.

Use review, readiness, completeness, evidence, and learning language. Use fake data. Do not expose customer data or secrets. Do not ask teams to save or share AI session transcripts.
