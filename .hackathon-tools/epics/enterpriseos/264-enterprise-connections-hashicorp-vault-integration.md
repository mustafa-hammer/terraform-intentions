### 264: Enterprise Connections — HashiCorp Vault Integration

**Product Focus:** EnterpriseOS

**Objective:** The Community Edition stores credentials in the OS keyring. For Enterprise, that's not enough: secrets must be centrally managed, audited, rotatable, dynamically minted per-session, and revokable. This epic backs the same `SecretStore` interface and Connection types with **HashiCorp Vault**, and adds Vault-only superpowers (dynamic secrets + lease-bound sandbox sessions).

**Why it matters for EnterpriseOS users:** EnterpriseOS users in regulated or large-scale environments often already depend on Vault for centralized secret control. This epic lets EnterpriseOS reuse that trust boundary instead of inventing another credential plane, while adding dynamic, lease-bound credentials that shrink the blast radius of agent work.

**Primary Output:** Lets us tell the Enterprise story: "Community uses your laptop's keychain; Enterprise uses your existing Vault — and adds dynamic secrets and lease-bound sessions that revoke themselves the moment a sandbox closes."

**Expected PR Shape:** Add a Vault-backed `SecretStore`, Vault auth configuration, `vault_dynamic` connection auth type, lease lifecycle management, tenant/group/role path-policy mapping, Vault audit forwarding, integration tests, sample deploy policy files, and demo notes.

**Definition of Done:**

- A `vault` implementation of the `SecretStore` interface (KV v2) plugs in behind the existing interface
- Server authenticates to Vault via AppRole (default) or Kubernetes auth
- A Vault-backed Connection auth type **`vault_dynamic`** mints short-lived credentials per sandbox session
- Vault leases are bound to the sandbox session lifetime — sandbox cleanup revokes leases
- Tenant + group + role map to Vault policy paths so blast-radius is contained per-tenant
- Vault's audit device receives forwarded sandbox + connection events
- Switching from keyring to Vault is a config change — no agent or skill code changes

**Stories:**

1. **#258: Vault SecretStore implementation (KV v2)**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Write the config shape for selecting the Vault backend and map each `SecretStore` method to the matching KV v2 API call.
   - Output: Vault KV v2 store implementation, backend config, token renewal support, and integration tests.

2. **#259: Vault auth — AppRole and Kubernetes auth methods**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Define the startup config and failure behavior for AppRole and Kubernetes auth before implementing either client.
   - Output: Vault auth implementations, renewal loop, health status, sample Nomad/Kubernetes configuration, and failure tests.

3. **#260: vault_dynamic connection auth type (DB engine + AWS STS)**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Define the `vault_dynamic` connection schema for database and AWS engines.
   - Output: `vault_dynamic` auth plugin, database and AWS materializers, lease capture, and sandbox launch tests.

4. **#261: Sandbox to Vault lease lifecycle (mint on launch, revoke on cleanup)**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Draw the lifecycle from sandbox launch through cleanup and mark where leases are minted, renewed, and revoked.
   - Output: Lease tracking, renewal and revocation logic, boot reconciliation, audit events, and lifecycle tests.

5. **#262: Tenant / group / role to Vault policy path mapping**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write three example identities and the Vault paths they should and should not be allowed to resolve.
   - Output: Policy path template resolver, sample Vault policies, mismatch errors, and tenant-isolation tests.

6. **#263: Forward sandbox + connection audit events to Vault audit device**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: List the EnterpriseOS audit events that need Vault correlation ids.
   - Output: Vault audit sink, fallback behavior, correlated event payloads, docs, and forwarding tests.

**Stretch Goals:**

- Add a local demo script that starts Vault dev mode, enables a sample engine, and runs one dynamic connection resolution.
- Add a lease dashboard panel showing active leases by sandbox and remaining TTL.
- Add a Vault namespace example for Vault Enterprise deployments.

**Review Checklist:**

- Does the Vault backend implement the same `SecretStore` contract without requiring agent or skill changes?
- Are Vault auth, token renewal, and startup failure behavior explicit and testable?
- Do dynamic credentials capture leases and revoke them on cleanup, timeout, abort, and orphan sweep?
- Does tenant/group/role path mapping prevent cross-tenant connection resolution before any Vault read?
- Are audit events correlated with Vault activity without leaking secret values?
