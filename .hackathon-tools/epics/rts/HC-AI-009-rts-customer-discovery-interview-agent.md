### HC-AI-009: RTS Customer Discovery Interview Agent

**Product Focus:** Terraform and Vault

**Scenario:** Scenario A or B.

**Objective:** Build a customer-discovery agent that helps RTS architects gather the right Terraform and Vault context before a design or implementation engagement.

**Why it matters to RTS:** Customer discovery often determines whether delivery starts with the right context or with hidden gaps. This gives RTS a repeatable way to help customers surface Terraform and Vault facts, unknowns, assumptions, and next questions before design or implementation work begins.

**Primary Output:** A guided discovery assistant with product-specific question paths, fake customer answers, and a generated discovery brief.

**Expected PR Shape:** Add discovery prompt/workflow, sample interviews, generated briefs, checks, and README.

**Definition of Done:**

- The agent asks product-specific Terraform and Vault discovery questions.
- It adapts follow-ups based on answers.
- It generates a concise discovery brief for an RTS architect.
- It marks unknowns and assumptions clearly.
- It includes a demo interaction.

**Stories:**

1. **Design the discovery flow**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Start with existing RTS discovery materials and pull out the questions that must never be missed.
   - Building with AI: Ask AI to draft discovery branches, then refine with RTS delivery experience. Probably a good idea to start with pre-existing RTS discovery materials.
   - Output: Discovery tree and output template.
2. **Build fake customer personas**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Create one platform owner persona and one security stakeholder persona with different concerns.
   - Building with AI: Generate fake customer stakeholders and answers, then edit for realism.
   - Output: Persona and answer example files.
3. **Build guided interview prompts/workflow**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Make the assistant ask a follow-up question when an answer is vague.
   - Building with AI: Build an adaptive interview that asks follow-up questions, not a static questionnaire.
   - Output: Assistant workflow.
4. **Build discovery brief checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: List required sections for the brief: known facts, unknowns, assumptions, risks, and next questions.
   - Building with AI: Create checks for assumptions, missing sections, and product specificity.
   - Output: Checklist.
5. **Flex: RTS usability test**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Use the assistant as if you were an RTS architect and note where it helped or slowed you down.
   - Building with AI: Use AI to draft a usability script, then run through the assistant as an RTS architect.
   - Output: Usability notes and review result.

**Stretch Goals:**

- Add a mode that generates follow-up emails.
- Add a customer-readout summary.
- Add EnterpriseOS metadata for agent registration.
- Add a configurable "discovery depth" that controls how far the discovery branches go. Some customer discovery meetings are high-level pre-sales conversations; others are deeper scoping or delivery-readiness sessions.

**Review Checklist:**

- Does the assistant help discovery rather than replace architect judgment?
- Are Terraform and Vault questions specific and useful?
- Are assumptions clearly marked?
- Is there evidence of usability testing?
