### HC-AI-010: RTS Delivery Handoff And Gap Analyzer

**Product Focus:** Terraform and Vault

**Scenario:** Scenario C, Platform Engineering Org.

**Plain-language context:** A handoff is the note RTS gives to the next person or team before delivery starts. It should answer: what do we know, what do we still not know, what could block delivery, who needs to decide, and what should happen next?

**Objective:** Build an AI workflow that reads a messy or incomplete discovery brief and turns it into a practical RTS delivery handoff: risks, open questions, things that must be ready first, likely workstreams, and next best actions.

**Why it matters to RTS:** Customer delivery handoffs often contain useful notes but leave the next team guessing about risks, blockers, and decisions still needed from the customer. This gives RTS a method for turning discovery context into a practical delivery brief that helps customers and delivery teams align on next steps.

**Primary Output:** A delivery-handoff assistant for RTS use, with fake but realistic inputs and organized outputs.

**Expected PR Shape:** Add sample discovery briefs, handoff workflow, generated handoffs, checks, and README.

**Definition of Done:**

- The assistant processes at least two fake but realistic discovery briefs.
- It identifies gaps and open questions.
- It proposes workstreams and things that must be ready first.
- It flags security, governance, and customer-readiness risks.
- It includes a demo interaction.

**Stories:**

1. **Define handoff sections**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Write the section headings a delivery lead would need before starting customer work.
   - Building with AI: Generate candidate handoff structures, then choose one that matches RTS delivery needs.
   - Output: Handoff format.
2. **Create fake discovery briefs**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Create one brief that is clear and one brief that is missing key details.
   - Building with AI: Generate two incomplete customer briefs and mark known gaps.
   - Output: Brief example files.
3. **Build the handoff workflow**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Feed one brief into the assistant and check whether it separates known facts from questions.
   - Building with AI: Build prompts or a small agent that transforms discovery inputs into a handoff artifact.
   - Output: Handoff assistant.
4. **Create quality checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write down what would make a handoff dangerous or useless, such as inventing facts or hiding missing decisions.
   - Building with AI: Ask AI what would make a handoff dangerous or useless, then turn that into a checklist.
   - Output: Checklist.
5. **Flex: Demo and improvement log**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Run the Readiness Coach once, improve the handoff, then record what changed.
   - Building with AI: Run the Readiness Coach twice and document what changed.
   - Output: Demo, review notes, and improvement log.

**Stretch Goals:**

- Add a "PM handoff" versus "architect handoff" output mode.
- Add a customer-facing summary variant.
- Add links to relevant prompt packs or agents from other epics.
- Add an optional Terraform run-visibility section for handoffs that involve HCP Terraform/TFE: recent run history, failed plans/applies, policy-check status, drift status, and workspace health concerns.

**Review Checklist:**

- Does the handoff make next actions clearer?
- Are risks and assumptions explicit?
- Is the output useful for RTS delivery planning?
- Does the assistant avoid making unsupported claims?

## Variant Epics
