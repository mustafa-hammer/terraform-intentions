### 257: Community Connections — Identity & Env-Var Pass-Through (OSS)

**Product Focus:** EnterpriseOS

**Objective:** The v1 OSS roadmap promises "Sandbox, propagated identity, connections." The sandbox runtime and Trajectory-scoped identity exist, but there is no first-class **Connection** concept yet. This epic adds Connection definitions to the OSS edition and wires them so identity + env vars flow into sandboxes at launch.

**Why it matters for EnterpriseOS users:** EnterpriseOS users need a simple way to declare which outside systems an agent can reach, pass only the right scoped material into a sandbox, and audit each resolution. A shared Connection model lets Community users start with local keyring-backed credentials while preserving the same agent and skill contract for Enterprise deployments.

**Primary Output:** Closes out the v1 OSS promise. Lets the demo show an agent that says "I need a GitHub connection and a database connection" — the user picks named connections, the sandbox launches with the right env, and the agent works against real services without secrets leaking.

**Expected PR Shape:** Add Connection model/storage/API, auth-type plugin registry, identity env contract, launch-time connection resolution, Connections UI, per-resolution audit events, keyring persistence, local connection config files, tests for secret redaction and tenant isolation, and demo notes.

**Definition of Done:**

- A `Connection` is a typed, named definition: `id`, `kind`, `target`, `auth_type`, `credential_refs`, owning scope
- Built-in connection auth types: `env_var`, `bearer_token`, `basic_auth`, `header_token`
- Agents can declare required connections in their manifest; sandbox launch fails fast if any are missing
- At launch, the requested connections are resolved into env vars and injected into the sandbox process — never on the command line, never logged
- Identity context propagates from the agent loop into the sandbox env
- Connections page in the UI lets a user define, edit, and revoke connections
- Every connection resolution emits an audit event — never the secret

**Stories:**

1. **#251: Connection data model + registry (storage + CRUD API)**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Define the Connection JSON shape and tenant-scoping rules before choosing the storage implementation.
   - Output: Connection model, registry/storage layer, CRUD API, validation, and tenant-isolation tests.

2. **#252: Connection auth-type plugins (env_var, bearer, basic, header)**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write one table that maps each auth type to required refs, env vars, and header hints.
   - Output: AuthType interface, built-in plugin implementations, registry, and redaction-focused tests.

3. **#253: Identity context propagation into the sandbox environment**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: New AI user
   - First useful step: Document the exact environment variable names and where each value comes from in the request context.
   - Output: Sandbox identity env contract, launch helper changes, Trajectory snapshot, and smoke test.

4. **#254: Resolve required connections to sandbox env vars at launch**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Add a fake manifest with one required connection and walk the launch path until it can fail before starting a sandbox.
   - Output: Manifest field, launch-time resolver, fail-fast errors, env injection, and integration tests.

5. **#255: Connections page in the UI (list, define, edit, revoke)**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Build the empty state and table from live API data before adding the new-connection wizard.
   - Output: Connections page, create/edit/revoke flows, filters/search, masked display, and activity feed entries.

6. **#256: Per-connection audit events on every resolution**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Define the audit event payload and add one test that fails if a known fake secret appears in it.
   - Output: Resolution audit events, last-used updates, Logs page visibility, and redaction tests.

7. **#279: Persist Connection secrets via the Keyring SecretStore**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Choose the ref naming convention and write a create/update/delete transaction outline that handles rollback.
   - Output: Keyring-backed connection secret persistence, rollback behavior, masked responses, and CI redaction scan.

8. **#280: Per-connection local configuration file**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Create a sample connection fixture file with refs only and validate it against the intended schema.
   - Output: Per-connection file store, atomic writes, fsnotify reloads, sample fixture, and schema-rejection tests.

**Stretch Goals:**

- Add an import/export format for non-secret connection definitions that can be shared without credential values.
- Add a connection test action that validates reachability without exposing resolved secrets.
- Add richer connection kinds for common developer systems such as GitHub, Postgres, Jira, and Slack.

**Review Checklist:**

- Does the Connection model keep secret values out of persisted non-secret config and API responses?
- Are required connections declared by agents and resolved before sandbox launch starts?
- Does identity context propagate through a documented, stable sandbox environment contract?
- Do audit events cover both successful and failed connection resolution without leaking values?
- Is there evidence that keyring persistence, local config files, and UI flows all use the same Connection contract?
