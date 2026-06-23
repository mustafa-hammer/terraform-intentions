### 264: Enterprise Connections — HashiCorp Vault Integration

**Product Focus:** EnterpriseOS

**Objective:** The Community Edition (#250, plus the Community Connections epic) stores credentials in the OS keyring. For Enterprise, that's not enough: secrets must be centrally managed, audited, rotatable, dynamically minted per-session, and revokable. This epic backs the same `SecretStore` interface and Connection types with **HashiCorp Vault**, and adds Vault-only superpowers (dynamic secrets + lease-bound sandbox sessions).

The contract from the Community epic stays the same — agents and skills do not change. A tenant operator flips the Enterprise backend on and the same Connections resolve through Vault.

**Why it matters for EnterpriseOS users:** EnterpriseOS users in regulated or large-scale environments often already depend on Vault for centralized secret control. This epic lets EnterpriseOS reuse that trust boundary instead of inventing another credential plane, while adding dynamic, lease-bound credentials that shrink the blast radius of agent work.

**Primary Output:** Lets us tell the Enterprise story: "Community uses your laptop's keychain; Enterprise uses your existing Vault — and adds dynamic secrets and lease-bound sessions that revoke themselves the moment a sandbox closes." This is the V1.3 + V3.0 promise made concrete.

**Expected PR Shape:** Add a Vault-backed `SecretStore`, Vault auth configuration, `vault_dynamic` connection auth type, lease lifecycle management, tenant/group/role path-policy mapping, Vault audit forwarding, integration tests using Vault dev mode or stubs, sample deploy policy files, and demo notes showing dynamic secret mint and revoke.

**Definition of Done:**

- A `vault` implementation of the `SecretStore` interface (KV v2) plugs in behind the existing interface from #245
- Server authenticates to Vault via AppRole (default) or Kubernetes auth (when running in Nomad/K8s)
- A Vault-backed Connection auth type **`vault_dynamic`** mints short-lived credentials per sandbox session (DB engine, AWS STS for the demo)
- Vault leases are bound to the sandbox session lifetime — sandbox cleanup revokes leases via `sys/leases/revoke`
- Tenant + group + role map to Vault policy paths so blast-radius is contained per-tenant
- Vault's audit device receives forwarded sandbox + connection events so SecOps has a single pane of glass
- Switching from keyring to Vault is a config change — no agent or skill code changes

**Related:**
Builds on #245 (`SecretStore` interface), #250 (Local Secrets Storage), #227 (Sandbox identity/consent/broker), and the Community Connections epic. Sets up V3.0 (Agent Gateway, all external connections brokered).

**Stories:**

1. **#258: Vault SecretStore implementation (KV v2)**
   - Description: Implement a Vault-backed `SecretStore` against the interface defined in #245. Uses Vault's KV v2 engine. Selectable at startup via config (`secrets.backend=vault`).
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Write the config shape for selecting the Vault backend and map each `SecretStore` method to the matching KV v2 API call.
   - Building with AI: Ask AI to draft Vault KV v2 integration tests and error cases, then verify them against official Vault behavior.
   - Output: Vault KV v2 store implementation, backend config, token renewal support, and integration tests.
   - Acceptance Criteria:
     - `internal/secrets/vault/vault_store.go` implements `SecretStore` against KV v2
     - Reads via `vault kv get`-equivalent API call to a configured mount + namespace
     - Writes via `vault kv put`; tombstone via `vault kv metadata delete`
     - `List` enumerates keys under the configured mount path
     - Configurable mount path, namespace (Vault Enterprise), and timeout
     - Token caching with renewal before TTL expires
     - Errors distinguish `ErrNotFound`, auth errors, and transport errors
     - Integration test uses `vault` in dev mode (`vault server -dev`) in CI

2. **#259: Vault auth — AppRole and Kubernetes auth methods**
   - Description: The server must authenticate to Vault before it can read secrets. Support **AppRole** as the default (works anywhere) and **Kubernetes** auth as the preferred method when running on Nomad/K8s with workload identity.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Define the startup config and failure behavior for AppRole and Kubernetes auth before implementing either client.
   - Building with AI: Use AI to compare AppRole and Kubernetes auth flows, then turn the differences into setup docs and health-check fields.
   - Output: Vault auth implementations, renewal loop, health status, sample Nomad/Kubernetes configuration, and failure tests.
   - Acceptance Criteria:
     - AppRole: configurable `role_id` + `secret_id` via config or env; secret_id resolvable from a file path (Nomad template)
     - Kubernetes auth: uses the projected service-account token; configurable Vault role name
     - Auth method picked via `vault.auth=approle|kubernetes` in config
     - Token renewal handled by the background loop; rotate well before expiry
     - On auth failure at startup, server logs the failure with the auth method + role and exits non-zero
     - Health check reports Vault auth status (`vault_authenticated: true|false, ttl_remaining`)
     - Documented in `deploy/` with sample Nomad job env block

3. **#260: vault_dynamic connection auth type (DB engine + AWS STS)**
   - Description: Add a new connection auth type `vault_dynamic` that mints short-lived credentials per sandbox session via Vault's dynamic secret engines. For the demo, support the **database** engine (Postgres) and **AWS STS**. The credentials are injected as env vars exactly like static connections — the agent doesn't know the difference.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Define the `vault_dynamic` connection schema for database and AWS engines, including which env vars each engine materializes.
   - Building with AI: Ask AI to draft engine-specific examples and then verify the generated fields against Vault database and AWS secrets engine behavior.
   - Output: `vault_dynamic` auth plugin, database and AWS materializers, lease capture, and sandbox launch tests.
   - Acceptance Criteria:
     - `vault_dynamic` auth type registered alongside the Community auth types
     - Connection definition includes: `engine` (`database` | `aws`), Vault `path`, and engine-specific options (DB role, AWS role)
     - On materialize, the server calls Vault to read a fresh credential
     - Returned lease ID + TTL captured against the sandbox session
     - Database engine: returns `USER` + `PASS` env vars
     - AWS STS: returns `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
     - Agent / skill manifest treats this like any other connection — no code changes
     - Test against `vault server -dev` with a stub DB engine

4. **#261: Sandbox to Vault lease lifecycle (mint on launch, revoke on cleanup)**
   - Description: A dynamic credential without a lease lifecycle is just a long-lived credential with extra steps. Bind every Vault lease to the sandbox session that triggered it: revoke on graceful close, on timeout, on abort, and on orphan-sweep at server boot.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Draw the lifecycle from sandbox launch through cleanup and mark where leases are minted, renewed, and revoked.
   - Building with AI: Use AI to generate a lease failure-mode matrix for timeout, kill, restart, and orphan cases.
   - Output: Lease tracking, renewal and revocation logic, boot reconciliation, audit events, and lifecycle tests.
   - Acceptance Criteria:
     - Lease tracking table associates `lease_id` → `sandbox_id`, `tenant_id`, `created_at`, `ttl`
     - Sandbox cleanup path calls `vault sys/leases/revoke` for each lease before tearing down
     - Timeout path same as cleanup — leases revoked before sandbox kill
     - Server boot reconciliation: revoke any lease whose sandbox no longer exists
     - Lease renewal loop refreshes leases approaching expiry while the sandbox is still alive (configurable lookahead)
     - Audit event on every mint, renew, and revoke
     - Test: launch sandbox → mint lease → kill sandbox → assert lease is revoked in Vault

5. **#262: Tenant / group / role to Vault policy path mapping**
   - Description: Map EnterpriseOS identity (tenant, groups, roles) to Vault policy paths so a tenant operator can constrain blast radius. A user in tenant `acme` and group `analysts` only resolves connections whose Vault paths satisfy a policy template like `enterpriseos/tenants/acme/analysts/*`.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write three example identities and the Vault paths they should and should not be allowed to resolve.
   - Building with AI: Ask AI to draft positive and negative policy examples, then tighten them into deterministic path-template tests.
   - Output: Policy path template resolver, sample Vault policies, mismatch errors, and tenant-isolation tests.
   - Acceptance Criteria:
     - Policy template config: `vault.path_template = "enterpriseos/tenants/{tenant}/{group}/{connection_kind}/{name}"` (configurable)
     - Each connection resolution computes the expected Vault path from the requester's identity and the connection metadata
     - Path-template mismatch returns a clear policy-violation error before any Vault call is made
     - Server boot logs the active template + a sample resolution for each known tenant
     - Sample Vault policy files committed under `deploy/vault/policies/` for the demo tenants
     - Negative test: a user in `tenantA` cannot resolve a connection under `tenantB`'s path

6. **#263: Forward sandbox + connection audit events to Vault audit device**
   - Description: Enterprise SecOps wants a single pane of glass. Forward sandbox + connection audit events into Vault's audit device so they correlate with secret read/write/lease events already captured by Vault.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: List the EnterpriseOS audit events that need Vault correlation ids and decide which sink modes are supported.
   - Building with AI: Use AI to draft sample audit payloads, then review them for correlation value and secret redaction.
   - Output: Vault audit sink, fallback behavior, correlated event payloads, docs, and forwarding tests.
   - Acceptance Criteria:
     - Configurable audit sink: `audit.sink = vault|stdout|both`
     - When `vault`, events are written via a Vault audit-compatible endpoint (file device or socket device target) configured at deploy time
     - Forwarded events: `connection.resolve`, `sandbox.launch`, `sandbox.cleanup`, `lease.mint`, `lease.revoke`
     - Events carry stable correlation ids (`run_id`, `session_id`, `sandbox_id`, `lease_id`)
     - Forwarding failures fall back to the local audit log and surface a Critical entry on the Logs page
     - Documented in `deploy/vault/` with a sample audit device config
     - Test: emit a sandbox launch event; assert it appears in the configured audit destination

**Stretch Goals:**

- Add a local demo script that starts Vault dev mode, enables a sample engine, and runs one dynamic connection resolution.
- Add a lease dashboard panel showing active leases by sandbox and remaining TTL.
- Add a Vault namespace example for Vault Enterprise deployments.
- Add a migration note explaining how existing keyring-backed connection refs map to Vault paths.

**Review Checklist:**

- Does the Vault backend implement the same `SecretStore` contract without requiring agent or skill changes?
- Are Vault auth, token renewal, and startup failure behavior explicit and testable?
- Do dynamic credentials capture leases and revoke them on cleanup, timeout, abort, and orphan sweep?
- Does tenant/group/role path mapping prevent cross-tenant connection resolution before any Vault read?
- Are audit events correlated with Vault activity without leaking secret values?
