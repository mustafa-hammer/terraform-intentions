### 250: Local Secrets Storage (OS Keyring)

**Product Focus:** EnterpriseOS

**Objective:** Today, AI provider API keys (Anthropic, GitHub Copilot, xAI) and connector credentials end up in `~/.enterpriseos/config.json` or env vars in plaintext. We need a real secret store that uses the OS-native credential vault: macOS Keychain, Windows Credential Manager, and Linux Secret Service. Tauri exposes this via [`tauri-plugin-keyring-store`](https://docs.rs/tauri-plugin-keyring-store/latest/tauri_plugin_keyring_store/); the Go server reaches the same OS store via a Go keyring library (e.g. `zalando/go-keyring`), so both the desktop UI and the local server share one credential surface.

**Why it matters for EnterpriseOS users:** EnterpriseOS users will not trust agent workflows if API keys and connector credentials are left in plaintext files. Moving local secrets into the OS keyring gives users a visible, verifiable security improvement while keeping the desktop and local server on one credential surface.

**Primary Output:** Demonstrates the security tenet ("we preference security, durability, availability") in a way the audience can see and verify on their own machine — no secret hits disk in cleartext.

**Expected PR Shape:** Add Tauri keyring wiring, Go `SecretStore` interface and OS keyring implementation, provider and connector migration code, Secrets UI, one-time config migration, redaction/audit tests, and documentation for local setup and verification.

**Definition of Done:**

- AI provider credentials (Anthropic, Copilot, xAI) and connector credentials live in the OS keyring, never in `config.json` plaintext
- The desktop app reads/writes secrets via `tauri-plugin-keyring-store`
- The Go server reads the same secrets via a Go OS keyring binding and a shared `SecretStore` interface
- A Secrets management UI lists stored credential **names** (never the value), and supports rotate / delete
- A one-time migration moves any existing plaintext credentials in `config.json` into the keyring and redacts the original file
- All read / write / delete operations emit audit events with the credential ref (never the value)

**Stories:**

1. **#244: Integrate tauri-plugin-keyring-store in the desktop shell**
   - Description: Wire [`tauri-plugin-keyring-store`](https://docs.rs/tauri-plugin-keyring-store/latest/tauri_plugin_keyring_store/) into the desktop shell so the renderer can read, write, and delete secrets through the OS-native credential vault.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Add the plugin dependency and build a tiny renderer smoke path that can set, get, and delete one test key.
   - Building with AI: Ask AI to compare the plugin setup against the Tauri version in the repo and to draft platform-specific smoke-test notes.
   - Output: Registered Tauri keyring plugin, JS bridge, capability allowlist, and smoke-test documentation.
   - Acceptance Criteria:
     - `tauri-plugin-keyring-store` added to `desktop/src-tauri/Cargo.toml` and registered in `tauri::Builder`
     - Service identifier set to `enterpriseos` so entries are namespaced in the OS keychain
     - JS bridge exposes `enterpriseos.secrets.{get,set,delete,list}(key)` from the renderer
     - Permissions / capability allowlist restricts the plugin to the configured EnterpriseOS service only
     - Smoke test: set → get → delete a value from the renderer on macOS, Windows, and Linux
     - README / desktop docs updated with the new dependency

2. **#245: Go-side SecretStore interface + OS keyring binding**
   - Description: Define a `SecretStore` interface in the Go server and implement it against the OS keyring (e.g. `github.com/zalando/go-keyring`). All credential lookups in the codebase route through this interface so swapping a backend later (Vault, KMS) is a one-place change.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Search all credential reads and group them into the smallest interface methods needed by providers and connectors.
   - Building with AI: Use AI to critique the interface for testability, backend swapping, and accidental secret exposure.
   - Output: `SecretStore` interface, OS keyring implementation, in-memory test store, and unit tests.
   - Acceptance Criteria:
     - `internal/secrets/secret_store.go` defines `SecretStore` with `Get(ctx, ref) (string, error)`, `Set(ctx, ref, value) error`, `Delete(ctx, ref) error`, `List(ctx) ([]string, error)`
     - OS keyring implementation under the same package, using a single service name (`enterpriseos`)
     - In-memory fallback used only in tests
     - Errors distinguish `ErrNotFound` from transport errors
     - Each call emits an audit event with the ref (never the value)
     - Existing config loader prefers `SecretStore` for any credential field; falls back to env only as a last resort
     - Unit tests cover happy path, not-found, and round-trip

3. **#246: Migrate AI provider credentials to the keyring**
   - Description: Move the three LLM provider credentials (Anthropic, GitHub Copilot, xAI/Grok) out of plaintext config and into the keyring. Provider initialization reads via `SecretStore`.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Trace provider initialization for Anthropic, Copilot, and xAI and list every plaintext key path.
   - Building with AI: Ask AI to generate a migration checklist and missing-key behavior tests for each provider.
   - Output: Provider credential migration, unconfigured-state handling, rotation behavior, and integration tests with a stub store.
   - Acceptance Criteria:
     - Providers under `internal/llm/` load their API keys via `SecretStore.Get(ctx, "llm/<provider>/api_key")`
     - Anthropic, Copilot, and xAI all updated; no plaintext key paths remain in `internal/llm/`
     - If a key is missing, the provider reports `unconfigured` rather than panicking
     - Provider settings UI saves through `SecretStore.Set`, not `config.json`
     - Rotation: writing a new value replaces the old; the next provider call picks it up without server restart
     - Integration test stubs `SecretStore` with the in-memory impl

4. **#247: Migrate connector credentials to the keyring**
   - Description: Connector configs in the UI today hold credential strings inline. Move every connector credential to the keyring; persisted connector config keeps only a credential **ref**, never the value.
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Identify every connector credential field and design the `credential_refs` schema before changing storage.
   - Building with AI: Use AI to threat-model browser/server secret flow and turn risky paths into redaction tests.
   - Output: Connector credential-ref schema, UI write path, runtime resolution, rotate/delete handling, and audit coverage.
   - Acceptance Criteria:
     - Connector config schema in `internal/connectors/` introduces a `credential_refs` map keyed by field name → keyring ref
     - Flip-card config UI writes credential fields through `enterpriseos.secrets.set`; the form never sends raw secrets to the catalog-config endpoint
     - Connector runtime resolves credential refs via `SecretStore.Get` at invocation time
     - Listing a connector's config shows masked values (`••••` plus last 4 chars) and a Rotate button
     - Removing a connector deletes its credential refs from the keyring
     - Audit event on every set / rotate / delete with connector_id + ref (never the value)

5. **#248: Secrets management UI (list / rotate / delete, never display)**
   - Description: Add a Settings → Secrets page in the web UI that lists every credential ref stored in the keyring, with rotate and delete actions. The page never displays the secret value.
   - Difficulty: Beginner to Intermediate
   - Suggested owner: New AI user
   - First useful step: Sketch the table columns and modal states using only credential refs and masked tails, never raw values.
   - Building with AI: Ask AI to generate UI states and copy for rotate/delete flows, then remove any wording that implies the value can be revealed.
   - Output: Settings Secrets page, rotate/delete flows, empty/loading/error states, and activity feed entries.
   - Acceptance Criteria:
     - New Settings → Secrets page
     - Lists refs grouped by domain: `llm/*`, `connectors/*`, `other/*`
     - Each row shows: ref, last-updated timestamp, last 4 chars of the value (masked), Rotate, Delete
     - Rotate opens a modal with a single password-type input; on save, calls `SecretStore.Set` and closes
     - Delete asks for confirmation; on confirm, calls `SecretStore.Delete` and refreshes
     - Page is gated behind the existing auth; no secrets returned to the browser
     - Activity feed entry per rotate / delete

6. **#249: One-time migration from config.json to the keyring**
   - Description: On first start after the keyring lands, detect any plaintext credentials in `~/.enterpriseos/config.json` (and similar files), prompt the user to migrate them into the keyring, then redact the original file.
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Build a fixture config containing fake credentials and define the before/after redacted file shape.
   - Building with AI: Use AI to draft idempotency and backup test cases, then manually verify no fake secret remains after migration.
   - Output: Migration scanner, migration prompt, redaction writer, backup behavior, and idempotency tests.
   - Acceptance Criteria:
     - Startup scan identifies known credential fields in `config.json` (LLM keys, connector creds)
     - First-run modal lists discovered credentials and asks "Migrate to keyring?"
     - On accept: writes each value via `SecretStore.Set`, then rewrites `config.json` with the value replaced by `"<ref>"` or removed
     - On decline: no changes made; reminder banner persists until dismissed or migrated
     - A backup of the original `config.json` is kept at `~/.enterpriseos/config.json.bak-<ts>` (mode 0600)
     - Migration is idempotent — running again with already-migrated config is a no-op
     - Audit events: one `secrets.migrate.started`, one `secrets.migrate.completed` with count

**Stretch Goals:**

- Add a developer command that prints credential refs and backend health without revealing values.
- Add platform-specific troubleshooting notes for locked keychains or missing Linux Secret Service.
- Add an automated redaction scan for known fake secret strings in config and connector files.
- Add a future-backend note explaining how the same `SecretStore` interface can be backed by Vault.

**Review Checklist:**

- Are provider and connector secrets removed from plaintext config and routed through `SecretStore`?
- Does the UI avoid returning or displaying secret values while still supporting rotate and delete?
- Is migration idempotent, backed up safely, and able to prove plaintext values were redacted?
- Do audit events identify refs and actions without leaking secret material?
- Is there test or demo evidence across Tauri, Go server, provider, and connector paths?
