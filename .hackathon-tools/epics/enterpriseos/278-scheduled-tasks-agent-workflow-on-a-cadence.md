### 278: Scheduled Tasks (Agent × Workflow on a Cadence)

**Product Focus:** EnterpriseOS

**Objective:** The Tasks page in the web UI is currently mocked. This epic turns it into the real surface for **scheduled tasks**: a user picks an Agent and a Workflow, sets a cadence (cron / interval / one-time), captures a pre-authorized consent envelope for unattended runs, and the scheduler fires the binding on schedule. Every scheduled execution flows through the existing agent loop, Trust Ladder resolution, Destination Decider, and Trajectory recording — same as an interactive run.

Behind the scenes a scheduled task resolves to an existing **Agent×Workflow×Environment binding**, so all the policy controls already in place (rung resolution, no-fly zones, action-score thresholds) apply unchanged. If a binding doesn't exist for the picked pair, the creation flow prompts the user to create one first.

**Why it matters for EnterpriseOS users:** EnterpriseOS users need agents that can perform recurring work without someone keeping a browser session open. Scheduled tasks make unattended agent work explicit, reviewable, consent-bound, and restart-safe, which is the difference between a demo interaction and a useful operating workflow.

**Primary Output:** Closes the loop on "agents that work for you." Interactive demos show what an agent *can* do; scheduled tasks show what it *does on its own*, every morning at 8am, while the user is at lunch. Pairs cleanly with V2.0 long-running agents (#238) and V2.1 observability (#243).

**Expected PR Shape:** Add schedule data model and CRUD API, scheduler worker, cadence picker, create/edit wizard, live Tasks page wiring, run history/lifecycle actions, consent envelope reuse, restart/misfire tests, and demo notes showing a schedule firing through the normal agent loop.

**Definition of Done:**

- A user can create a scheduled task by picking an installed agent, a workflow, and a cadence
- Cadence options: cron expression, interval (every N minutes/hours/days), one-time at a specific datetime, and friendly presets (hourly, daily, weekly)
- A pre-authorized consent envelope is captured at creation; unattended runs use it instead of an interactive consent prompt (#222)
- Scheduled task references the binding for the picked (agent, workflow) pair; missing binding triggers the create-binding flow
- A background scheduler worker fires due tasks; each firing produces a normal agent run with a `trigger=schedule` tag
- The existing Tasks page is wired to live data — schedule list, next run, last run, status, lifecycle actions
- Per-schedule run history view links to each run's trajectory
- Run-now, pause/resume, delete actions are available with audit events on each
- Scheduler is restart-safe — schedules persist; missed runs after downtime follow a configurable misfire policy

**Related:**
Builds on Bindings (#220 group policy, existing Agent×Workflow×Environment scaffold), #227 (consent envelope), #238 (long-running agents). Uses #243 observability for run telemetry.

**Stories:**

1. **#272: Schedule data model + CRUD API**
   - Description: Define the `Schedule` entity, storage, and CRUD API. A schedule is the durable record of "run this binding on this cadence."
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Define the schedule schema and validation errors before adding endpoints.
   - Building with AI: Ask AI to generate schedule examples for cron, interval, and one-time cadences, then use them as API validation fixtures.
   - Output: Schedule model, migration, CRUD endpoints, binding validation, and tenant-scoped tests.
   - Acceptance Criteria:
     - Schema: `id`, `tenant_id`, `owner_user_id`, `agent_id`, `workflow_id`, `binding_id` (resolved at create), `cadence` (typed: cron | interval | one_time), `cadence_value` (e.g. `"0 8 * * *"` or `"PT15M"` or ISO datetime), `timezone`, `enabled`, `consent_envelope_id`, `misfire_policy` (`fire_once_on_recovery` | `skip` | `fire_all`), `next_run_at`, `last_run_at`, `last_run_status`, `created_at`
     - Migration checked in under `internal/db/migrations/`
     - CRUD endpoints: `GET /api/v1/schedules`, `GET /api/v1/schedules/:id`, `POST`, `PATCH`, `DELETE`
     - On create, server validates cadence syntax + timezone + binding existence; returns structured errors per field
     - If no binding exists for (agent, workflow) in the tenant, POST returns 409 with a `missing_binding` code and the suggested binding payload
     - Tenant-scoped via the existing auth middleware
     - Unit tests cover validation, missing-binding case, and round-trip

2. **#273: Scheduler runtime worker (due-detection, trigger, misfire policy)**
   - Description: Background scheduler worker that detects due schedules, fires them through the existing agent loop, and applies the misfire policy if the process was down.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Write the due-detection and misfire policy table before coding the worker loop.
   - Building with AI: Use AI to generate edge cases for timezones, missed runs, duplicate firing, and active previous runs.
   - Output: Scheduler worker, trigger integration, misfire handling, singleton/concurrency lock, and worker tests.
   - Acceptance Criteria:
     - `internal/scheduler/` package with a ticker that polls due schedules every 10s (configurable)
     - On due, enqueues an agent run with `trigger=schedule`, `schedule_id=...`, attaching the pre-authorized consent envelope
     - Run goes through the normal path: Trust Ladder resolution → Destination Decider → sandbox → Trajectory record
     - `next_run_at` recomputed from cadence + timezone after each fire
     - Misfire policy applied on startup for schedules whose `next_run_at` is in the past:
       - `fire_once_on_recovery` (default) — single catch-up run
       - `skip` — drop missed firings, advance `next_run_at` to the next future slot
       - `fire_all` — fire every missed slot (rate-limited)
     - Singleton lock so multiple enterpriseos instances don't double-fire the same schedule
     - Per-schedule concurrency: a new firing waits if the previous run is still active
     - Audit event per fire (`schedule.fire`) and per skip (`schedule.skip`) with `reason`
     - Tests cover due-detection, misfire branches, and concurrency lock

3. **#274: Cadence picker UI component (cron / interval / one-time + presets)**
   - Description: A reusable cadence picker component. Users hate raw cron — they want presets, a friendly builder, and a preview of the next few firings. Cron stays available for power users.
   - Difficulty: Beginner to Intermediate
   - Suggested owner: New AI user
   - First useful step: Build a static cadence picker mock with presets and a "Next 3 firings" preview before wiring API calls.
   - Building with AI: Ask AI to draft cron validation cases and friendly labels, then verify the output against a cron parser or scheduling helper.
   - Output: Reusable cadence picker component, validation states, timezone support, and example page.
   - Acceptance Criteria:
     - React-style component (or vanilla equivalent matching the existing UI conventions) usable across pages
     - Three modes selectable via tabs: **Presets**, **Interval**, **Cron**
     - Presets: Hourly, Every 6 hours, Daily at HH:MM, Weekly on <day> at HH:MM, Monthly on <date> at HH:MM, One-time at <datetime>
     - Interval mode: number input + unit dropdown (minutes / hours / days)
     - Cron mode: text input + inline validation + tooltip with field meaning
     - Timezone picker (defaults to user's browser timezone)
     - "Next 3 firings" preview underneath, recomputed on every change
     - Emits a structured `{ kind, value, timezone }` object — never raw form state
     - Storybook-style example page included for visual testing

4. **#275: Schedule create/edit wizard (agent → workflow → cadence → consent)**
   - Description: The create/edit wizard captures everything needed to schedule a task: pick an installed agent, pick a workflow it's bound to, choose cadence, and capture the pre-authorized consent envelope for unattended runs.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Define the wizard state machine and how it handles a missing Agent×Workflow binding.
   - Building with AI: Use AI to create a wizard test script for happy path, missing binding, edit, and cancellation with unsaved changes.
   - Output: Create/edit wizard, binding fallback flow, consent capture, save behavior, and UI tests or demo notes.
   - Acceptance Criteria:
     - Modal or slide-over wizard launched from the Tasks page "New scheduled task" CTA
     - Step 1 — Agent: picker shows only installed agents (uses #268 "Installed Agents" data)
     - Step 2 — Workflow: picker filtered to workflows compatible with the chosen agent (looks at existing bindings; offers "create binding" inline if missing)
     - Step 3 — Cadence: embeds the cadence picker from STORY_13_3
     - Step 4 — Consent: shows the requested connections, identity scope, est. resource cost; user clicks "Authorize for all future runs"
     - Consent envelope tied to the schedule id (not the user's session) so it survives logout
     - Edit mode: same wizard pre-filled; changing the agent/workflow pair re-validates the binding
     - Save calls the schedule create/update endpoint and closes the wizard with a success toast
     - Cancel discards changes; confirmation prompt if anything has been edited

5. **#276: Wire scheduled tasks into the existing Tasks page (replace mock)**
   - Description: Replace the mocked Tasks page data with the real schedule list. Each row shows the schedule's identity, next/last run, status, and lifecycle actions; clicking a row opens the run history view (STORY_13_6).
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Remove or isolate the mock data source and render the existing table from `/api/v1/schedules`.
   - Building with AI: Ask AI to generate empty, loading, error, and populated table states, then align styling with the current Tasks page.
   - Output: Live Tasks page, filters, lifecycle action entry points, auto-refresh, and smoke-test evidence.
   - Acceptance Criteria:
     - Tasks page fetches from `/api/v1/schedules` on load
     - Table columns: name (agent → workflow), cadence (human-readable), timezone, next run (relative), last run + status pill, enabled toggle, actions menu
     - Status pill colour reflects last run: green/success, red/failed, yellow/running, gray/never-run
     - Filter chips: Enabled / Paused / Mine / All
     - Empty state with "Create your first scheduled task" CTA wired to the wizard
     - Auto-refresh every 30s (or via SSE if streaming engine #233 is available)
     - No remaining mock data references in the page source
     - Smoke test creates a schedule and confirms it appears here within one refresh

6. **#277: Run history + lifecycle actions (Run now, pause/resume, delete)**
   - Description: Each schedule has a detail view showing past runs, plus lifecycle actions (Run now, Pause / Resume, Delete). Every action emits an audit event.
   - Difficulty: Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Add the detail panel shell and wire one read-only run-history query before adding destructive actions.
   - Building with AI: Use AI to draft confirmation and disabled-state cases, then verify each action emits the expected audit event.
   - Output: Schedule detail panel, run history, run-now/pause/resume/delete actions, consent revocation, and audit coverage.
   - Acceptance Criteria:
     - Schedule detail panel reachable by clicking a Tasks row (slide-over or sub-route)
     - Header shows cadence summary, next run, owner, binding details
     - Run history table: started_at, duration, status, trigger source (`schedule` vs `manual`), link to Trajectory
     - **Run now** button — enqueues an immediate run reusing the schedule's consent envelope; respects the per-schedule concurrency lock
     - **Pause / Resume** — toggles `enabled`; paused schedules are not fired but remain in the list
     - **Delete** — confirmation dialog naming the schedule; deletes schedule + revokes consent envelope; preserves run history (orphaned but readable)
     - Each action emits an audit event: `schedule.run_now`, `schedule.pause`, `schedule.resume`, `schedule.delete`
     - Action buttons disabled when not permitted (e.g. policy denial, missing binding) with a clear tooltip reason

**Stretch Goals:**

- Add natural-language cadence creation that converts "every weekday at 8am" into the structured cadence object.
- Add a calendar-style preview of upcoming scheduled runs.
- Add schedule templates for common agent/workflow pairs.
- Add notification hooks for failed scheduled runs.

**Review Checklist:**

- Does schedule creation validate agent, workflow, binding, cadence, timezone, and consent envelope before saving?
- Do scheduled firings travel through the same Trust Ladder, Destination Decider, sandbox, and Trajectory path as interactive runs?
- Is the scheduler restart-safe, including explicit misfire behavior and duplicate-fire protection?
- Is the Tasks page backed by live schedule data with no remaining mock dependency?
- Are lifecycle actions audited and reflected in run history?
