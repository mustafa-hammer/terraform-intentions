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
   - Description: Implement a deploy adapter that launches a sandbox as a Nomad job, exposing the same `Exec` interface as the local sandbox.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Compare the current local sandbox interface with the minimum Nomad allocation details needed to return the same handle shape.
   - Building with AI: Ask AI to draft the Nomad job template and failure-mode checklist, then validate the output against the existing sandbox interface.
   - Output: Nomad-backed sandbox adapter, Docker fallback path, job template, and routing tests.
   - Acceptance Criteria:
     - `internal/sandbox/nomad.go` implements the existing sandbox interface
     - Renders a job spec parameterised by sandbox_id, image, env, resource limits
     - Submits via `nomad job run`; tracks allocation ID
     - Health check before returning the sandbox handle
     - Falls back to Docker driver if Nomad is unavailable
     - Destination Decider can route to `remote` and produce this sandbox

2. **#235: Long-running agent worker process**
   - Description: Introduce a worker model that lets an agent run in the background independent of an interactive session.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Trace the interactive agent loop and mark which dependencies assume an attached SSE consumer.
   - Building with AI: Use AI to design a restart-safe worker lifecycle and then turn the lifecycle into tests for resume, heartbeat, and event replay.
   - Output: Background worker runtime, persisted worker state, heartbeat updates, and replayable events.
   - Acceptance Criteria:
     - `internal/agent/worker.go` runs the agent loop without an attached SSE consumer
     - Worker emits events into the streaming engine for later replay
     - Restart-safe: in-flight workers resume after a server restart
     - Worker writes Trajectory + Decision records like interactive runs
     - Heartbeat field on the worker row so UI can detect stalls
     - Configurable per-tenant concurrency cap

3. **#236: Agent lifecycle API + UI (start / pause / stop / restart)**
   - Description: Expose agent lifecycle controls (start, pause, stop, restart) via API and surface them in the Fleet page.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Define the allowed state transitions and which transitions should emit audit events before wiring UI buttons.
   - Building with AI: Ask AI to generate a transition table and API examples, then use that table to check backend and UI behavior.
   - Output: Lifecycle endpoints, Fleet page controls, persisted state transitions, and audit events.
   - Acceptance Criteria:
     - `POST /api/v1/agents/:id/start|pause|stop|restart`
     - Fleet card shows current state + lifecycle action buttons
     - State transitions are persisted and emit audit events
     - Pause is graceful: completes current step then stops
     - Stop with grace period before kill
     - Status badge colour reflects state

4. **#237: Persistence and reconnect for deployed sandboxes**
   - Description: Deployed sandboxes survive a server restart. On boot, the server reattaches to existing Nomad allocations and reconciles their state.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write the reconciliation cases for live, dead, unknown, and manually reattached sandboxes.
   - Building with AI: Use AI to draft reconciliation pseudocode and a restart test plan, then implement the smallest path that proves reattach works.
   - Output: Startup reconciliation, periodic reattach loop, manual reattach action, and restart test evidence.
   - Acceptance Criteria:
     - On startup, reconcile against `nomad job status` for `enterpriseos-sandbox-*` jobs
     - Live sandboxes are reattached; dead ones are removed from the local registry
     - Background reconciliation loop runs every N seconds
     - Reattach emits an audit event with disposition
     - Manual "Reattach" action on the Fleet page for stuck cases
     - Test: kill server while sandbox is running; confirm reattach on boot

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
