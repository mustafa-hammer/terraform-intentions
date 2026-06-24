### HC-AI-011: Consul Service Discovery Debugging Coach

**Product Focus:** Consul

**Scenario:** Scenario D, Multi-Region Service Operations.

**Objective:** Build an AI coach that helps an operator reason through a fake but realistic Consul service discovery issue and produce a safe troubleshooting plan.

**Why it matters to RTS:** Customer operators often need help debugging Consul service discovery without jumping straight to unsafe fixes. This gives RTS a stepwise troubleshooting method for helping customers confirm symptoms, inspect service health, explain likely causes, and choose safe next checks.

**Primary Output:** A Consul troubleshooting assistant with fake service health inputs, organized findings, and a demo.

**Expected PR Shape:** Add fake Consul scenarios, prompt/workflow, sample outputs, checks, and README.

**Definition of Done:**

- The coach handles at least two fake but realistic service discovery failures.
- It separates symptoms, likely causes, and next checks.
- It avoids destructive or unsupported fixes.
- It generates a customer-safe explanation.
- It includes a demo interaction.

**Stories:**

1. **Design troubleshooting flow**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Write the safe order for debugging: confirm symptom, inspect health, inspect registration/DNS, then recommend next checks.
   - Building with AI: Compare linear prompt versus stepwise agent workflow, then choose and document the flow.
   - Output: Troubleshooting format.
2. **Create fake Consul scenarios**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Create one fake service health problem and one fake DNS/service lookup problem.
   - Building with AI: Generate fake service health, DNS, or registration symptoms for review.
   - Output: Scenario example files.
3. **Build the debugging coach**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Test the coach on one scenario and see whether it asks for the next useful check.
   - Building with AI: Implement prompts or workflow and iterate against the scenarios.
   - Output: Coach artifact.
4. **Build safety checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: List destructive or unsupported fixes the coach must not recommend.
   - Building with AI: Generate bad troubleshooting advice examples and create checks to reject them.
   - Output: Checklist.
5. **Flex: Demo and field note**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Write a customer-safe explanation of one issue in three sentences.
   - Building with AI: Draft a customer-facing explanation and edit it for RTS delivery tone.
   - Output: Demo transcript and field note.

**Stretch Goals:**

- Add a service mesh scenario.
- Add a "what to ask the customer next" mode.
- Add a comparison to a generic LLM answer.

**Review Checklist:**

- Is the advice Consul-specific?
- Does it preserve safe troubleshooting order?
- Does it produce useful customer language?
- Is the demo inspectable?
