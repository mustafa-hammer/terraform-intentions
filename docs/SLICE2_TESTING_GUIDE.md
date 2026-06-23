# Slice 2 Local Testing Guide

This guide walks you through testing Slice 2 functionality locally with real Terraform Cloud.

## Prerequisites Checklist

- ✅ All tests passing (`uv run pytest`)
- ✅ Smoke tests passing (`./tests/smoke_test_e2e.sh`)
- ✅ TFC workspace configured (from Slice 1)
- ✅ GitHub repo connected to TFC workspace
- ⚠️ TFC team token (we'll create this)

## Step 1: Create TFC Team Token

1. **Navigate to TFC Team Settings**
   ```
   https://app.terraform.io/app/YOUR-ORG/settings/teams
   ```

2. **Select a Team** (or create one)
   - Click on the team name (e.g., "owners")
   - Go to "Team API Token" tab

3. **Generate Token**
   - Click "Create a team token"
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

## Step 2: Start the Webhook Locally

1. **Terminal 1: Start the webhook**
   
   ```bash
   cd /path/to/terraform-intentions
   ```
   Run:
   ```bash 
   uv run uvicorn terraform_intentions.app:app --reload
   ```

   You should see:
   ```
   INFO:     Started server process [xxxxx]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   ```

2. **Verify health check**
   ```bash
   # In another terminal
   curl http://localhost:8000/healthz
   # Should return: {"status":"ok"}
   ```

## Step 3: Expose Webhook with Cloudflared

1. **Terminal 2: Start tunnel**
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

   You'll see output like:
   ```
   2026-06-23T19:00:00Z INF +--------------------------------------------------------------------------------------------+
   2026-06-23T19:00:00Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
   2026-06-23T19:00:00Z INF |  https://random-words-1234.trycloudflare.com                                               |
   2026-06-23T19:00:00Z INF +--------------------------------------------------------------------------------------------+
   ```

2. **Copy the public URL** (e.g., `https://random-words-1234.trycloudflare.com`)

3. **Test tunnel works**
   ```bash
   curl https://random-words-1234.trycloudflare.com/healthz
   # Should return: {"status":"ok"}
   ```

## Step 4: Update TFC Run Task URL

1. **Go to TFC Workspace Settings**
   ```
   https://app.terraform.io/app/YOUR-ORG/workspaces/YOUR-WORKSPACE/settings/run-tasks
   ```

2. **Edit the existing run task**
   - Click on "intention-checker" (or your run task name)
   - Update "Endpoint URL" to: `https://random-words-1234.trycloudflare.com/run-task`
   - Keep "HMAC Key" as is (from Slice 1)
   - Keep "Enforcement Level" as "Advisory"
   - Click "Update run task"

## Step 5: Trigger a Test Run

### Option A: Create a New PR (Recommended)

1. **In your terraform-test-workspace directory:**
   ```bash
   cd ~/path/to/terraform-test-workspace
   
   # Create a new branch
   git checkout -b test/slice-2-data-fetching
   
   # Add a simple resource
   cat >> main.tf << 'EOF'
   
   # Test resource for Slice 2
   resource "null_resource" "slice2_test" {
     triggers = {
       timestamp = timestamp()
     }
   }
   EOF
   
   # Commit and push
   git add main.tf
   git commit -m "test: Add null_resource for Slice 2 testing"
   git push origin test/slice-2-data-fetching
   ```

2. **Create PR on GitHub**
   - Go to your repo on GitHub
   - Click "Compare & pull request"
   - Title: "Test Slice 2: Add null resource"
   - Description: "Adding a null_resource to test Slice 2 data fetching"
   - Click "Create pull request"

3. **TFC will automatically trigger a plan**

### Option B: Manual Run (Faster, but no PR data)

1. **Go to TFC workspace**
   ```
   https://app.terraform.io/app/YOUR-ORG/workspaces/YOUR-WORKSPACE
   ```

2. **Click "Actions" → "Start new run"**
   - Reason: "Testing Slice 2 data fetching"
   - Click "Start run"

## Step 6: Watch the Logs

### Terminal 1 (Webhook logs)

You should see output like:

```
INFO:terraform_intentions.app:Received run-task payload:
{
  "access_token": "***redacted***",
  "task_result_callback_url": "https://app.terraform.io/api/v2/task-results/...",
  "plan_json_api_url": "https://app.terraform.io/api/v2/plans/plan-.../json-output",
  "configuration_version_id": "cv-...",
  ...
}
```

**For PR runs, you'll see:**
```
INFO:terraform_intentions.app:Fetched ingress attributes: {
  "is_pull_request": true,
  "pull_request_number": 5,
  "pull_request_body": "Adding a null_resource to test Slice 2 data fetching",
  "identifier": "your-org/your-repo",
  "branch": "test/slice-2-data-fetching"
}

INFO:terraform_intentions.app:Plan summary: {
  "creates": ["null_resource.slice2_test"],
  "updates": [],
  "deletes": [],
  "replaces": [],
  "total_changes": 1
}

INFO:terraform_intentions.app:PR context: repo=your-org/your-repo, PR#5, branch=test/slice-2-data-fetching
INFO:terraform_intentions.app:PR body:
Adding a null_resource to test Slice 2 data fetching

INFO:terraform_intentions.app:Posted run-task result status=passed
```

**For non-PR runs, you'll see:**
```
INFO:terraform_intentions.app:Run is not associated with a PR (is_speculative=False)
INFO:terraform_intentions.app:Posted run-task result status=passed
```

## Step 7: Verify in TFC UI

1. **Go to the run in TFC**
   ```
   https://app.terraform.io/app/YOUR-ORG/workspaces/YOUR-WORKSPACE/runs/run-...
   ```

2. **Check the "Run Tasks" section**
   
   **For PR runs:**
   - ✅ Green check mark next to "intention-checker"
   - Message: "✅ Slice 2 data gathering complete for PR #5."
   - Details showing:
     ```
     Plan changes: 1 resources
       • Creates: 1
     (LLM analysis coming in Slice 3)
     ```

   **For non-PR runs:**
   - ✅ Green check mark
   - Message: "No PR associated with this run (direct push or manual run). Skipping intention check."

## Success Criteria

✅ **Slice 2 is complete when you see:**

1. Webhook logs show:
   - ✅ Fetched ingress attributes with PR data
   - ✅ Fetched plan JSON
   - ✅ Plan summary with correct resource counts
   - ✅ PR body logged
   - ✅ Posted "passed" verdict

2. TFC UI shows:
   - ✅ Green check on run task
   - ✅ Message with PR number and resource counts
   - ✅ Advisory status (doesn't block apply)

3. Non-PR runs handled gracefully:
   - ✅ Logs show "No PR associated"
   - ✅ Still posts "passed" verdict

## Troubleshooting

### Issue: "Failed to fetch TFC data"

**Check:**
- Is `TFI_TFC_TEAM_TOKEN` set correctly in `.env`?
- Does the token have "Read workspaces" permission?
- Test token manually:
  ```bash
  curl -H "Authorization: Bearer $TFI_TFC_TEAM_TOKEN" \
    https://app.terraform.io/api/v2/organizations/YOUR-ORG/workspaces
  ```

### Issue: "No configuration_version_id in payload"

**This is expected for:**
- Manual runs without a configuration
- Verification events (TFC testing the endpoint)

**Not a problem** - webhook handles it gracefully.

### Issue: Tunnel URL changes

**Cloudflared free tunnels get new URLs each time.**

**Solution:**
- Update TFC run task URL each time you restart cloudflared
- Or use a persistent tunnel (requires cloudflared account)

### Issue: "Rejected run-task request with invalid signature"

**Check:**
- Is `TFI_TFC_HMAC_KEY` in `.env` the same as in TFC run task settings?
- Did you update the TFC run task with the new tunnel URL?

## Demo Script for Teammates

```bash
# Terminal 1: Start webhook
cd /path/to/terraform-intentions
uv run uvicorn terraform_intentions.app:app --reload

# Terminal 2: Start tunnel
cloudflared tunnel --url http://localhost:8000
# Copy the URL and update TFC run task

# Terminal 3: Trigger test
cd /path/to/terraform-test-workspace
git checkout -b demo/slice-2
echo 'resource "null_resource" "demo" {}' >> main.tf
git add main.tf
git commit -m "demo: Test Slice 2"
git push origin demo/slice-2
# Create PR on GitHub

# Watch Terminal 1 for logs showing:
# - Fetched ingress attributes
# - Plan summary
# - PR body
# - Posted verdict

# Show TFC UI with green check and message
```

## Next Steps

Once Slice 2 is verified working:
- ✅ Commit and push changes
- ✅ Create PR for Slice 2
- ✅ Move on to Slice 3 (LangChain integration)