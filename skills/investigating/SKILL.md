---
name: investigating
description: Use when the user asks to research or investigate a question, claim, or topic in depth. Comprehensive investigation with current information, every claim traceable to a source.
model: sonnet
---

# Investigating

Investigate thoroughly. Every claim must be traceable to a source.

## Investigation Flow

1. **Scope.** What exactly are we investigating? Restate in one sentence.
2. **Gather.** Collect evidence from all relevant sources:
   - Code: codebase-memory-mcp graph tools FIRST (`search_graph` to find symbols, `trace_path` for call chains, `get_code_snippet` for source, `get_architecture` for structure; run `index_repository` if the project is not indexed) — fall back to grep/read for text, configs, and non-code files; check git history
   - External: web search, documentation, API references
   - Runtime: logs, error messages, test output
3. **Verify.** Cross-check findings. If two sources conflict, investigate the conflict.
4. **Synthesize.** Connect findings into a coherent picture. Identify what is confirmed, what is likely, and what is unknown.
5. **Report.** Present findings structured as:

```
## Findings

### Confirmed
[Evidence-backed conclusions]

### Likely (needs verification)
[Reasonable inferences with stated assumptions]

### Unknown
[What we could not determine and why]

### Sources
[Where each finding came from]
```

## Scout Pattern (Optional, for Unfamiliar Territory)

When the question is in code or systems you have not touched, send a scout agent before doing the real investigation.

**How:**

1. Launch one Agent (`Explore` or `general-purpose`) with a deliberately loose prompt — "explore X, report what you found, what's confusing, where you'd dig next."
   Subagents do NOT receive the session code-discovery reminder, so the prompt MUST include: "Use codebase-memory-mcp tools first (`search_graph`, `trace_path`, `get_code_snippet`, `search_code`) before grep/file-read."
2. **Discard the scout's conclusions.** They are not the answer.
3. Read the scout's findings for: which files matter, which terms appear, where the dead ends are.
4. Use that intel to write a precise prompt for the real investigation (Step 1 below).

**Why this beats jumping straight in:** the scout pays the discovery cost in parallel with whatever else you're doing, and the precise prompt that follows hits its target on the first try instead of meandering.

**Skip the scout when:** the territory is familiar, the question is narrow (one file, one symbol), or the answer is in obvious places (`git log`, a known doc).

## Principles

- **Comprehensive over fast.** Check all relevant sources before concluding.
- **Logic chain visible.** Show how you got from evidence to conclusion.
- **Current information.** Use web search and documentation tools to verify — do not rely solely on training data.
- **Insufficient evidence is itself a finding.** Report it as "insufficient evidence", never dressed up as "probably X".
- **Distinguish fact from inference.** Label which is which.
