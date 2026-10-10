# Adversarial review procedure

Use this branch for a requested adversarial code, pull-request, or report
review. It extends `SKILL.md`, which owns evidence pinning, the trust boundary,
launch parameters, the tool allowlist, the reserved matrix, and completion
delivery; the parent launches, collects, and owns parent synthesis.

## Pin the review

Add a concrete risk tier to the evidence `SKILL.md` pins. URLs are provenance
only until the parent materializes their content.

## Topology and models

Apply author-family exclusion first; stop if required origin is unknown. Prefer
a different family from a report author for any verifier.

| Risk | Discovery | Conditional verification | Synthesis |
| --- | --- | --- | --- |
| Routine | 1 fresh reviewer | One per serious candidate | Parent |
| High | 3 fresh reviewers with distinct lenses | One per serious candidate | Parent |

High-risk lenses cover specification/correctness, security/failure behavior,
and operations/concurrency/test evidence. Launch verifiers only for potential
P0/P1 or another predeclared material claim. If no cross-family verifier is
available, a fresh same-family verifier runs and the report discloses the reuse.

Use stable anonymous IDs `R1`, `R2`, `R3`, `V1`, `V2`, `V3`; keep the
alias-to-model mapping as parent audit provenance.

## Finding records

Require each discovery and verifier to end its final message with the report in
exactly one `json` fence, under 12,000 characters. Public delivery wraps that
message in a completion presentation, so the fence is what keeps the report
recoverable. Use the request-local helpers in
[`adversarial-review-example.js`](adversarial-review-example.js) to validate
public subagent results. The helpers are not an extension or runner schema.

A record has `reviewerId`, `status` (`COMPLETE` or `INCOMPLETE`), bounded
`findings`, and bounded `coverageGaps`. Every finding has a stable ID, claimed
P0–P3 severity, nullable confirmed severity, `candidate`/`confirmed`/`rejected`
resolution, `reproduced`/`trace-backed`/`unverified` evidence status, location,
provenance, preconditions, reproduction or trace, expected behavior, actual
behavior, impact, and minimal fix.

A discovery P0/P1 remains an unverified candidate until verifier evidence
confirms or rejects it. A verifier can resolve only supplied IDs, and a
confirmation or rejection needs reproduced or trace-backed evidence. Malformed
reports, public subagent operational failures, coverage gaps, and any child
`INCOMPLETE` propagate `INCOMPLETE`; an unresolved serious candidate is reported
as unverified.

## Parent synthesis

The parent validates every public result, preserves the original delivery for
audit, and builds an identity-minimized projection for synthesis. Preserve
success reports and failure code, retryability, and bounded error evidence; omit
session paths, pane names, and model IDs from the review content. This reduces
bias cues but is not a security boundary.

Reconcile serious candidates with verifier evidence. The final report puts
actionable findings first, then coverage, source provenance, the wave/runtime
matrix, and uncertainties. It explicitly states when no actionable findings
remain. Do not use confidence scores, vote counts, silent retries, or a
mechanical worst-severity rule.
