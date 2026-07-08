---
name: skill-name
description: Short description of what the skill does and why it exists
whenToUse: Concrete conditions that tell an agent when to apply this skill
tags:
  - tag1
  - tag2
---

# How Apply this template
1. Decide the skill format:
   - **Human Flat**: use for self-contained skills. Save as `{skill-name}.skill.md`.
   - **Human Dir**: use when the skill references extra files (templates, examples, diagrams, etc.). Save as `{skill-name}.skill/{skill-name}.skill.md` and keep all supporting files inside `{skill-name}.skill/`.
2. Fill the front matter. Make `whenToUse` concrete enough that an agent can decide to use the skill just by reading it.
3. Fill each section following the `hint` blocks.
4. Remove all `hint`, `example`, and `code example` blocks, and this `# How Apply this template` section before finalizing the skill.

# Goal
```hint
List of goals that are pursued by the creation of this skill.
```

# Core Principle
```hint
Core principles the agent should follow when applying this skill.
```

# Rule
```hint
Define MUST, SHOULD, MAY, SHOULD NOT, MUST NOT rules.
If a category has no rules, skip it — do not write an empty subblock.
```

## MUST
- Choose the correct skill format.
- Keep all supporting files inside the skill folder when using Human Dir.
- Use links that are relative to the skill file or to the repository root.
- Make every rule actionable for an AI agent.

## SHOULD

## MAY

## SHOULD NOT

## MUST NOT

# Anti-patterns
```hint
Describe concrete wrong ways and their consequences.
Each item must tell the agent what NOT to do, why it is harmful, and what to do instead. Optionally it could contain example.

Format:
- **{What NOT to do}**
  - Example: {example of anti pattern}
  - Consequence: {negative consequence}
  - Instead: {correct alternative}

RECOMMENDATION:
- Prefer bullet list
- Be specific to the skill context
```
```example
- **Skip validation**
  - Consequence: service may fail during request execution or save invalid data
  - Instead: validate input at the transport boundary before the handler runs

- **Abstract log message**
  - Example: "task is done" | "Entity has been created"
  - Consequence: The message in the log does not give any idea what exactly is being discussed
  - Instead: Add additional info in message "task 'clear db' is done" | "Entity 1234 has been created"
```

# Check list
- [ ] The skill uses the correct format (Human Flat or Human Dir).
- [ ] Front matter is filled, and `whenToUse` clearly states when to apply the skill.
- [ ] All rules are actionable for an AI agent.
- [ ] All links use relative or repository-root-relative markdown/wikilink syntax.
- [ ] All template hints and example blocks are removed from the final skill.
