### HC-AI-014: Packer And Waypoint Golden Path Assistant

**Product Focus:** Packer and Waypoint

**Scenario:** Scenario C, Platform Engineering Org.

**Objective:** Build an AI assistant that helps a platform team describe a golden image and deployment path, then generates a draft checklist and example workflow for review.

**Why it matters to RTS:** Customer platform teams often need help turning image and deployment standards into a path application teams can actually follow. This gives RTS a way to help customers separate image-build decisions from deployment handoff decisions, identify missing inputs, and create a reviewable golden path.

**Primary Output:** A golden-path assistant with fake app inputs, image pipeline guidance, deployment handoff, and a demo.

**Expected PR Shape:** Add fake app profiles, assistant prompt/workflow, sample golden-path outputs, checks, and README.

**Definition of Done:**

- The assistant processes at least two fake but realistic app profiles.
- It produces a golden image checklist and deployment handoff.
- It separates image-build concerns from deployment concerns.
- It identifies missing security or operational inputs.
- It includes a demo interaction.

**Stories:**

1. **Define golden-path output**
   - Difficulty: Advanced
   - Suggested owner: AI Builder Lead
   - First useful step: Split the output into two columns: image-build concerns and deployment concerns.
   - Building with AI: Ask AI to draft output sections, then refine for Packer and Waypoint product boundaries.
   - Output: Output format.
2. **Create fake app profiles**
   - Difficulty: Beginner
   - Suggested owner: New AI user
   - First useful step: Create two app profiles with different deployment constraints.
   - Building with AI: Generate fake application profiles and deployment constraints.
   - Output: App profile example files.
3. **Build assistant workflow**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Make the assistant ask about missing security or runtime requirements before producing a checklist.
   - Building with AI: Build prompts or a workflow that generates checklists and asks clarifying questions.
   - Output: Assistant artifact.
4. **Build checks**
   - Difficulty: Intermediate
   - Suggested owner: Comfortable with AI tools
   - First useful step: Write one check that fails if the assistant mixes image-build and deployment responsibilities.
   - Building with AI: Generate quality checks for unclear boundaries, missing required inputs, and unsafe assumptions.
   - Output: Checklist.
5. **Flex: Demo and customer usage note**
   - Difficulty: Beginner to Intermediate
   - Suggested owner: Flex teammate
   - First useful step: Create a short walkthrough from app profile to golden-path output.
   - Building with AI: Use AI to draft a delivery note and edit it for RTS architects.
   - Output: Demo, note, review result.

**Stretch Goals:**

- Add a sample Packer template or Waypoint config stub if repo conventions are clear.
- Add a diagram generated from the assistant output.
- Add a comparison between two golden-path options.

**Review Checklist:**

- Does the assistant keep Packer and Waypoint concerns distinct?
- Are missing required inputs clearly called out?
- Is the output useful to a platform team?
- Does the PR include enough evidence for maintainers to review?
