### 238: Deployed Sandboxes & Long-Running Agents (V2.0)

**Product Focus:** EnterpriseOS

**Objective:** V2.0 promises "deployed sandboxes and long running agents." Today sandboxes are local-only (OpenShell on the user's host) and agents are tied to a session. This epic lifts sandboxes onto deployed infrastructure (Nomad / Docker) and introduces a worker model for long-running agents.

**Why it matters for EnterpriseOS users:** EnterpriseOS users need agents that can keep working after an interactive session ends, but they also need lifecycle controls, state recovery, and clear ownership of remote execution. Deployed sandboxes and long-running workers turn EnterpriseOS from a desktop-only demo into a credible operating surface for durable agent work.

**Primary Output:** Promotes EnterpriseOS from "tools the user pokes at" to "agents that work for you." Critical for the "agentic workloads" positioning.

**Expected PR Shape:** Add a deployed sandbox adapter, worker runtime, lifecycle API/UI, persistence and reconciliation code, Destination Decider remote routing updates, tests for restart and lifecycle behavior, and demo notes showing a remote sandbox plus a background agent surviving a restart.

**Definition of Done:**

- A deployed-sandbox backend launches sandboxes as Nomad jobs (or Docker containers as fallback)
- Long-running agents can run as background workers independent of an interactive session
- Agent lifecycle (start / pause / stop / restart) is exposed via API + UI
- Deployed sandbox state survives a server restart (reattach on boot)
- The existing Destination Decider can route to the new `remote` destination

**Stories:**

1. **#234: Sandbox deploy adapter — Nomad job spec**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Compare the current local sandbox interface with the minimum Nomad allocation details needed to return the same handle shape.
   - Building with AI: Ask AI to draft the Nomad job template and failure-mode checklist, then validate the output against the existing sandbox interface.
   - Output: Nomad-backed sandbox adapter, Docker fallback path, job template, and routing tests.

2. **#235: Long-running agent worker process**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Trace the interactive agent loop and mark which dependencies assume an attached SSE consumer.
   - Building with AI: Use AI to design a restart-safe worker lifecycle and then turn the lifecycle into tests for resume, heartbeat, and event replay.
   - Output: Background worker runtime, persisted worker state, heartbeat updates, and replayable events.

3. **#236: Agent lifecycle API + UI (start / pause / stop / restart)**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Define the allowed state transitions and which transitions should emit audit events before wiring UI buttons.
   - Building with AI: Ask AI to generate a transition table and API examples, then use that table to check backend and UI behavior.
   - Output: Lifecycle endpoints, Fleet page controls, persisted state transitions, and audit events.

4. **#237: Persistence and reconnect for deployed sandboxes**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write the reconciliation cases for live, dead, unknown, and manually reattached sandboxes.
   - Building with AI: Use AI to draft reconciliation pseudocode and a restart test plan, then implement the smallest path that proves reattach works.
   - Output: Startup reconciliation, periodic reattach loop, manual reattach action, and restart test evidence.

**Stretch Goals:**

- Add resource-limit presets for small, medium, and large remote sandboxes.
- Add a worker-drain mode for planned server maintenance.
- Add a visual timeline that shows worker events before and after a reconnect.
- Add a Nomad allocation detail link from the Fleet page when Nomad is configured.

**Review Checklist:**

- Does the remote sandbox adapter preserve the same caller contract as the local sandbox?
- Can long-running agents continue or resume without an attached browser session?
- Are lifecycle actions persisted, audited, and reflected accurately in the UI?
- Does restart reconciliation handle live and dead deployed sandboxes without double-running work?
- Is there evidence of a demo or test that covers remote routing and restart behavior?
