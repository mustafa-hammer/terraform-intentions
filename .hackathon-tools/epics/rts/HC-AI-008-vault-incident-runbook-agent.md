### HC-AI-008: Vault Incident Runbook Agent

**Product Focus:** Vault

**Scenario:** Scenario D, Multi-Region Service Operations.

**Objective:** Build a demoable AI interaction that helps an operator review a fake but realistic Vault incident and generate a clear runbook update after resolution.

**Why it matters to RTS:** During incidents, customer teams need calm guidance that separates facts from guesses and keeps remediation decisions under human control. This gives RTS a method for helping customers triage Vault incidents, communicate next checks, and improve runbooks after the event.

**Primary Output:** A Vault incident review assistant with fake but realistic incident logs, response guidance, and post-incident runbook output.

**Expected PR Shape:** Add incident examples, assistant prompts/workflow, sample outputs, checks, and README.

**Definition of Done:**

- The assistant reviews at least two fake but realistic Vault incident scenarios.
- It separates observation, hypothesis, and recommended action.
- It includes escalation and safety language.
- It generates a post-incident runbook improvement.
- It includes a demo interaction.

**Stories:**

1. **Define incident response flow**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Write the safe order of operations: observe, form hypothesis, choose next check, escalate if needed.
   - Building with AI: Use AI to draft a response flow, then refine to avoid dangerous remediation.
   - Output: Flow and output template.
2. **Create fake incident data**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Generate a short fake log snippet and a short operator symptom report.
   - Building with AI: Generate fake logs and symptoms, then strip any unrealistic or unsafe details.
   - Output: Incident example set.
3. **Build triage assistant**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Test whether the assistant clearly labels facts versus guesses.
   - Building with AI: Iterate prompts or agent steps to produce organized incident analysis.
   - Output: Triage assistant.
4. **Build runbook update generator**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Turn one incident finding into one concrete runbook improvement.
   - Building with AI: Generate runbook updates from incident findings and validate them manually.
   - Output: Runbook update examples.
5. **Flex: Demo, review, and safety pass**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Ask the Readiness Coach to find one unsafe recommendation and fix it.
   - Building with AI: Run the Readiness Coach and ask it specifically to find unsafe incident-response advice.
   - Output: Safety notes and final demo.

**Stretch Goals:**

- Add timeline reconstruction.
- Add a "questions for the operator" mode.
- Add a comparison between first AI output and corrected human-reviewed output.

**Review Checklist:**

- Does the assistant avoid high-risk automatic remediation?
- Does it distinguish facts from hypotheses?
- Does it create a useful runbook update?
- Are incident examples clearly fake but realistic?
