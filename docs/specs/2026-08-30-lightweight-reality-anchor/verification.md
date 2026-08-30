# Lightweight implementation graph verification

## Requirement evidence

| Requirement | Evidence | Result |
|---|---|---|
| Every source-changing run states Alignment in the model's own words | Real Opus behavior eval `case_inline_executes_directly` observed `Alignment:` in the streamed assistant output before the production edit | pass |
| Decision-complete work proceeds while user-owned decisions route to grilling | Static prompt guard confirmed the decision-complete edge in `leveraging-tasks`; real Inline behavior proceeded in one turn without a confirmation pause | pass |
| The simplest credible Reality anchor and checkpoint are named before implementation | Real Opus behavior eval parsed streamed text and the first Bash `sed -i` production mutation; both Alignment and Reality anchor preceded that mutation | pass |
| Implementation follows target-project-native practices | Prompt guard confirmed the load-bearing native-practices instruction; the isolated eval used the project CLI and shell harness supplied by the sandbox | pass |
| Verification exercises the anchor and records requirement evidence | Real Inline eval ran the CLI and its check; approved Durable eval produced 9 requirement rows, each with a valid `pass`/`fail`/`unknown` verdict | pass |
| Inline/Durable routing and approval semantics remain intact | Full `tests/prompts.sh` passed; real eval observed Inline execution without artifacts, Durable `Status: proposed` before approval, and production editing only after approval | pass |
| Active roots reliably trigger the positive graph | Both roots carry the same source-change trigger; prompt guards passed; after a focused run exposed a skipped skill invocation, two consecutive isolated Opus runs observed the full graph before editing | pass |
| Both root prompts contain the exact writing principle | Prompt guard and direct installed-root inspection found「提示詞、文件與文章應直接陳述期望行為，避免不必要的防禦性用語。」in both `CLAUDE.md` and `AGENTS.md` | pass |
| Installed Claude and Codex surfaces resolve to updated repository source | Real installer removed both retired repository links; `readlink` resolved both roots and both `leveraging-tasks` skills to this repository; `claude doctor` reported no installation issues | pass |

## Feedback-loop evidence

- Initial focused prompt checks failed because Alignment, Reality anchor, and
  the exact root writing principle were absent.
- Initial fresh/upgrade install checks failed because the retired skill was
  still linked into both user roots.
- Focused guards passed after the positive graph and exact-target retirement
  were implemented; user-owned same-name paths also survived install/uninstall.
- The first real behavior eval proved the agent's actual declaration order was
  correct and exposed two oracle gaps: Bash `sed -i` was not classified as an
  edit, and a later evidence table was mistaken for the requirement table.
- After correcting only the eval oracle, the second complete Opus run passed all
  Inline, Durable proposal, approval, implementation, and evidence assertions.
- A later focused run exposed stochastic routing: the agent edited directly
  without invoking the skill. Both always-loaded roots then gained the same
  positive source-change trigger. Two consecutive isolated Opus runs passed all
  Inline graph and ordering assertions afterward.

## Additional validation

- Full `bash tests/prompts.sh`, `bash tests/install.sh`, and
  `bash tests/uninstall.sh` suites passed.
- Shell syntax checks passed for installer, uninstaller, prompt tests, install
  tests, uninstall tests, and the behavior eval.
- `git diff --check` passed.
- Active model-facing source contains no retired methodology term.
- `skills/leveraging-tasks/SKILL.md` remains within its 100-line budget; the
  complete progressively disclosed surface remains within 185 lines.
- The real installer completed and removed the two retired repository links.
- After the final root trigger was added, two consecutive real Opus Inline evals
  passed Alignment, Reality anchor, execution, and ordering assertions.

## Human appropriateness

The user confirmed the graph and supplied the exact root writing principle.

## Deviations

None from the approved behavior. The eval parser was widened to observe Bash
source edits and scoped to its named requirement table after real output exposed
the former oracle assumptions.

## Unresolved gaps

None for repository behavior and local installation. The changes are not
committed or pushed because neither action was authorized.
