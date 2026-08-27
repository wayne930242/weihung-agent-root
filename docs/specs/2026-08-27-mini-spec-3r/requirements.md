# Mini Spec 3R requirements

Created: 2026-08-27

## Outcome

The Mini SDD lifecycle keeps its light footprint but stops relying on the
agent's discretion at its three load-bearing moments. Each source change makes
its depth, its authority to edit, and its proof of correctness observable, and
those rules are held by a real agent-behavior eval rather than by prose
assertions alone.

## Why now

Strong models already carry out the phases without being told. What they still
drift on is the boundary work: silently choosing inline, re-asking for approval
the user already gave, starting production edits from an unconfirmed spec, and
closing on "all tests pass" instead of per-requirement evidence. The 3R contract
names exactly those three boundaries and nothing else.

## The three boundaries

- **Route.** Every source change declares Inline or Durable before the first
  production edit, and the declaration has a named escalation rule.
- **Ratify.** Inline carries a one-sentence observable Contract and records the
  user's explicit request as its Authorization; Durable carries a fixed
  `Status` / `Approved at` / `Approved from` header that only the user can move
  to `approved`.
- **Result.** Verification maps every specified requirement to evidence from a
  real interface with a `pass` / `fail` / `unknown` result.

## Required behavior

1. Inline work states one observable Contract, records the user's explicit
   source-change request as Authorization, and executes without asking for the
   approval that request already gave.
2. Escalation to Durable is triggered by material ambiguity, cross-module or
   cross-session scope, a lasting contract, high risk, scope expansion beyond
   the request, or a user asking to see the spec first.
3. A durable `spec.md` opens with `Status: proposed | approved`, `Approved at`,
   and `Approved from`. `proposed` forbids production-source edits. Only an
   explicit user reply moves it to `approved`, and that reply is what
   `Approved from` records.
4. `verification.md` records a `Requirement | Evidence | Result` row for every
   requirement in `spec.md`. `Result` is `pass`, `fail`, or `unknown`. Evidence
   names the real interface exercised and what it observed. A green suite or an
   agent's completion claim is not evidence for a requirement nothing
   exercised; such a requirement stays `unknown`.

## Verification requirements

- The existing text-consistency assertions are demoted to deletion guards. They
  may prove a rule is still written down; they may not stand in for proof that
  an agent obeys it.
- A real agent-behavior eval drives a headless agent against the installed
  instructions in an isolated sandbox and asserts observable outcomes. It covers
  at least: inline direct execution, durable stopping before any source edit,
  and durable post-approval per-requirement evidence.
- No hook enforces any part of this contract. Hooks stay logging and status
  surface; the workflow lives in the instructions the agent reads.

## Out of scope

- New phases, a task engine, an implementation diary, or a status tracker.
- Any change to the Straw Boss dispatch boundary.
- Any additional artifact file beyond the existing four.

## Research basis

The approved contract was shaped upstream against OpenAI model guidance,
Anthropic's 2026-04-08 managed-agents guidance, the two 2026-06-03 CodeMySpec
comparisons, Agent OS shape-spec, the OpenSpec spec-driven schema, Spec Kit
converge/workflows, and Superpowers 6.2/6.3 release notes. This run consumed
that conclusion rather than re-deriving it; the primary sources it did read are
this repository's own [2026-08-23 Integrated Mini SDD](../2026-08-23-integrated-mini-sdd/spec.md)
artifacts and the current skill, test, and installer sources.
