### 250: Local Secrets Storage (OS Keyring)

**Product Focus:** EnterpriseOS

**Objective:** Today, AI provider API keys (Anthropic, GitHub Copilot, xAI) and connector credentials end up in `~/.enterpriseos/config.json` or env vars in plaintext. We need a real secret store that uses the OS-native credential vault: macOS Keychain, Windows Credential Manager, and Linux Secret Service.

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
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Add the plugin dependency and build a tiny renderer smoke path that can set, get, and delete one test key.
   - Building with AI: Ask AI to compare the plugin setup against the Tauri version in the repo and to draft platform-specific smoke-test notes.
   - Output: Registered Tauri keyring plugin, JS bridge, capability allowlist, and smoke-test documentation.

2. **#245: Go-side SecretStore interface + OS keyring binding**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Search all credential reads and group them into the smallest interface methods needed by providers and connectors.
   - Building with AI: Use AI to critique the interface for testability, backend swapping, and accidental secret exposure.
   - Output: `SecretStore` interface, OS keyring implementation, in-memory test store, and unit tests.

3. **#246: Migrate AI provider credentials to the keyring**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Trace provider initialization for Anthropic, Copilot, and xAI and list every plaintext key path.
   - Building with AI: Ask AI to generate a migration checklist and missing-key behavior tests for each provider.
   - Output: Provider credential migration, unconfigured-state handling, rotation behavior, and integration tests with a stub store.

4. **#247: Migrate connector credentials to the keyring**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Identify every connector credential field and design the `credential_refs` schema before changing storage.
   - Building with AI: Use AI to threat-model browser/server secret flow and turn risky paths into redaction tests.
   - Output: Connector credential-ref schema, UI write path, runtime resolution, rotate/delete handling, and audit coverage.

5. **#248: Secrets management UI (list / rotate / delete, never display)**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: New AI user
   - First useful step: Sketch the table columns and modal states using only credential refs and masked tails, never raw values.
   - Building with AI: Ask AI to generate UI states and copy for rotate/delete flows, then remove any wording that implies the value can be revealed.
   - Output: Settings Secrets page, rotate/delete flows, empty/loading/error states, and activity feed entries.

6. **#249: One-time migration from config.json to the keyring**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Build a fixture config containing fake credentials and define the before/after redacted file shape.
   - Building with AI: Use AI to draft idempotency and backup test cases, then manually verify no fake secret remains after migration.
   - Output: Migration scanner, migration prompt, redaction writer, backup behavior, and idempotency tests.

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
