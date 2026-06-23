# Bob Code Mode Rules For Hackathon Tools

Use Code mode for focused implementation inside the team project.

- Read `.hackathon/epic.md` before editing.
- Keep changes small and reviewable.
- Use fake data only.
- Do not expose secrets or customer data.
- Prefer creating visible evidence: README notes, examples, generated outputs, tests, smoke commands, or demo scripts.
- After meaningful changes, suggest `/run-readiness-review`.
- When setup updates `.gitignore`, add `.hackathon/` and also `.hackathon-tools/` if that folder exists.

## Testing Requirements

Before committing changes that affect the webhook server or request handling:

1. **Always run unit tests:** `uv run pytest`
2. **Run E2E smoke test:** `bash tests/smoke_test_e2e.sh`
3. **Verify cleanup:** Check no orphaned processes with `lsof -i :8768`

The smoke test ensures the server starts, responds correctly, and cleans up properly. It's not in CI but is critical for server-related changes.
