### 257: Community Connections — Identity & Env-Var Pass-Through (OSS)

**Product Focus:** EnterpriseOS

**Objective:** The v1 OSS roadmap promises "Sandbox, propagated identity, connections." The sandbox runtime (`internal/sandbox/`) and Trajectory-scoped identity exist, but there is no first-class **Connection** concept yet: a named, reusable definition of "how an agent reaches X" with the auth material it needs. This epic adds Connection definitions to the OSS edition and wires them so identity + env vars flow into sandboxes at launch.

The Enterprise tier later swaps the backing store from the OS keyring (#250) to HashiCorp Vault — see the companion epic. Both editions share the Connection data model so agents and skills written for OSS run unmodified on Enterprise.

**Why it matters for EnterpriseOS users:** EnterpriseOS users need a simple way to declare which outside systems an agent can reach, pass only the right scoped material into a sandbox, and audit each resolution. A shared Connection model lets Community users start with local keyring-backed credentials while preserving the same agent and skill contract for Enterprise deployments.

**Primary Output:** Closes out the v1 OSS promise. Lets the demo show an agent that says "I need a GitHub connection and a database connection" — the user picks named connections, the sandbox launches with the right env, and the agent works against real services without secrets leaking.

**Expected PR Shape:** Add Connection model/storage/API, auth-type plugin registry, identity env contract, launch-time connection resolution, Connections UI, per-resolution audit events, keyring persistence, local connection config files, tests for secret redaction and tenant isolation, and demo notes showing a sandbox launched with named connections.

**Definition of Done:**

- A `Connection` is a typed, named definition: `id`, `kind`, `target`, `auth_type`, `credential_refs`, owning scope
- Built-in connection auth types: `env_var`, `bearer_token`, `basic_auth`, `header_token`
- Agents can declare required connections in their manifest; sandbox launch fails fast if any are missing
- At launch, the requested connections are resolved into env vars and injected into the sandbox process — never on the command line, never logged
- Identity context (`tenant_id`, `user_id`, `session_id`, `run_id`, `scopes`) propagates from the agent loop into the sandbox env
- Connections page in the UI lets a user define, edit, and revoke connections (values stored via the Keyring `SecretStore`, only refs in connection config)
- Every connection resolution emits an audit event with `connection_id`, requester, decision, sandbox_id — never the secret

**Related:**
Depends on #227 (sandbox + connection broker mechanism), #245 (`SecretStore` interface).

**Stories:**

1. **#251: Connection data model + registry (storage + CRUD API)**
   - Description: Add a `Connection` data model under `internal/connections/` with persistent storage and a CRUD API. A Connection is the typed, reusable handle that an agent declares it needs; the actual secret material lives in the `SecretStore`, the connection only holds refs.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Define the Connection JSON shape and tenant-scoping rules before choosing the storage implementation.
   - Building with AI: Ask AI to compare DB-backed and file-backed registry designs against the existing repo patterns, then document the chosen path.
   - Output: Connection model, registry/storage layer, CRUD API, validation, and tenant-isolation tests.
   - Acceptance Criteria:
     - Schema: `id`, `kind` (e.g. `github`, `postgres`, `http`), `name`, `target` (URL/host/db), `auth_type`, `credential_refs` (map of slot → SecretStore ref), `owner` (user_id), `tenant_id`, `created_at`, `last_used_at`
     - Migration checked in under `internal/db/migrations/`
     - CRUD endpoints: `GET /api/v1/connections`, `GET /api/v1/connections/:id`, `POST`, `PATCH`, `DELETE`
     - Connections are tenant-scoped via existing auth middleware
     - Creation rejects unknown `auth_type` values with a structured error
     - Delete removes the connection and detaches (but does not delete) referenced SecretStore entries
     - Unit tests cover round-trip, tenant isolation, and validation errors

2. **#252: Connection auth-type plugins (env_var, bearer, basic, header)**
   - Description: Implement the four built-in connection auth-type plugins. Each plugin knows how to (a) validate its credential refs, (b) materialize the credential as env-var slots, and (c) optionally hint headers for outbound HTTP from the agent gateway later.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write one table that maps each auth type to required refs, env vars, and header hints.
   - Building with AI: Use AI to generate plugin test cases, especially malformed refs and redaction-in-error cases.
   - Output: AuthType interface, built-in plugin implementations, registry, and redaction-focused tests.
   - Acceptance Criteria:
     - `AuthType` interface: `Validate(refs) error`, `Materialize(ctx, store, refs) (map[string]string, error)`
     - `env_var` — pass-through; refs map directly to env var names
     - `bearer_token` — single secret ref; materializes as `<NAME>_TOKEN` env + `Authorization: Bearer ...` header hint
     - `basic_auth` — username + password refs; materializes as `<NAME>_USER` / `<NAME>_PASS` + `Authorization: Basic ...` hint
     - `header_token` — single secret ref + header name; materializes as env + header hint
     - Materialize never logs or returns the secret value in errors
     - Plugins registered in a small registry so future auth types (`oauth2_client_credentials`, etc.) plug in cleanly
     - Unit tests for each plugin including the redaction-in-errors case

3. **#253: Identity context propagation into the sandbox environment**
   - Description: Identity context (`tenant_id`, `user_id`, `session_id`, `run_id`, declared `scopes`) must flow from the agent loop into the sandbox environment so a sandbox can attribute its own actions and tools downstream can verify them. Today the agent loop carries `run_id` and `trajectory`; this story extends that into a stable env contract for sandboxes.
   - Difficulty: Beginner to Intermediate
   - Suggested owner: New AI user
   - First useful step: Document the exact environment variable names and where each value comes from in the request context.
   - Building with AI: Ask AI to create a simple smoke-test script that prints only non-secret identity vars and validates they are present.
   - Output: Sandbox identity env contract, launch helper changes, Trajectory snapshot, and smoke test.
   - Acceptance Criteria:
     - Documented env contract: `ENTERPRISEOS_TENANT_ID`, `ENTERPRISEOS_USER_ID`, `ENTERPRISEOS_SESSION_ID`, `ENTERPRISEOS_RUN_ID`, `ENTERPRISEOS_SCOPES` (comma-separated)
     - Sandbox launch helper in `internal/sandbox/` injects these from the request context
     - Values never appear on the command line — env only
     - Backwards compatible: if a downstream tool ignores the vars, behavior is unchanged
     - Trajectory record gains an `identity_envelope` snapshot for the run
     - Smoke test launches a sandbox that echoes the env vars; asserts each is non-empty and correct

4. **#254: Resolve required connections to sandbox env vars at launch**
   - Description: When an agent declares required connections, the sandbox launcher resolves each via the registry + auth-type plugins, materializes them into env vars, and injects them at launch. Missing or invalid connections fail fast with a clear reason before any sandbox process starts.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Add a fake manifest with one required connection and walk the launch path until it can fail before starting a sandbox.
   - Building with AI: Use AI to draft the failure-mode matrix for missing, denied, invalid, and successful resolutions.
   - Output: Manifest field, launch-time resolver, fail-fast errors, env injection, and integration tests.
   - Acceptance Criteria:
     - Agent / skill manifest gains a `requires_connections: [{ id, slot }]` field
     - Sandbox launch resolves each requested connection via the registry → plugin → SecretStore
     - Env vars assigned per the manifest's `slot` name (`<SLOT>_TOKEN`, `<SLOT>_USER`, etc.)
     - If any required connection is missing or fails policy, launch returns 412 with the failing connection id and reason — no sandbox is started
     - Resolved env vars merged with the identity envelope from STORY_10_3 (`#`-link will resolve once filed)
     - Existing Claude / Bob Shell launchers refactored to use this path (no regression)
     - Integration test covers happy path, missing connection, and invalid auth-type

5. **#255: Connections page in the UI (list, define, edit, revoke)**
   - Description: Build a Connections page in the web UI where users define, edit, and revoke connections. Values are written through the `SecretStore`; the page never displays a secret value, only the masked tail.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Build the empty state and table from live API data before adding the new-connection wizard.
   - Building with AI: Ask AI to generate wizard state diagrams and validation messages, then adapt them to existing UI conventions.
   - Output: Connections page, create/edit/revoke flows, filters/search, masked display, and activity feed entries.
   - Acceptance Criteria:
     - New "Connections" sidebar entry (or a tab under Settings, whichever fits the existing nav)
     - Table view with columns: name, kind, auth type, last used, status, actions
     - "New connection" wizard: pick kind → pick auth type → fill required fields (password-style inputs) → save
     - Edit allows renaming + rotating credential refs; never reveals stored values
     - Revoke marks the connection inactive and removes the SecretStore entries
     - Filter by kind; search by name
     - Activity feed entry on create / edit / revoke
     - Empty state with a "create your first connection" CTA

6. **#256: Per-connection audit events on every resolution**
   - Description: Every connection resolution (success or failure) emits a structured audit event into the streaming engine. The event never carries the secret value — only the connection id, requester, decision, and sandbox id.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Define the audit event payload and add one test that fails if a known fake secret appears in it.
   - Building with AI: Use AI to produce sample success/failure events and then manually remove any field that could leak credential material.
   - Output: Resolution audit events, last-used updates, Logs page visibility, and redaction tests.
   - Acceptance Criteria:
     - Audit event shape: `ts`, `event=connection.resolve`, `connection_id`, `tenant_id`, `user_id`, `session_id`, `run_id`, `sandbox_id`, `decision` (`granted`/`denied`/`error`), `reason`
     - Emitted from the sandbox launch resolution path (STORY_10_4)
     - `last_used_at` on the connection row updated on grant
     - No secret value, no env-var value, ever included in the event
     - Test asserts the redaction property by attempting to log a known secret and grepping the event payload
     - Events visible on the Logs page filtered by `event=connection.resolve`

7. **#279: Persist Connection secrets via the Keyring SecretStore**
   - Description: Connection secret material (tokens, passwords, header values) is persisted via the `SecretStore` interface (#245) — which on the desktop is the Tauri keyring plugin (#244) and on the server is the OS keyring via `go-keyring`. Connection auth-type plugins (#252) write through `SecretStore.Set` on configure; the per-connection config file (#280) holds only refs, never values.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Choose the ref naming convention and write a create/update/delete transaction outline that handles rollback.
   - Building with AI: Ask AI to find rollback and partial-write edge cases, then turn those into tests with fake known-secret values.
   - Output: Keyring-backed connection secret persistence, rollback behavior, masked responses, and CI redaction scan.
   - Acceptance Criteria:
     - Ref naming convention: `connections/<connection_id>/<slot>` (e.g. `connections/c_8f3a/bearer_token`, `connections/c_8f3a/basic_user`, `connections/c_8f3a/basic_pass`)
     - All four built-in auth-type plugins (`env_var`, `bearer_token`, `basic_auth`, `header_token`) write secrets via `SecretStore.Set` using this scheme
     - Connection create / update flow writes secrets first, then writes the config file; rolls back the keyring entries if the config write fails
     - Connection delete revokes the matching keyring entries before removing the config file
     - On the desktop (Tauri), writes go through `enterpriseos.secrets.set` (the JS bridge from #244); on the server, through the Go OS keyring binding (#245)
     - Secret values never appear in connection list / detail API responses; only refs and masked tails (last 4 chars)
     - Audit event per `secrets.set` / `secrets.delete` with the ref (never the value)
     - Lint / test: a grep against the connection config directory for any known-secret string fails CI

8. **#280: Per-connection local configuration file**
   - Description: Each Connection's non-secret configuration lives in its own file under `~/.enterpriseos/connections/<id>.json`. The file is the source of truth for Community Edition; the server reads the directory on startup and watches for changes so manual edits or sync tools work without a restart. Secret material is **not** in the file — only refs into the keyring (see #279).
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Create a sample connection fixture file with refs only and validate it against the intended schema.
   - Building with AI: Use AI to draft load/save/hot-reload test cases, then add explicit checks for file mode and no-secret properties.
   - Output: Per-connection file store, atomic writes, fsnotify reloads, sample fixture, and schema-rejection tests.
   - Acceptance Criteria:
     - File layout: `~/.enterpriseos/connections/<id>.json` per connection, file mode 0600, directory mode 0700
     - File schema mirrors the Connection model from #251: `id`, `kind`, `name`, `target`, `auth_type`, `credential_refs` (map of slot → keyring ref), `owner`, `tenant_id`, `metadata`, `created_at`, `last_used_at`
     - No secret values in the file — `credential_refs` holds keyring ref names only
     - Server loads all `*.json` from the directory on startup; ignores files that fail schema validation with a Warning log
     - Filesystem watcher (`fsnotify`) reloads individual connections on change; debounced to 200ms
     - CRUD API from #251 reads/writes through this file store rather than a DB
     - Atomic writes via `os.Rename` from a sibling temp file to avoid partial writes
     - Delete removes the file and the matching keyring entries (#279)
     - `~/.enterpriseos/connections/` is git-ignored by default if the workspace is a repo
     - Sample fixture file checked in under `docs/samples/connection.json`
     - Unit tests cover load, save, atomic-write, hot-reload, and schema-rejection paths

**Stretch Goals:**

- Add an import/export format for non-secret connection definitions that can be shared without credential values.
- Add a connection test action that validates reachability without exposing resolved secrets.
- Add richer connection kinds for common developer systems such as GitHub, Postgres, Jira, and Slack.
- Add a migration guide showing how the Community keyring-backed model maps to the Enterprise Vault-backed model.

**Review Checklist:**

- Does the Connection model keep secret values out of persisted non-secret config and API responses?
- Are required connections declared by agents and resolved before sandbox launch starts?
- Does identity context propagate through a documented, stable sandbox environment contract?
- Do audit events cover both successful and failed connection resolution without leaking values?
- Is there evidence that keyring persistence, local config files, and UI flows all use the same Connection contract?
