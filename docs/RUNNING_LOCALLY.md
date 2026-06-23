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

## 2. Choose an HMAC key

The webhook verifies every request's `X-Tfc-Task-Signature` against a shared secret. Pick
any value now and use the **same** value in TFC (step 5). For local dev:

```bash
cp .env.example .env
# edit .env so it reads:  TFI_TFC_HMAC_KEY=devsecret
```
### Optional: Use direnv for automatic environment loading

If you have [direnv](https://direnv.net/) installed, it will automatically load `.env` when you `cd` into the project:

```bash
# Install direnv (macOS)
brew install direnv

# Add to your shell (bash/zsh)
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc  # or ~/.zshrc

# Allow direnv for this project
direnv allow

# Now .env is automatically loaded when you cd into the directory
cd /path/to/terraform-intentions
# ✅ terraform-intentions environment loaded
```

With direnv, you don't need to manually export variables or use inline env vars.


You can also pass it inline (as below) instead of using `.env`.

## 3. Start the webhook server

In its own terminal (leave it running):

```bash
TFI_TFC_HMAC_KEY=devsecret uv run uvicorn terraform_intentions.app:app --port 8000
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
| `401` in server logs / TFC test fails | HMAC key in TFC ≠ `TFI_TFC_HMAC_KEY` |
| Tunnel `curl /healthz` hangs or 502 | uvicorn server isn't running on port 8000 |
| TFC can't reach endpoint after a while | tunnel was restarted → new hostname; update the run task URL |
| No check appears on the run | run task attached to the wrong stage; must be **Post-plan** |

## Tear down

`Ctrl-C` the tunnel and the server terminals. Remove or disable the run task in TFC if you
don't want it firing on future runs.
