# Human final check for appropriateness

Use this branch only when an objectively working result still needs a person's
judgment about whether it is suitable for its users or context. Examples include
perceived clarity, visual hierarchy, usefulness, workflow fit, tone, and domain
appropriateness. It is not a correctness oracle.

## Prepare the checkpoint

The agent first exercises the strongest available correctness interfaces. Use the
actual user-facing surface when practical: Chrome or browser automation for web
behavior, computer use for native interfaces, and CLI, API, runtime, or
operational evidence where those are the real seams. Report unresolved
correctness gaps as implementation gaps instead of handing them to the reviewer.

Agree with the user on:

- scenario, actor, starting state, data, device, and environment
- what the agent will prepare and which correctness evidence it will capture
- the exact suitability question the reviewer must answer
- pass, revise, and stop outcomes
- how the verdict returns to `design.md` and `verification.md`

Default to one final check. Use an iterative human-in-the-loop only when the user
chooses to shape the experience through repeated feedback during Requirements or
Design.

## Execute and close

The agent prepares the scenario, completes objective checks, and presents the
evidence with the suitability question. Record the environment, verdict,
feedback, and resulting design or implementation change. A revision re-enters
the agent-owned correctness loop before another suitability check.

If the user declines the check, record the appropriateness criterion as out of
scope or unresolved according to the user's decision. This does not waive any
correctness evidence required for the programming change.
