---
name: skill-design
description: Rules for writing skills that AI agents can understand and apply correctly
when_to_use: when you create a new skill or update an existing one
---

# Goal
- Define how to describe skills so that an AI agent can decide when to use them and how to follow them.
- Standardize skill structure, naming, and cross-references across the repository.

# Scope
This skill applies to every skill-writing task in the repository. It defines the baseline goals, principles, and rules that must be followed when creating or updating any skill. If a domain-specific skill provides its own template or workflow (for example, [solution-create.skill](./files/solution-create.skill.md)), use it, but still satisfy the baseline requirements from this skill. Use the generic [skill.template.md](.claude/skills/skill-design/templates/skill.template.md) only when no domain-specific template or skill exists.

# Core Principle
- Write every skill as instructions you would need to execute the task yourself.
- If you cannot tell when the skill applies by reading `whenToUse`, the skill is not clear enough.
- **Agent clarity and convenience are the key success factors.** Every rule, example, and checklist must make the skill easier for an AI agent to understand and apply. If a skill is confusing, hard to follow, or forces the agent to guess, rewrite or split it.
- Write skill in English

# Rule

## MUST
- Treat this skill as the baseline for every skill-writing task, even when a domain-specific skill provides its own template or workflow.
- Use [skill.template.md](.claude/skills/skill-design/templates/skill.template.md) as the starting point only when no domain-specific template or skill exists for the skill you are writing.
- When you follow a domain-specific skill, still satisfy the baseline requirements of this skill: clear `whenToUse`, actionable rules, valid links, correct format, and filled `# Anti-patterns` and `# Check list` sections.
- Choose the correct skill format:
  - **Human Flat**: a single file named `{skill-name}.skill.md`. Use for self-contained skills that do not need additional files.
  - **Human Dir**: a folder named `{skill-name}.skill/` containing a file named `{skill-name}.skill.md`. Use when the skill references its own supporting files (templates, examples, diagrams, ADRs, etc.).
- Make `whenToUse` describe concrete trigger conditions, not vague marketing text. An agent must read it and know whether to apply the skill.
- Keep the skill actionable: rules, workflows, checklists, and anti-patterns must tell the agent exactly what to do.
- Use links that are resolvable from the skill file:
  - Relative to the skill file: `[label](./path/to/file.md)` or `[[./path/to/file.md|label]]`.
  - Relative to the repository root: `[label](skills/.../file.md)` or `[[skills/.../file.md|label]]`.
- Use wikilinks or standard markdown links consistently within one skill.
- For Human Dir skills, keep all referenced supporting files inside the skill folder.
- Match the folder name and the main skill file name exactly: `{skill-name}.skill/{skill-name}.skill.md`.

## SHOULD
- Provide a `# Check list` so the agent can verify it has followed the skill.
- Provide `# Anti-patterns` with concrete examples, consequences, and correct alternatives.
- Use tags that help discover related skills.
- Prefer short, focused skills over large monolithic ones.

## MAY
- Add diagrams, templates, or ADRs inside the skill folder when they make the skill easier to apply.

## SHOULD NOT
- Use absolute file-system paths or URLs that depend on the local machine.
- Leave empty hint/example blocks in the final skill file (remove them after filling the template).

## MUST NOT
- Put supporting files for a Human Flat skill outside the single markdown file.
- Use confusing or generic `whenToUse` text like "when needed" or "for development".

# Anti-patterns
- **Writing for a human reader instead of an AI agent**
  - Example: "This skill explains the importance of clean code."
  - Consequence: The agent does not know what actions to take or when to take them.
  - Instead: Write "Apply these rules when you create or refactor a class: ..."

- **Vague `whenToUse`**
  - Example: "Use this skill for best practices."
  - Consequence: The agent cannot decide whether the skill applies to the current task.
  - Instead: "Use this skill when you add logging to code or choose a log level."

- **Broken or inconsistent links**
  - Example: `[template](C:\Users\...\skill.template.md)` or `[[skill.template.md]]` used from a different folder.
  - Consequence: The agent cannot find related files.
  - Instead: Use relative links from the skill file or repository-root-relative links.

- **Mixing skill formats**
  - Example: A flat skill that also creates a `templates/` folder next to it without converting to Human Dir.
  - Consequence: Files are scattered and the skill structure is unclear.
  - Instead: Convert to Human Dir when the skill needs supporting files.

- **Leaving template hints in the final skill**
  - Example: Keeping `hint` and `example` blocks after filling the template.
  - Consequence: The final skill is noisy and harder to follow.
  - Instead: Remove all `hint`, `example`, and `code example` blocks, and the `# How Apply this template` section before committing.

- **Ignoring this skill because a domain-specific skill-writing skill exists**
  - Example: "I am following `solution-create.skill`, so I do not need to check `skill-design`."
  - Consequence: The resulting skill may have vague `whenToUse`, broken links, a missing checklist, an inconsistent format, or instructions that are hard for an agent to apply.
  - Instead: Use the domain-specific skill for specialized guidance, but verify that the baseline requirements from this skill are still met.

# Check list
- [ ] The skill is written with the agent's understanding and convenience as the primary measure of quality.
- [ ] If a domain-specific skill/template is used, the baseline requirements of this skill are still satisfied.
- [ ] The skill uses the correct format (Human Flat or Human Dir).
- [ ] The skill file name and folder name match the `name` in the front matter.
- [ ] `whenToUse` clearly states when the skill should be applied.
- [ ] All rules are actionable for an AI agent.
- [ ] All links are relative to the skill file or repository root and use markdown or wikilink syntax.
- [ ] All supporting files are inside the skill folder (for Human Dir).
- [ ] Template hints and example blocks are removed from the final skill.
- [ ] `# Anti-patterns` and `# Check list` sections are filled.

## Metadata

```yaml
tags:
- skill
- common-workflow
- documentation
```
