---
paths:
  - "**/SKILL.md"
  - "**/skills/**"
  - "**/agents/**/*.md"
---

# Skill Writing Vocabulary

When writing or editing skills, agents, or agent-system docs, use the `writing-great-skills` vocabulary.
Full definitions live in `~/.claude/skills/writing-great-skills/GLOSSARY.md` — consult it before coining a new term.

## Canonical terms

- **Predictability** — the root virtue: same process every run. Use this, not "consistency", "reliability", "robustness".
- **model-invoked / user-invoked** — the invocation axis. Use this, not "ability", "tool", "procedure", "command".
- **description** — the skill's machine-readable trigger.
- **context load / cognitive load** — the two costs of the invocation choice. Use this, not "token cost", "burden", "overhead".
- **steps / reference** — the two content types of a skill. Use this, not "workflow", "instructions", "choreography", "docs".
- **branch** — a distinct way a skill is invoked. Use this, not "path", "case", "fork".
- **completion criterion** — the condition that tells the agent a unit of work is done. Use this, not "exit condition", "stopping rule".
- **leading word** — a pretrained concept token, repeated as a token, that anchors behaviour.
- **context pointer / progressive disclosure / co-location** — how reference is reached and arranged on the information hierarchy.
- **single source of truth** — each meaning lives in exactly one authoritative place.
- **legwork** — the digging an agent does within a step. Use this, not "effort", "diligence", "coverage".

## Failure-mode names

Diagnose skill problems with these exact names: **duplication**, **sediment**, **sprawl**, **no-op**, **negation**, **premature completion**.

## Writing discipline

- Prompt the positive: state the target behaviour; keep a prohibition only as a hard guardrail, paired with what to do instead.
- Run the no-op test on every line: a line stays only if it changes behaviour versus the model's default.
- One trigger per branch in descriptions; collapse synonyms that rename the same branch.
- Make every completion criterion checkable, and exhaustive where it matters.
