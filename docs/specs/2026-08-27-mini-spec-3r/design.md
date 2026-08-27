# Mini Spec 3R design

## Approach

Add the three rules to the files that already own their phase, and add no new
file to the always-loaded surface. `SKILL.md` gains the Route declaration, the
Inline `Contract:`/`Authorization:` pair, the escalation list, the `proposed`
gate, and the per-requirement result rule. `MINI-SDD.md` gains the two field
shapes those rules refer to — the `spec.md` approval header and the
`verification.md` table. `DEBUGGING.md` is untouched.

The line budgets in `tests/prompts.sh` rise once, deliberately, to hold the new
surface: `SKILL.md` 100, `MINI-SDD.md` 50, `DEBUGGING.md` 35, total 185.

## Where each rule lives

| Rule | File | Section |
|---|---|---|
| Declare Inline or Durable | `SKILL.md` | Ground |
| Inline `Contract:` + `Authorization:` | `SKILL.md` | Ground |
| Escalation triggers | `SKILL.md` | Ground |
| `proposed` blocks production edits | `SKILL.md` | Spec |
| Approval header field shape | `MINI-SDD.md` | `spec.md` |
| Per-requirement evidence rule | `SKILL.md` | Verify |
| Evidence table shape | `MINI-SDD.md` | `verification.md` |

## Verification seam

Two layers, with distinct jobs.

**Deletion guards — `tests/prompts.sh`.** Static assertions that each
load-bearing line is still present, that the surface stays inside its budget,
that the persistence threshold is still stated once, that no active file routes
to OpenSpec, and that no hook configuration references the contract. These
catch an accidental removal. They are not evidence that an agent obeys the rule,
and the file says so.

**Behavior eval — `evals/mini-spec-3r.sh`.** The real interface. Each case:

1. `mktemp -d` gives a sandbox with `home/` and `project/`.
2. `scripts/install.sh --home <sandbox>/home` installs this repo's actual
   instructions and skills, and the real credentials file is copied in. The
   agent therefore reads exactly what a user would have after installing.
3. `project/` is a git repo holding one production file and one fixture.
4. `claude -p` runs with `CLAUDE_CONFIG_DIR` pointed at the sandbox home,
   `--strict-mcp-config` with an empty server set, and
   `--permission-mode bypassPermissions`, so nothing outside the sandbox
   influences the run.
5. Assertions read the sandbox filesystem, not the agent's prose.

Case C resumes case B's session by id with an explicit approval message, which
is what makes it a test of the approval transition rather than of a fresh run.

The durable prompt is deliberately decision-complete. An under-specified one
sends the agent to `grilling` and it stalls at Requirements in a headless run —
correct behavior, but it never reaches the boundary the case exists to test. The
prompt's durability comes from the lasting public contract, the stated reuse,
and the user asking to see the spec first, not from leaving questions open.

Assertions read the full turn stream, not the closing message. The declaration
lines are stated before the agent starts working, so a final-message-only view
misses them.

`--model` defaults to `sonnet` and is overridable with `EVAL_MODEL`; a contract
that only holds on the largest model is not a contract.

## Trade-offs and risks

- **The eval costs money and wall-clock time and is not deterministic.** It is
  therefore separate from `tests/`, run on demand, and asserts filesystem facts
  with generous tolerance for how the agent phrases things.
- **`install.sh --home` inside the eval doubles as install coverage.** That is a
  bonus, not the purpose; `tests/install.sh` remains the installer's own test.
- **Sandbox realism.** Copying the real credentials file is the one thing the
  sandbox borrows from the user's home. Everything else — instructions, skills,
  settings, project — is built fresh.

## Precedent

`tests/prompts.sh` already extracts and asserts on instruction text, and
`tests/install.sh` already drives `scripts/install.sh --home` against a
temporary root. The eval composes both patterns and adds the agent itself.
