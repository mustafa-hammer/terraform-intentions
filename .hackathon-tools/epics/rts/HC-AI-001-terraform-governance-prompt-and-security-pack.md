### HC-AI-001: Terraform Governance Prompt And Security Pack

**Product Focus:** Terraform

**Scenario:** Scenario A, Global Bank Platform.

**Objective:** Build a reusable prompt pack and set of review checks that helps a Terraform practitioner review proposed infrastructure changes for governance, security, and operational risk before they are submitted for human review.

**Why it matters to RTS:** Customer teams often need help turning Terraform plan details into a clear delivery decision: what is changing, who could be affected, what policy concerns exist, and what needs human review. This gives RTS a repeatable way to advise customers on infrastructure risk before a change reaches approval.

**Primary Output:** A Terraform prompt/security pack with fake but realistic examples, test prompts, expected response patterns, and a demoable AI interaction.

**Expected PR Shape:** Add prompt pack files, fake but realistic Terraform plan snippets, review check cases, a README, and a short demo script or notebook that runs the pack against at least three examples.

**Definition of Done:**

- The prompt pack can review at least three Terraform change examples: low-risk, medium-risk, and high-risk.
- The output explains risk in terms a customer architect can use.
- The output distinguishes product facts from assumptions.
- The checks look for required sections such as risk, who or what could be affected, policy concerns, and recommended human follow-up.
- The README explains how RTS would use this during customer delivery.

**Stories:**

1. **Design the review workflow**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Write down the four or five questions an RTS architect would ask before approving a Terraform change.
   - Building with AI: Use an AI tool to compare at least two prompt/workflow designs, then select and document the final structure.
   - Output: Workflow design, prompt structure, and reviewer persona.
2. **Create fake but realistic Terraform examples**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Ask AI for one low-risk, one medium-risk, and one high-risk Terraform plan summary, then remove anything that looks like a real customer detail.
   - Building with AI: Generate fake but realistic Terraform plan summaries, then manually remove anything unrealistic or unsafe.
   - Output: Three safe example files with expected reviewer concerns.
3. **Build the prompt pack**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Turn the review workflow into a first prompt and run it against the low-risk example.
   - Building with AI: Iteratively build and refine prompts for product correctness, security language, and concise recommendations.
   - Output: Prompt files and example outputs.
4. **Build the review checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: List the sections every good answer must include before writing any code or reviewer prompt.
   - Building with AI: Ask AI to draft review criteria, then harden them into deterministic checks where practical.
   - Output: Check script, checklist, or Readiness Coach prompt.
5. **Flex: Package, review, and demo**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Run the current demo from a clean checkout and write down every missing setup step.
   - Building with AI: Invoke the Readiness Coach, capture feedback, and use AI to turn gaps into a final PR checklist.
   - Output: README, demo notes, review results, and PR polish.

**Stretch Goals:**

- Add Sentinel or policy-as-code examples if the repo has a natural location.
- Add a comparison mode that explains why two Terraform changes differ in risk.
- Add an EnterpriseOS-compatible description file for the prompt pack.
- Add HCP Terraform/TFE run-visibility guidance: which plan/apply logs, run history, policy checks, drift signals, and workspace health details should a reviewer inspect before making a recommendation?

**Review Checklist:**

- Does the pack give Terraform-specific, not generic, guidance?
- Does it avoid pretending to know customer-specific facts?
- Do the checks catch missing risk and impact analysis?
- Is the learning trail visible in prompts, revisions, or notes?
