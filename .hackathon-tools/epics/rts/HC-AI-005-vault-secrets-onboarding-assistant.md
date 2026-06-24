### HC-AI-005: Vault Secrets Onboarding Assistant

**Product Focus:** Vault

**Scenario:** Scenario B, Regulated Healthcare SaaS.

**Objective:** Build an AI-assisted onboarding flow that helps a new application team describe its secrets needs and receive a safe starting plan for Vault.

**Why it matters to RTS:** Application teams often come to Vault onboarding with incomplete requirements and uncertainty about safe patterns. This gives RTS a discovery method for helping customers describe their secrets needs, identify missing information, and leave with a human-reviewable starting plan without exposing real secrets.

**Primary Output:** A Vault onboarding assistant with fake but realistic interview questions, recommended architecture patterns, and guardrails.

**Expected PR Shape:** Add assistant prompts or workflow, sample app scenarios, recommended outputs, checks, and a README.

**Definition of Done:**

- The assistant interviews a fake but realistic app team about secret types, runtime, environment, rotation, and access.
- It produces a starting Vault onboarding plan.
- It identifies missing information instead of guessing.
- It includes safety warnings around secrets and auth methods.
- It includes a demo interaction.

**Stories:**

1. **Design the onboarding interview**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Write the first five questions an RTS architect would ask a new app team about secrets.
   - Building with AI: Use AI to draft interview paths, then refine for Vault delivery realism.
   - Output: Interview flow and response template.
2. **Generate fake app profiles**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Create one app profile with enough detail and one with missing details so the assistant must ask follow-up questions.
   - Building with AI: Generate app team profiles with incomplete but realistic requirements.
   - Output: Three app profile example files.
3. **Build assistant prompts/workflow**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Make the assistant ask one clarifying question before it is allowed to recommend anything.
   - Building with AI: Build a guided assistant that asks follow-up questions before recommending.
   - Output: Prompt pack, agent, or interactive script.
4. **Create safety and correctness checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: List the mistakes the assistant must avoid, starting with asking for or printing real secrets.
   - Building with AI: Ask AI for common Vault onboarding mistakes, then turn them into reviewer checks.
   - Output: Checklist.
5. **Flex: RTS handoff note**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Turn one assistant output into a short note an RTS architect could send to a teammate.
   - Building with AI: Draft a customer handoff note and edit it for clarity.
   - Output: Field note and demo transcript.

**Stretch Goals:**

- Add a mode for dynamic secrets versus static secrets.
- Add Kubernetes auth or AppRole decision support.
- Add a red-team prompt that tries to make the assistant leak secrets.

**Review Checklist:**

- Does the assistant ask clarifying questions before recommending?
- Does it avoid collecting or exposing real secrets?
- Are Vault patterns explained accurately?
- Is the output useful to RTS during discovery?
