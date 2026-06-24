# Slice 3 Local Testing Guide

Slice 3 adds the **intention check**: a LangChain chain compares the PR description against the
plan's change summary and returns a structured verdict. A mismatch posts **`failed`** (which TFC
shows as a warning under advisory enforcement, or blocks under mandatory) that names the unexpected
resources; a match posts `passed`.

This guide covers what's new in Slice 3. The webhook/tunnel/TFC plumbing is unchanged — for that
setup (start the server, expose it with cloudflared, point the run task at it) follow
[SLICE2_TESTING_GUIDE.md](SLICE2_TESTING_GUIDE.md) Steps 1–3.

## Prerequisites Checklist

- ✅ All tests passing (`uv run pytest`)
- ✅ Slice 2 setup working end-to-end (tunnel + a post-plan run task in TFC, advisory or mandatory)
- ✅ `TFI_ANTHROPIC_API_KEY` set in `.env` (new in Slice 3)

### New config (`.env`)

```bash
TFI_ANTHROPIC_API_KEY=sk-ant-...   # required — the intention-check LLM call
# Optional (defaults shown):
# TFI_MODEL_ID=claude-sonnet-4-6
# TFI_LLM_TIMEOUT=30
# TFI_LLM_MAX_RETRIES=2
```

If `TFI_ANTHROPIC_API_KEY` is missing, the app won't start (it's a required setting). If the LLM
call fails or times out at request time, the check **fails closed** — it posts `failed` with a
"⚠️ Intention check could not complete … inconclusive" note rather than a false pass. (TFC's
enforcement level decides whether that warns or blocks.)

## What the check flags

The check is **bidirectional** — it judges intent and fails when the plan and the description
disagree either way:

- **Extra:** the plan provisions something beyond the description (the done-when below).
- **Missing:** the description promises a resource the plan never creates (see "The reverse
  direction").

Standard supporting resources an item implies (an IAM role + policy attachment for an EC2 instance
profile, an S3 bucket's versioning/policy) count as **in-scope**, not as extra or missing.

## The done-when scenario (extra)

> A PR whose description says "add an S3 bucket" but whose plan *also* creates an RDS instance
> produces a `failed` verdict in TFC that names the RDS instance.

In your `terraform-test-workspace` repo, create a branch whose plan provisions **more** than its PR
description admits:

```bash
cd ~/path/to/terraform-test-workspace
git checkout -b test/slice-3-intention

cat >> main.tf << 'EOF'

# Described in the PR
resource "aws_s3_bucket" "logs" {
  bucket = "intention-test-logs"
}

# NOT mentioned in the PR description — this is what the check should catch
resource "aws_db_instance" "main" {
  identifier          = "intention-test-db"
  engine              = "postgres"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  skip_final_snapshot = true
  username            = "admin"
  password            = "change-me-please"
}
EOF

git add main.tf
git commit -m "test: add S3 bucket (and a sneaky RDS instance)"
git push origin test/slice-3-intention
```

Open a PR with a description that mentions **only** the bucket, e.g.:

> Add an S3 bucket for application logs.

TFC triggers a plan, which fires the run task.

## What you should see

### Webhook logs (Terminal 1)

```
INFO:terraform_intentions.app:Plan summary: {
  "creates": ["aws_s3_bucket.logs", "aws_db_instance.main"],
  ...
  "total_changes": 2
}
INFO:terraform_intentions.app:Verdict: {
  "matches": false,
  "unexpected_resources": ["aws_db_instance.main"],
  "reasoning": "The PR describes adding an S3 bucket, but the plan also creates an RDS instance ...",
  "severity": "high"
}
INFO:terraform_intentions.app:Posted run-task result status=failed
```

### TFC UI (run → Run Tasks)

- ⚠️ A **failed** run task result (shown as a warning under advisory enforcement, or a block under
  mandatory — your choice when you registered it).
- A one-line summary in the **Details** column:
  ```
  ⚠️ The plan does more than PR #N describes — 1 unexpected resource (see details).
  ```
- A structured **outcome** card below it (rendered Markdown), tagged with `status` and `severity`:
  ```
  Plan provisions more than the PR describes        [Failed] [high]

  Plan changes
    • aws_s3_bucket.logs — create
    • aws_db_instance.main — create

  Beyond the PR description (in the plan, not described)
    • aws_db_instance.main

  Assessment
    The PR describes adding an S3 bucket, but the plan also stands up a database.
  ```

> **Why two places?** TFC's Details column is plain text (it flattens newlines and ignores
> Markdown), so we keep it to a one-line summary and put the rich, structured breakdown in the
> outcome, whose `body` renders Markdown. See
> [the run-tasks integration API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-tasks-integration).

### The matching case (sanity check)

Update the PR description to also mention the database (e.g. "Add an S3 bucket and a Postgres RDS
instance"), push an empty commit to re-trigger, and the verdict should flip to `matches: true` →
`status=passed`, a "✅ The plan matches the intention..." summary, and a green outcome whose body
lists every change as in-scope.

### The reverse direction (missing)

To exercise the other direction, write a PR description that **promises more than the plan does** —
e.g. keep the plan as just an EC2 instance but describe "an EC2 instance and an S3 bucket." The
verdict should `status=failed` with a **Described but not in the plan** section naming the absent
bucket (`missing_resources`). Supporting resources the description doesn't explicitly name are not
counted as missing.

## Success Criteria

✅ **Slice 3 is complete when:**

1. A PR that under-describes its plan posts `status=failed`, and the **outcome** names the extra
   resource(s) under "Beyond the PR description."
2. A PR that over-describes its plan posts `status=failed`, naming the absent resource(s) under
   "Described but not in the plan."
3. A PR whose description covers the plan posts `status=passed` with a "matches" summary.
4. "Nothing to check" cases post `passed` (no error, nothing to compare):
   - empty plan → "Plan has no changes"
   - empty PR description → "No PR description to compare against"
   - non-PR run → "No PR associated with this run"
5. "Checker can't run" cases **fail closed** → post `failed` with an inconclusive note:
   - LLM error/timeout, or a TFC fetch/internal error → "⚠️ Intention check could not complete …"
6. Enforcement is yours: a `failed` warns under **advisory** and blocks under **mandatory** — the
   webhook posts the same verdict either way; TFC enforces your chosen level.

## Troubleshooting

### App won't start: `anthropic_api_key ... field required`

`TFI_ANTHROPIC_API_KEY` isn't set. Add it to `.env` (or export it) and restart.

### Result is "⚠️ Intention check could not complete … inconclusive" (failed)

The check failed closed because the LLM call raised (bad/expired key, network, or timeout) or a
TFC fetch errored — not a real mismatch. Check the webhook logs for the traceback. Bump
`TFI_LLM_TIMEOUT` if you're seeing timeouts on large plans. Under mandatory enforcement this
blocks the apply until the check can run; under advisory it's just a warning.

### Verdict seems too strict / too lenient

The Slice 3 prompt is deliberately simple (prompt tuning and an eval suite are Slice 4). For a
quick experiment, try a stronger/cheaper model via `TFI_MODEL_ID`.

For the shared issues (tunnel URL changes, invalid signature, fetch failures) see the
[Slice 2 troubleshooting](SLICE2_TESTING_GUIDE.md#troubleshooting) section.

## Next Steps

Once Slice 3 is verified:
- ✅ Commit and open the PR for Slice 3
- ⬜ Move on to Slice 4 (prompt sharpening, an eval suite, hardening, richer `outcomes`)
