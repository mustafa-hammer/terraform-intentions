### HC-AI-003: Terraform Drift Triage LangGraph Workflow

**Product Focus:** Terraform

**Scenario:** Scenario A, Global Bank Platform.

**Objective:** Build a LangGraph-centered workflow that sorts through fake but realistic Terraform drift findings and explains business impact, likely cause, owner questions, and recommended next action.

**Why it matters to RTS:** Customer teams struggle with drift because the alert rarely explains business impact, ownership, or the safest next conversation. This gives RTS a guided approach for helping customers connect drift findings to run history, workspace health, likely cause, and the right owner questions.

**Primary Output:** A small LangGraph workflow or equivalent graph-based agent prototype that demonstrates multi-step drift review.

**Expected PR Shape:** Add the workflow, fake but realistic drift examples, graph diagram or notes, check cases, and a README explaining how to run it.

**Definition of Done:**

- The workflow has at least three named nodes or steps.
- It reviews at least three fake but realistic drift scenarios.
- It produces organized output suitable for a platform team.
- It documents why LangGraph helped or did not help.
- It includes a demo command, notebook, or transcript.

**Stories:**

1. **Design the graph**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Sketch the workflow as boxes: read finding, identify impact, ask owner questions, recommend next step.
   - Building with AI: Use AI to compare graph shapes for drift review, then choose nodes and state fields.
   - Output: Graph design and state fields.
2. **Build fake but realistic drift examples**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Create one drift example caused by a manual console change and one caused by expected out-of-band automation.
   - Building with AI: Generate drift examples and owner questions, then validate that they are plausible for Terraform.
   - Output: Three scenario files.
3. **Implement the LangGraph workflow**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead or comfortable with AI tools
   - First useful step: Implement the smallest graph with one input and one final output before adding branches.
   - Building with AI: Pair with AI to implement the graph, then manually inspect and simplify the code.
   - Output: Runnable workflow.
4. **Create output and checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Decide which fields must always appear in a good drift review.
   - Building with AI: Build checks for required fields and bad advice.
   - Output: Check cases or Readiness Coach prompt.
5. **Flex: Framework learning note**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Write three bullets: where LangGraph helped, where it added work, and what the team would do differently.
   - Building with AI: Ask AI to critique the team's LangGraph usage, then write a human-edited learning note.
   - Output: README section on LangGraph lessons.

**Stretch Goals:**

- Add a LangChain-only variant and compare maintainability.
- Add a human approval checkpoint node.
- Add EnterpriseOS-compatible packaging details.
- Incorporate LangSmith to explore more of the Lang* ecosystem.
- Add HCP Terraform/TFE observability inputs, such as drift status, latest run result, plan/apply log excerpts, policy-check results, run history, and workspace health, then show how those signals change the recommended next action.

**Review Checklist:**

- Is LangGraph used for real workflow state, not just as decoration?
- Are drift findings translated into useful customer-delivery language?
- Does the team document framework tradeoffs?
- Are unsafe auto-remediation recommendations avoided?
