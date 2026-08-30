# Lightweight implementation graph

## Outcome and actors

Agents doing source-changing work align on the user's intent, choose a credible
reality anchor, implement through the target project's native practices, and
verify the result inside that anchor.

## In scope

- Begin source-changing work with a concise restatement of the task and intended
  outcome in the model's own words.
- Continue directly when that interpretation is decision-complete; use
  `grilling` when it reveals a consequential user-owned decision.
- Choose the simplest credible reality anchor and its checkpoint before
  implementation.
- Let the task, user, and target project determine the method inside the anchor.
- Reduce the active user-root prompt and skill surface to this positive graph.
- Trigger the source-change graph from both always-loaded root prompts before
  the first production edit.
- Add the exact root-level writing principle to both `CLAUDE.md` and
  `AGENTS.md`: 「提示詞、文件與文章應直接陳述期望行為，避免不必要的防禦性用語。」
- Update prompt guards, documentation, the real agent behavior eval, and local
  Claude/Codex installation to match.

## Out of scope

- Changes to Straw Boss, plugin caches, or project-local rules.
- Changes to Mini SDD's Inline/Durable routing, approval gate, or
  per-requirement evidence contract.
- Rewriting historical specifications.
- Commit, push, release, or hosted deployment.

## Scenarios

1. A clear source change begins with a concise model-authored interpretation,
   names a simple credible anchor, and proceeds.
2. The interpretation exposes a consequential product decision; the agent uses
   `grilling` before specifying or implementing that branch.
3. The target project supplies a development practice; the agent follows it as
   part of the project's native method.
4. The credible anchor is an executable check, a real or simulated user
   operation, human judgment, or focused review according to the work.
5. Durable work retains its approval lifecycle and records requirement-specific
   evidence from the chosen anchor.

## Confirmed decisions

- Active user-root instructions state desired behavior positively.
- The root writing principle explicitly names unnecessary defensive wording so
  the model can identify and avoid it.
- Intent alignment precedes implementation.
- The reality anchor is selected before implementation and remains as simple as
  credibility permits.
- The target project and user own the method inside the anchor.
- Root-level triggering keeps skill invocation reliable while graph details stay
  in `leveraging-tasks`.

## Open questions

None.
