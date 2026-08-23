# Debugging branch

Use this branch when the requested source change fixes broken, failing, slow, or
intermittent behavior.

## Before specification

1. Build one tight, agent-runnable feedback loop that asserts the user's exact
   symptom. Prefer a failing test, request script, CLI fixture, browser check,
   replay, harness, fuzz loop, bisection, or differential comparison.
2. Run it and confirm it can go red on the reported bug. For flaky behavior,
   raise and measure the reproduction rate.
3. Minimize the reproduction until every remaining element is load-bearing.

If no red-capable loop can be built, report what is missing and request the
narrow evidence or access needed. Do not theorize from code alone.

## Design and implementation

1. Generate three to five falsifiable hypotheses with predicted observations.
2. Test them one variable at a time. Prefer debugger inspection, then targeted
   logs tagged with a unique `[DEBUG-xxxx]` prefix. Measure performance before
   changing performance code.
3. State the supported root cause and smallest fix. If the cause is architectural,
   return to the design phase.
4. Turn the minimized reproduction into a regression test at the public seam,
   then make the smallest change that turns it green.

## Verification

- Re-run the original feedback loop and regression test.
- Run the affected suite.
- Remove every tagged debug probe and throwaway artifact.
- If three fix attempts fail against the same red loop, revisit the hypotheses or
  architecture before another attempt.
