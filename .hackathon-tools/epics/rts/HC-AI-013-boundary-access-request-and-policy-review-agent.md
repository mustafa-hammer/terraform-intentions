### HC-AI-013: Boundary Access Request And Policy Review Agent

**Product Focus:** Boundary

**Scenario:** Scenario A, Global Bank Platform.

**Objective:** Build an AI interaction that reviews a fake but realistic access request and helps an operator reason about Boundary target access, approval questions, and least-privilege concerns.

**Why it matters to RTS:** Customer teams reviewing access requests need help asking better approval questions without delegating the access decision to AI. This gives RTS a least-privilege review method for helping customers identify missing justification, risky scope, and safer access alternatives.

**Primary Output:** A Boundary access-review assistant with fake access requests, organized outputs, and safety checks.

**Expected PR Shape:** Add access request examples, prompt/workflow, sample reviews, checks, and README.

**Definition of Done:**

- The assistant reviews at least three fake but realistic access requests.
- It identifies missing justification or risky scope.
- It proposes approval questions and safer alternatives.
- It avoids approving access automatically.
- It includes a demo interaction.

**Stories:**

1. **Define access review format**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: List what a reviewer needs to know before approving access.
   - Building with AI: Ask AI to draft a format, then refine it for Boundary access review.
   - Output: Review format.
2. **Create fake access requests**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Create one low-risk request and one overbroad request.
   - Building with AI: Generate fake access requests with varying risk.
   - Output: Request example files.
3. **Build review assistant**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Test whether the assistant asks for missing justification instead of approving the request.
   - Building with AI: Iterate prompts/workflow until output asks good approval questions.
   - Output: Assistant artifact.
4. **Build safety checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write one check that fails if the assistant says access is approved.
   - Building with AI: Create checks that reject automatic approval or overbroad access.
   - Output: Checklist.
5. **Flex: Customer-safe explainer**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Draft a short explanation of why least privilege matters for one request.
   - Building with AI: Draft and edit a short explanation of why access review matters.
   - Output: Explainer, demo, review pass.

**Stretch Goals:**

- Add Vault identity context as optional input.
- Add a "request more info" output mode.
- Add a manager-facing summary.

**Review Checklist:**

- Does the assistant avoid making access decisions on its own?
- Are least-privilege concerns clear?
- Are approval questions useful?
- Is the Boundary framing accurate?
