Status: approved
Approved at: 2026-08-30T12:31:17+08:00
Approved from: 使用者回覆「確認」，並指定完整措辭「提示詞、文件與文章應直接陳述期望行為，避免不必要的防禦性用語。」

# Lightweight implementation graph specification

## Observable behavior

1. Every `leveraging-tasks` run begins with one concise `Alignment:` statement
   that restates the requested task and intended outcome in the model's own
   words.
2. A decision-complete alignment proceeds directly; a consequential user-owned
   decision routes to `grilling`.
3. Before implementation, the agent names the simplest credible `Reality
   anchor:` and the checkpoint that will establish the result.
4. Implementation follows the target project's native practices and the method
   chosen by the user and agent inside the anchor.
5. Verification exercises the chosen anchor and maps every requirement to its
   observed evidence and result.
6. Mini SDD continues to route Inline/Durable work and gate durable production
   edits on approval.
7. Both root prompts trigger `leveraging-tasks` and its Alignment/Reality anchor
   declarations before the first production edit; the skill owns graph details.
8. `CLAUDE.md` and `AGENTS.md` contain the exact principle：「提示詞、文件與文章應
   直接陳述期望行為，避免不必要的防禦性用語。」
9. A real agent behavior eval observes Alignment and Reality anchor declarations
   while preserving existing Inline/Durable behavior.

## Edge cases

- The Alignment statement is a working interpretation rather than a mandatory
  user checkpoint.
- Human judgment remains available when suitability is the actual completion
  criterion.
- Read-only or documentation work may use focused review when that is the
  closest credible contact with reality.
- Specialized and project-local instructions refine the method for their own
  scope.

## Compatibility constraints

- Preserve the existing Inline contract and authorization lines.
- Preserve durable requirements/spec/design/verification artifacts and their
  approval semantics.
- Preserve the per-requirement `pass`/`fail`/`unknown` evidence table.
- Keep the always-loaded skill within its current line budget.
- Keep the exact writing principle identical across both root prompts.
- Preserve installer ownership with exact-target cleanup for retired managed
  skills and user-owned same-name paths.

## Non-goals

- No new universal development methodology.
- No Straw Boss dispatch state or coordination taxonomy in this user root.
- No change to external projects or their practices.
- No commit, push, tag, release, or hosted deployment.

## Applied standards

- [`AGENTS.md`](../../../AGENTS.md): read before write, explain decisions, verify
  before claiming success, and route source changes through `leveraging-tasks`.
- [`skills/writing-great-skills/SKILL.md`](../../../skills/writing-great-skills/SKILL.md):
  state positive target behavior, keep one source of truth, and remove sediment
  instead of layering exceptions.
- [`docs/design-principles.md`](../../../docs/design-principles.md): keep the
  user-root layer thin and use the lightest process that preserves intent and proof.

## Evidence and precedent

- Straw Boss `choosing-graph` separates the reality anchor from the method
  inside it; this design adopts that boundary without its coordination machinery.
- [`skills/leveraging-tasks/SKILL.md`](../../../skills/leveraging-tasks/SKILL.md)
  is the single source of truth for the user-root implementation graph.
- [`tests/prompts.sh`](../../../tests/prompts.sh) guards load-bearing prompt text,
  and [`evals/mini-spec-3r.sh`](../../../evals/mini-spec-3r.sh) exercises the real
  installed prompt surface.

## Correctness strategy

First update prompt guards and behavior-eval assertions so the current graph
fails the new Alignment and Reality anchor contract. Then replace the active
general guidance with the positive graph, retire the obsolete method-specific
skill from repository and installed surfaces, and update current documentation.
Run prompt, install, uninstall, shell, static, and real agent behavior checks.
Finally run the real installer and inspect exact installed links and active
prompt text.

## Human appropriateness question

None after the user confirms that this positive graph matches the intended
lightweight user-root behavior.
