---
description: Set up or update hackathon epic context for this project.
---

Read `.hackathon-tools/AGENTS.md`, `.hackathon-tools/skills/setup-hackathon/SKILL.md`, and `.hackathon-tools/review-commands/setup-hackathon.md`.

Run the participant-facing `setup-hackathon` workflow for this project. Create or update `.hackathon/epic.md`, `.hackathon/private/scratch.md`, and `.hackathon/hackathon-tooling-guide.md`.

If `.gitignore` exists, add `.hackathon/` and `.hackathon-tools/` only if missing.

Keep the workflow idempotent: show existing values when present, let the operator keep or update them, and avoid duplicate sections.
