### HC-AI-004: Terraform Policy Explanation And Fix Coach

**Product Focus:** Terraform

**Scenario:** Scenario B, Regulated Healthcare SaaS.

**Objective:** Build an AI coach that explains policy violations to Terraform practitioners and suggests safe fix paths without hiding the need for human approval.

**Why it matters to RTS:** Customer teams often experience policy failures as a blocker rather than useful guidance. This gives RTS a way to help customers understand the reason for a failure, compare safe fix options, and preserve the right approval path instead of encouraging workarounds.

**Primary Output:** A prompt pack or lightweight agent that turns fake but realistic policy failures into clear explanations, fix options, and learning notes.

**Expected PR Shape:** Add sample policy failures, prompts/workflow, expected outputs, checks, and a README.

**Definition of Done:**

- The coach handles at least three fake but realistic policy failures.
- It explains the failure in plain language and Terraform terms.
- It suggests at least two fix options per case.
- It marks risky changes that require human review.
- It includes an RTS/customer usage note.

**Stories:**

1. **Define policy failure categories**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: List common reasons a Terraform change might fail policy, such as missing tags, public access, or risky instance settings.
   - Building with AI: Ask AI to propose failure categories, then refine for Terraform governance realism.
   - Output: Category list and response template.
2. **Create policy failure examples**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Write one failing policy example and the confused question a practitioner might ask about it.
   - Building with AI: Generate example violations and expected user questions.
   - Output: Example files.
3. **Build the coach prompts/workflow**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Ask the coach to explain one policy failure in two versions: beginner-friendly and architect-friendly.
   - Building with AI: Iterate on explanations until they are concise, teachable, and product-specific.
   - Output: Prompt pack or agent flow.
4. **Build fix-safety checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write three phrases the assistant should avoid, such as "just bypass the policy" or "apply this automatically."
   - Building with AI: Create checks that penalize unsafe auto-fix language.
   - Output: Checklist or automated reviewer.
5. **Flex: Demo and review pass**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Capture one demo transcript and highlight where the coach explains the policy in plain language.
   - Building with AI: Run the Readiness Coach and convert feedback into final README improvements.
   - Output: Demo transcript and review summary.

**Stretch Goals:**

- Add a "teach me why" mode for junior practitioners.
- Add example pull request comments.
- Add a comparison against a naive generic AI response.
- Add HCP Terraform/TFE policy-check visibility: include sample policy check results, where they appear in the run, which logs or run details to inspect, and how to connect the policy failure back to workspace health and recent run history.

**Review Checklist:**

- Does the coach teach rather than merely reject?
- Are fix options product-specific and safe?
- Does it preserve human approval for risky changes?
- Is there evidence of prompt iteration?
