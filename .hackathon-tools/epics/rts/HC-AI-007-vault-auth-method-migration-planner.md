### HC-AI-007: Vault Auth Method Migration Planner

**Product Focus:** Vault

**Scenario:** Scenario B, Regulated Healthcare SaaS.

**Objective:** Build an AI-assisted planner that helps a customer reason about moving from one Vault auth pattern to another without skipping risk, identity mapping, or rollout concerns.

**Why it matters to RTS:** Customers planning Vault auth changes need structured advice before they touch production access paths. This gives RTS a way to guide customer teams through prerequisites, identity mapping, rollout sequencing, and rollback planning before any migration work begins.

**Primary Output:** A migration-planning assistant with fake but realistic inputs, organized output, and validation checks.

**Expected PR Shape:** Add migration scenarios, prompt/workflow, plan examples, checks, and README.

**Definition of Done:**

- The planner handles at least two fake but realistic migration scenarios.
- It identifies things that must be ready first, unknowns, risks, and rollback considerations.
- It produces a phased plan suitable for human review.
- It includes a "do not automate blindly" warning.
- It includes a demo interaction.

**Stories:**

1. **Design migration plan format**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Draft the section headings a human would expect in a safe migration plan.
   - Building with AI: Ask AI to draft migration sections, then refine with Vault delivery experience.
   - Output: Plan format and response expectations.
2. **Build fake migration inputs**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Create one migration scenario with missing identity details and one with a rollback concern.
   - Building with AI: Generate migration profiles with missing information and competing constraints.
   - Output: Scenario example files.
3. **Build planner workflow**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Make the planner ask for missing context before it generates a phased plan.
   - Building with AI: Create a workflow that asks clarifying questions before generating a plan.
   - Output: Planner prompt pack or agent.
4. **Add risk and rollback checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write one example of bad migration advice the assistant must reject.
   - Building with AI: Generate bad migration advice examples and build checks to catch them.
   - Output: Checklist.
5. **Flex: Customer workshop guide**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Turn the planner's questions into a workshop agenda.
   - Building with AI: Draft a workshop facilitation guide and edit it into RTS language.
   - Output: Workshop guide and review pass.

**Stretch Goals:**

- Add a dependency map output.
- Add a migration readiness score.
- Add a human approval gate compatible with EnterpriseOS workflow concepts.

**Review Checklist:**

- Does the planner ask for missing context?
- Are migration risks and rollback called out?
- Is the output useful for a customer workshop?
- Does it avoid prescribing unsafe direct changes?
