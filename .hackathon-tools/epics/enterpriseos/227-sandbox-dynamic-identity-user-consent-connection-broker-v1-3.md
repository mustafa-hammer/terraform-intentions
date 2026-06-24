### 227: Sandbox — Dynamic Identity, User Consent, Connection Broker (V1.3)

**Product Focus:** EnterpriseOS

**Objective:** The V1.3 release promises an enterprise local sandbox with **dynamic identity, user consent, connections+identity, logs, and a Destination Decider stub**. The Destination Decider stub and OpenShell sandbox runtime have just landed (`internal/deployment/decider.go`, `internal/sandbox/`). This epic completes V1.3 by adding per-task identity minting, an explicit user consent prompt, a connection broker, sandbox-scoped logs surfaced in the UI, and a policy-aware Decider v2.

**Why it matters for EnterpriseOS users:** EnterpriseOS users need to trust that agent work runs with explicit consent, scoped identity, brokered access, and reviewable evidence. This epic makes sandbox execution understandable and governable instead of asking users to accept a black-box agent runtime.

**Primary Output:** Completes V1.3 — the first version of EnterpriseOS a security-minded enterprise can stand behind. Concrete proof that "agents in sandboxes with brokered identity" is real, not slideware.

**Expected PR Shape:** Add sandbox identity and broker implementation changes, consent UI/API changes, log filtering updates, Destination Decider v2 behavior, cleanup/revocation tests, and a README or demo notes showing a launch, approval, brokered connection, logs, and cleanup.

**Definition of Done:**

- Each sandbox launch mints a short-lived identity scoped to that task
- A user-consent prompt is required before any sandbox launch (with remember-this-action option)
- The sandbox cannot reach external services directly; it requests connections through the broker and the user approves them
- Logs emitted by the sandbox are tagged with sandbox_id and visible on the Logs page filtered by sandbox
- The Destination Decider evaluates policy (current stub is local-only) and explains its decision in the Trajectory record
- Identity is revoked + sandbox cleaned up at session end

**Stories:**

1. **#221: Dynamic identity minting per sandbox launch**
   - Description: Each sandbox launch mints a short-lived identity (token + scoped permissions) bound to that specific task. The identity is injected into the sandbox env, never exposed on the host.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Trace the current sandbox launch path and write down the exact point where a scoped identity can be minted and injected.
   - Building with AI: Use AI to compare identity envelope designs, then ask it to generate test cases for TTL, scope, audit, and revocation behavior.
   - Output: Identity minting implementation, scoped env injection, audit events, and unit tests.
   - Acceptance Criteria:
     - `internal/sandbox/` mints a per-launch identity via `identity.Mint(ctx, scope)`
     - Identity has a TTL no longer than the sandbox session
     - Identity carries scope: tenant_id, user_id, skill_id, allowed_connections
     - Token injected into sandbox via env var; never appears on the command line
     - Identity revoked when the sandbox exits or is killed
     - Each mint emits an audit event

2. **#222: User consent prompt before sandbox launch**
   - Description: Before any sandbox launches, the UI shows a user consent prompt with the action summary, requested connections, and identity scope. The user must explicitly approve.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Draft the consent payload contract between the backend and UI before changing the modal.
   - Building with AI: Ask AI to critique the consent screen for missing security context and ambiguous user choices.
   - Output: Consent API contract, modal implementation, backend enforcement, and audit record.
   - Acceptance Criteria:
     - Consent modal displayed before sandbox launch
     - Shows: skill name, action summary, requested connections, identity scope, est. duration
     - Approve / Deny buttons; Deny aborts cleanly with no side effects
     - "Remember for this session" option (scoped to skill_id)
     - Consent decision recorded in audit log with decision_id
     - Backend rejects sandbox launch if no consent token is present

3. **#223: Connection broker — sandbox requests, user approves**
   - Description: Sandboxes cannot reach external services directly; they request connections through a broker, and the user approves (or has pre-approved) each connection.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Define the broker request/decision/handle lifecycle and where secrets must never cross a boundary.
   - Building with AI: Use AI to threat-model the broker flow and turn the useful risks into tests or validation checks.
   - Output: Broker API, approval path, brokered handles, policy hooks, and redaction tests.
   - Acceptance Criteria:
     - `internal/sandbox/broker.go` exposes `RequestConnection(ctx, sandbox_id, target)` to the sandbox
     - Connection requests appear in the UI for approval if not pre-approved
     - Approved connections return a brokered handle; the sandbox never sees real credentials
     - Per-tenant pre-approval policy (e.g. "auto-approve corporate GitHub")
     - Denied requests get a clean error returned to the sandbox
     - Each broker interaction logged with sandbox_id, target, decision

4. **#224: Sandbox-scoped logs on the Logs page**
   - Description: Sandboxes emit structured logs tagged with sandbox_id, and the Logs page can filter to a single sandbox or session.
   - Difficulty: Beginner to Intermediate
   - Suggested owner: New AI user
   - First useful step: Find the existing operations log shape and add the minimum sandbox/session fields needed for filtering.
   - Building with AI: Ask AI to generate example log events and UI empty states, then verify they match existing naming and styling conventions.
   - Output: Structured sandbox log events, Logs page filter, session timeline toggle, and sample events.
   - Acceptance Criteria:
     - Sandbox writes structured JSON logs (event, ts, sandbox_id, session_id, severity, message)
     - Logs ingested into the existing operations log store
     - Logs page gets a `sandbox_id` filter and a "View as session timeline" toggle
     - Severity colour coding consistent with existing Logs page
     - Empty state shown when a sandbox has no logs yet

5. **#225: Destination Decider v2 — policy-aware decisions**
   - Description: Promote the current Destination Decider stub from "local-only" into a policy-aware decision engine that considers user preference, action sensitivity, tenant policy, and sandbox availability.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Enumerate the decision inputs and expected branch outcomes before modifying the Decider interface.
   - Building with AI: Ask AI to generate a decision table, then convert the table into tests for each policy branch.
   - Output: Policy-aware Decider implementation, structured reasons, Trajectory integration, and branch tests.
   - Acceptance Criteria:
     - `Decide(ctx, action, prefs) (Decision, error)` consumes action metadata + tenant policy + sandbox availability
     - Decision branches: `direct`, `local`, `remote` with a structured `Reason`
     - Tenant policy can force a destination (e.g. "always sandbox") regardless of user preference
     - Decision included in the Trajectory record for the run
     - Unit tests cover each policy branch
     - No breaking change to existing decider callers

6. **#226: Sandbox identity revocation and cleanup**
   - Description: When a sandbox session ends — gracefully, by timeout, or by abort — its identity is revoked and resources are cleaned up.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Map every sandbox termination path and identify which cleanup actions must run in each path.
   - Building with AI: Use AI to draft a cleanup matrix, then ask it to look for orphan and double-revocation edge cases.
   - Output: Cleanup lifecycle implementation, timeout/orphan sweep behavior, and audit tests.
   - Acceptance Criteria:
     - Sandbox manager calls `identity.Revoke(token)` on session end
     - Brokered connections for that sandbox are torn down
     - OpenShell sandbox is destroyed (`openshell sandbox delete`) when no longer referenced
     - Timeout policy: configurable max session age (default 1h)
     - Clean-up emits an audit event with disposition: `completed`, `timeout`, `aborted`
     - Orphan cleanup job sweeps stale sandboxes on server start

**Stretch Goals:**

- Add a demo policy that shows the same action routed differently based on tenant rules.
- Add a consent history view that lets a user inspect prior sandbox approvals and denials.
- Add broker metrics for approval latency, denied requests, and connection usage by sandbox.
- Add a security review note explaining which values can appear in logs and which must never appear.

**Review Checklist:**

- Does every sandbox launch require explicit consent or a valid remembered consent token?
- Are identities short-lived, scoped, injected only through environment, and revoked on every termination path?
- Are external connections brokered without exposing real credentials to the sandbox?
- Are Decider reasons visible in the Trajectory record and specific enough for a user to understand?
- Is there evidence of tests or demo output for approval, denial, logging, and cleanup paths?
