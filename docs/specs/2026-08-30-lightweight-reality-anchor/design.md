# Lightweight implementation graph design

## Chosen approach

`skills/leveraging-tasks/SKILL.md` remains the graph owner. Its execution path
becomes:

1. State `Alignment:` in the model's own words.
2. Resolve a consequential user-owned decision through `grilling` when one is
   exposed.
3. State the simplest credible `Reality anchor:` and its checkpoint.
4. Implement through the target project's native practices.
5. Exercise the anchor and record requirement-specific evidence.

The obsolete method-specific skill is removed from the repository and retired
from exact repository-managed Claude/Codex links during install and uninstall.
General prompt, shared engineering, prototype, design-principle, README, and
prompt-guard references are rewritten around the positive graph.

Both root prompts carry the user's exact writing principle:
「提示詞、文件與文章應直接陳述期望行為，避免不必要的防禦性用語。」

## Interfaces and data flow

- `leveraging-tasks` supplies the Alignment and Reality anchor declarations to
  both Claude and Codex through their installed shared skill link.
- `CLAUDE.md` and `AGENTS.md` supply the writing principle and source-change
  trigger on the always-loaded root surface.
- `tests/prompts.sh` guards the load-bearing wording and active graph.
- `evals/mini-spec-3r.sh` drives an installed Claude agent and observes the
  declarations in execution order before the first production edit.
- `scripts/install.sh` and `scripts/uninstall.sh` remove only retired skill links
  whose target is this repository's former path; a different same-name target
  remains user-owned.

## Existing precedent

- The installer already uses exact-target retirement for an obsolete Codex agent.
- Prompt deletion guards already enforce load-bearing Mini SDD phrases and line
  budgets.
- The behavior eval records the full streamed conversation and production diff,
  providing an operational seam for declaration order and execution.

## Decisions and trade-offs

- The active prompt states only the desired graph. Retirement mechanics and
  absence checks live in scripts/tests rather than model-facing instructions.
- Reality anchor stays singular and method-neutral. Examples illustrate
  credibility without defining a taxonomy.
- Project-local and specialist instructions naturally refine implementation
  because `leveraging-tasks` explicitly follows the target project's native
  practices.
- Exact-target retirement protects user-owned same-name skills at the cost of
  leaving any independently installed path untouched.

## Risks

- Removing the repository directory without retiring installed symlinks would
  leave broken skill entries; install/uninstall cases cover both roots.
- Static wording alone would not prove the agent follows declaration order; the
  streamed real-agent eval checks declarations before the first production edit.
- Duplicating the writing principle in two roots creates maintenance risk; an
  exact-equality guard keeps the required duplication synchronized.

## Correctness method

Change prompt and installation tests first and observe focused failures against
the current graph. Implement the prompt, skill retirement, documentation, and
eval parser; then run focused and full prompt/install/uninstall suites, shell and
static checks, and the real behavior eval. Reinstall the real user root and
inspect both root prompts, skill links, and the updated active graph.

## Human appropriateness

The user supplied the exact root-principle wording and confirmed the graph.
