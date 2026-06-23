### HC-AI-006: Vault Policy Review And Least-Privilege Coach

**Product Focus:** Vault

**Scenario:** Scenario A, Global Bank Platform.

**Objective:** Build an AI coach that reviews fake but realistic Vault policies and explains least-privilege issues, risky capabilities, and safer alternatives.

**Why it matters to RTS:** Customer teams often need help understanding whether a Vault policy is too broad and what a safer alternative could look like. This gives RTS a customer-safe review method that explains least privilege, flags risky capabilities, and keeps final approval with the policy owner.

**Primary Output:** A policy-review prompt pack or lightweight agent with example files, expected outputs, and a review checklist.

**Expected PR Shape:** Add fake Vault policies, review prompts/workflow, sample findings, checks, and README.

**Definition of Done:**

- The coach reviews at least three policies with different risk levels.
- It identifies overbroad paths or capabilities.
- It explains risk in customer-safe language.
- It suggests safer alternatives without claiming to be authoritative.
- It includes a demo interaction.

**Stories:**

1. **Define policy risk categories**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: List what makes a Vault policy broad, risky, or hard to review.
   - Building with AI: Generate risk categories and validate them against Vault policy concepts.
   - Output: Risk categories and output template.
2. **Create fake policies**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Create one obviously broad policy and one subtle policy that needs a closer look.
   - Building with AI: Generate fake Vault policies with obvious and subtle issues.
   - Output: Policy example set.
3. **Build review prompts/workflow**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Ask the assistant to explain one policy finding without using scare language.
   - Building with AI: Iterate prompts until findings are specific and non-alarmist.
   - Output: Review assistant.
4. **Build checks and red-team cases**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Ask AI for three ways this policy coach could give bad advice, then turn those into checks.
   - Building with AI: Ask AI to find ways the coach could be wrong, then build tests/checks around those cases.
   - Output: Review checklist or automated checks.
5. **Flex: Demo and review packaging**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Build a five-minute walkthrough around one low-risk and one high-risk policy.
   - Building with AI: Use AI to generate a demo script, then tighten it for a 5-minute walkthrough.
   - Output: README, demo, review results.

**Stretch Goals:**

- Add before/after policy examples.
- Add a mode that teaches the policy syntax to new users.
- Add a comparison with manual policy-review checklist.

**Review Checklist:**

- Are policy findings specific and actionable?
- Does the coach avoid overstating certainty?
- Does it explain least privilege clearly?
- Are examples safe and realistic?
