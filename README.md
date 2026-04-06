# weihung-user-claude

Personal global Claude Code agent system.
Applies to all projects via `~/.claude/`.

## Structure

```
CLAUDE.md                          # Constitution (~40 lines, always loaded)
rules/
  clean-architecture.md            # Architecture quality gates (always loaded)
  go.md                            # Go rules (*.go)
  typescript.md                    # TypeScript rules (*.ts, *.tsx)
  python.md                        # Python rules (*.py)
  shell.md                         # Shell rules (*.sh)
  markdown.md                      # Markdown rules (*.md)
  deployment.md                    # Deploy safety (always loaded)
  chinese-writing.md               # Chinese output quality (always loaded)
agents/
  silent-failure-hunter.md         # Hunt silent failures, swallowed errors, dangerous fallbacks
  security-reviewer.md             # OWASP Top 10 + dangerous pattern detection
skills/
  leveraging-tasks/                # Dev task router: classify → gate → delegate
  providing-knowledge/             # Question answering: mental model first
  investigating/                   # Research: comprehensive, traceable
  inspecting/                      # Audit: plan → investigate per item
  reflecting-to-root/              # Session reflection → user/project routing
```

## Routing

CLAUDE.md contains the routing table.
Before responding, classify the request:

1. **External skill applies** (superpowers, rcc, openspec, ttt, etc.) → use that skill directly
2. **Development task** (implement, design, debug, deploy) → `leveraging-tasks`
3. **Question** (explain, what is, how does) → `providing-knowledge`
4. **Investigation** (research, find out, current state of) → `investigating`
5. **Inspection** (check, audit, verify, review) → `inspecting`

## Skills

### leveraging-tasks

Thin router for development tasks.
Four pipes (implement, design, debug, deploy) with cross-cutting refactor awareness.

- Quality awareness is continuous, not just an entry gate
- Refactor is not a separate pipe — it's a reflex embedded in all pipes
- Feedback loops: implement discovers new context → back to design; debug finds architectural root cause → refactor first

### providing-knowledge

Answers questions by building mental models.
Clear, no flattery, honest about uncertainty.

### investigating

Conducts research with traceable evidence.
Every claim linked to a source.
Distinguishes confirmed facts from inferences.

### inspecting

Builds a comprehensive check plan, then verifies each item using `investigating`.
Plan first, check second.
User controls scope.

### reflecting-to-root

Post-session reflection that routes learnings to the correct scope.

- Cross-project patterns → `~/.claude/CLAUDE.md` or `~/.claude/rules/`
- Project-specific patterns → `.claude/CLAUDE.md` or `.claude/rules/`
- Delegates to `rcc:reflecting` for project-level integration when available

## Design Principles

- **CLAUDE.md = constitution**: universal laws, every word counts
- **rules/ = scoped laws**: loaded by file glob, saves context window
- **skills = leverage**: few powerful process skills that multiply project-level skills
- **settings.local.json**: sensitive data (accounts, IPs) — not tracked

## Model Routing

| Role | Model |
|------|-------|
| Router / orchestration | opus (session default) |
| implement / deploy / refactor | sonnet |
| design / debug | opus |
| question / investigation / inspection | sonnet |
| search / summary / formatting | haiku |

## Not Tracked

- `settings.json` / `settings.local.json` (credentials, paths)
- `plugins/` (managed separately)
- `todos/`, `projects/`, `statsig/` (auto-generated)
- Existing user skills (`agent-browser/`, `find-skills`)
