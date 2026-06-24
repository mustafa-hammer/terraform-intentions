### HC-AI-002: Terraform Module Modernization Assistant

**Product Focus:** Terraform

**Scenario:** Scenario C, Platform Engineering Org.

**Objective:** Build an AI-assisted workflow that helps a platform team review an old Terraform module and produce a modernization plan with safe, incremental changes.

**Why it matters to RTS:** Customer platform teams often know a module is painful but are unsure which improvements are safe to tackle first. This gives RTS a practical method for helping customers modernize modules in small steps while calling out state, provider, and rollout risks that need deeper review.

**Primary Output:** A module-modernization assistant that analyzes a fake but realistic legacy module and generates a prioritized improvement plan.

**Expected PR Shape:** Add a fake but realistic legacy module, an AI workflow or prompt pack, modernization output examples, tests/checks, and a README.

**Definition of Done:**

- The assistant reviews a fake but realistic legacy module.
- It produces a modernization plan with at least five concrete recommendations.
- It separates quick wins from risky refactors.
- It includes a human-review checklist for module owners.
- It produces a demoable interaction or script.

**Stories:**

1. **Define modernization criteria**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Make a short list of what makes a Terraform module easy or hard for a customer team to maintain.
   - Building with AI: Ask AI to propose criteria, then refine them using Terraform module best practices and customer-delivery experience.
   - Output: Criteria covering inputs, outputs, providers, state risk, testing, and documentation.
2. **Create the fake legacy module**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Generate a tiny module with a few obvious issues, then add notes that explain what is intentionally wrong.
   - Building with AI: Generate a realistic but fake Terraform module with known problems.
   - Output: Legacy module example and issue notes.
3. **Build the modernization workflow**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Run the assistant against the example module and ask it for quick wins before risky changes.
   - Building with AI: Build prompts or a small agent flow that turns module review into a clear modernization plan.
   - Output: Assistant prompt/workflow and sample output.
4. **Add checks for usefulness**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write down what would make a recommendation too vague for a module owner to act on.
   - Building with AI: Use AI to draft check cases, then add checks for specificity, risk language, and actionable recommendations.
   - Output: Checklist or automated checks.
5. **Flex: Demo and RTS field note**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Record a short before/after walkthrough using one module recommendation.
   - Building with AI: Use AI to draft a field note, then edit it into customer-safe language.
   - Output: Demo script and RTS usage note.

**Stretch Goals:**

- Generate a draft PR patch for one low-risk modernization recommendation.
- Add a module-owner interview prompt for customer workshops.
- Add scoring for modernization priority.
- Add HCP Terraform/TFE rollout visibility guidance: what run history, failed plans, longer applies, policy-check failures, drift alerts, or workspace health changes should module owners watch after adopting a recommendation?

**Review Checklist:**

- Are the recommendations specific enough for a module owner to act on?
- Does the assistant avoid unsafe state or provider migration advice?
- Is there a clear separation between automated suggestion and human approval?
- Does the PR include a runnable or inspectable demo?
