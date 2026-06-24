# Running the webhook locally (end to end)

How to start the run-task webhook on your machine, expose it with a tunnel, and wire it
to a Terraform Cloud (TFC) run task so a real plan triggers a green advisory check.

This is the Slice 1 round-trip: the webhook always returns a hardcoded `passed` — there's
no plan/PR analysis yet.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) installed (the project pins Python 3.12 via `.python-version`).
- [`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
  installed (`brew install cloudflared`). Any HTTP tunnel works; `ngrok` is fine too.
- Access to a TFC organization + workspace where you can add a run task.

## 1. Install dependencies

```bash
uv sync
```

## 2. Configure environment variables

The webhook requires two environment variables:

1. **HMAC key** - verifies every request's `X-Tfc-Task-Signature` against a shared secret
2. **TFC team token** - authenticates with TFC API to fetch plan JSON and ingress attributes

**Choose one of two methods:**

### Option A: Using .env file (recommended for most users)

```bash
cp .env.example .env
# edit .env to set:
#   TFI_TFC_HMAC_KEY=devsecret
#   TFI_TFC_TEAM_TOKEN=your-tfc-team-token-here
```

The application will automatically load `.env` on startup.

### Option B: Using direnv (automatic environment loading)

If you have [direnv](https://direnv.net/) installed:

```bash
# Install direnv (macOS)
brew install direnv

# Add to your shell
# For bash:
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc

# For zsh:
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc

# Set up .envrc
cp .envrc.example .envrc
# edit .envrc to set:
#   export TFI_TFC_HMAC_KEY=devsecret
#   export TFI_TFC_TEAM_TOKEN=your-tfc-team-token-here

# Allow direnv for this project
direnv allow
```

With direnv, environment variables are automatically loaded when you `cd` into the directory.

**Important:** The HMAC key can be any value for local dev; use the **same** value in TFC (step 5).

### Creating a TFC Team Token

The TFC team token must be a valid [team token](https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/api-tokens#team-api-tokens) with read access to the workspace.

**To create one:**

1. **Navigate to Organization Settings**
   ```
   https://app.terraform.io/app/YOUR-ORG/settings
   ```

2. **Go to API Tokens page**
   - In the left sidebar, click "API Tokens"
   - Click on the "Team Tokens" tab

3. **Create Team Token**
   - Click "Create a team token"
   - Select the team (e.g., "owners")
   - Click "Generate token"
   - Copy the token immediately (it won't be shown again)
   - Token format: `xxxxxxxxxxxxx.atlasv1.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

4. **Add to .env**
   ```bash
   # Edit .env file
   nano .env
   
   # Replace the placeholder:
   TFI_TFC_TEAM_TOKEN=your-actual-token-here
   ```

5. **Verify Token Works**
   ```bash
   # Test the token can read TFC API
   export TFI_TFC_TEAM_TOKEN="your-token"
   
   # Try to list workspaces (should return JSON)
   curl -s -H "Authorization: Bearer $TFI_TFC_TEAM_TOKEN" \
     https://app.terraform.io/api/v2/organizations/YOUR-ORG/workspaces \
     | jq '.data[0].attributes.name'
   ```
## 3. Start the webhook server

In its own terminal (leave it running):

**If using .env file:**
```bash
uv run uvicorn terraform_intentions.app:app --port 8000
```

**If using direnv:**
```bash
uv run uvicorn terraform_intentions.app:app --port 8000
```

**If passing inline (without .env or direnv):**
```bash
TFI_TFC_HMAC_KEY=devsecret TFI_TFC_TEAM_TOKEN=your-token-here uv run uvicorn terraform_intentions.app:app --port 8000
```

Verify it's up:

```bash
curl http://localhost:8000/healthz      # -> {"status":"ok"}
```

## 4. Start the tunnel and get your public URL

In a second terminal (leave it running):

```bash
cloudflared tunnel --url http://localhost:8000
```

cloudflared prints a banner with a public URL, e.g.:

```
Your quick Tunnel has been created! Visit it at:
  https://random-three-words-1234.trycloudflare.com
```

Your **run-task endpoint URL** is that hostname plus the `/run-task` path:

```
https://random-three-words-1234.trycloudflare.com/run-task
```

Confirm the tunnel reaches your server before touching TFC:

```bash
curl https://random-three-words-1234.trycloudflare.com/healthz   # -> {"status":"ok"}
```

> Note: each `cloudflared tunnel --url` run generates a **new random hostname**. If you
> restart the tunnel, update the URL in the TFC run task (step 5).

## 5. Create the run task in TFC

In the TFC UI:

1. **Organization Settings → Run Tasks → Create a run task.**
   - **Name:** e.g. `intention-checker`
   - **Endpoint URL:** the `/run-task` URL from step 4
   - **HMAC key:** the same value as `TFI_TFC_HMAC_KEY` (e.g. `devsecret`)
   - Save. TFC sends a verification ping; the endpoint acks `200` (you'll see it hit the
     server terminal).
2. **Attach it to a workspace:** open the workspace → **Settings → Run Tasks → Add run task.**
   - Select `intention-checker`
   - **Stage:** Post-plan
   - **Enforcement:** **Advisory** (a "failed" result only warns; it never blocks an apply)

## 6. Trigger a plan and watch it

Start a run in the workspace (queue a plan, or push a commit to a connected PR branch).
When the run reaches **post-plan**, TFC calls the webhook. You should see:

- the request logged in the **server** terminal,
- a **green advisory check** for `intention-checker` in the run's UI (our callback posted
  `passed`).

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| `500` error with "Field required" for `tfc_team_token` | Missing `TFI_TFC_TEAM_TOKEN` environment variable |
| `401` in server logs / TFC test fails | HMAC key in TFC ≠ `TFI_TFC_HMAC_KEY` |
| Tunnel `curl /healthz` hangs or 502 | uvicorn server isn't running on port 8000 |
| TFC can't reach endpoint after a while | tunnel was restarted → new hostname; update the run task URL |
| No check appears on the run | run task attached to the wrong stage; must be **Post-plan** |

## Tear down

`Ctrl-C` the tunnel and the server terminals. Remove or disable the run task in TFC if you
don't want it firing on future runs.
