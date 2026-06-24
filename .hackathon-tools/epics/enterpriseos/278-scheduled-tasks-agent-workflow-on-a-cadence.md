### 278: Scheduled Tasks (Agent × Workflow on a Cadence)

**Product Focus:** EnterpriseOS

**Objective:** The Tasks page in the web UI is currently mocked. This epic turns it into the real surface for **scheduled tasks**: a user picks an Agent and a Workflow, sets a cadence (cron / interval / one-time), captures a pre-authorized consent envelope for unattended runs, and the scheduler fires the binding on schedule.

**Why it matters for EnterpriseOS users:** EnterpriseOS users need agents that can perform recurring work without someone keeping a browser session open. Scheduled tasks make unattended agent work explicit, reviewable, consent-bound, and restart-safe, which is the difference between a demo interaction and a useful operating workflow.

**Primary Output:** Closes the loop on "agents that work for you." Interactive demos show what an agent *can* do; scheduled tasks show what it *does on its own*, every morning at 8am, while the user is at lunch.

**Expected PR Shape:** Add schedule data model and CRUD API, scheduler worker, cadence picker, create/edit wizard, live Tasks page wiring, run history/lifecycle actions, consent envelope reuse, restart/misfire tests, and demo notes.

**Definition of Done:**

- A user can create a scheduled task by picking an installed agent, a workflow, and a cadence
- Cadence options: cron expression, interval (every N minutes/hours/days), one-time at a specific datetime, and friendly presets (hourly, daily, weekly)
- A pre-authorized consent envelope is captured at creation; unattended runs use it instead of an interactive consent prompt
- A background scheduler worker fires due tasks; each firing produces a normal agent run with a `trigger=schedule` tag
- The existing Tasks page is wired to live data — schedule list, next run, last run, status, lifecycle actions
- Per-schedule run history view links to each run's trajectory
- Run-now, pause/resume, delete actions are available with audit events on each
- Scheduler is restart-safe — schedules persist; missed runs after downtime follow a configurable misfire policy

**Stories:**

1. **#272: Schedule data model + CRUD API**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Define the schedule schema and validation errors before adding endpoints.
   - Output: Schedule model, migration, CRUD endpoints, binding validation, and tenant-scoped tests.

2. **#273: Scheduler runtime worker (due-detection, trigger, misfire policy)**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Write the due-detection and misfire policy table before coding the worker loop.
   - Output: Scheduler worker, trigger integration, misfire handling, singleton/concurrency lock, and worker tests.

3. **#274: Cadence picker UI component (cron / interval / one-time + presets)**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: New AI user
   - First useful step: Build a static cadence picker mock with presets and a "Next 3 firings" preview before wiring API calls.
   - Output: Reusable cadence picker component, validation states, timezone support, and example page.

4. **#275: Schedule create/edit wizard (agent → workflow → cadence → consent)**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Define the wizard state machine and how it handles a missing Agent×Workflow binding.
   - Output: Create/edit wizard, binding fallback flow, consent capture, save behavior, and UI tests or demo notes.

5. **#276: Wire scheduled tasks into the existing Tasks page (replace mock)**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Remove or isolate the mock data source and render the existing table from `/api/v1/schedules`.
   - Output: Live Tasks page, filters, lifecycle action entry points, auto-refresh, and smoke-test evidence.

6. **#277: Run history + lifecycle actions (Run now, pause/resume, delete)**
   - Difficulty: Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Add the detail panel shell and wire one read-only run-history query before adding destructive actions.
   - Output: Schedule detail panel, run history, run-now/pause/resume/delete actions, consent revocation, and audit coverage.

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
