#!/usr/bin/env python3
"""Show where Claude Code token spend goes, from local session transcripts.

Cost is reported in input-equivalent units (one uncached input token = 1),
using Anthropic's price ratios: output 5x, cache read 0.1x (0.025x on
claude-fable-5-1), 5-minute cache write 1.25x, 1-hour cache write 2x.
Every cached call re-reads its whole context, so cost follows context size
times the number of calls, not the size of what the agent writes.

Run the same window before and after a change to compare:

    python3 scripts/token-sinks.py --since 2026-09-03 --until 2026-09-17
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUTPUT_RATE = 5.0
UNCACHED_RATE = 1.0
CACHE_READ_RATES = {"claude-fable-5-1": 0.025}
DEFAULT_CACHE_READ_RATE = 0.1
WRITE_5M_RATE = 1.25
WRITE_1H_RATE = 2.0
PARTS = ("cache read", "cache write", "uncached input", "output")
CONTEXT_BUCKETS = ("<=200k", "200-400k", ">400k")


@dataclass
class Call:
    at: datetime
    context: int
    tools: int
    cost: dict[str, float]


@dataclass
class Session:
    project: str
    name: str
    subagent: bool
    calls: list[Call]
    compactions: int

    def total(self) -> float:
        return sum(sum(c.cost.values()) for c in self.calls)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def price(model: str, usage: dict) -> dict[str, float]:
    written = usage.get("cache_creation_input_tokens", 0)
    by_ttl = usage.get("cache_creation") or {}
    written_1h = by_ttl.get("ephemeral_1h_input_tokens", 0)
    read_rate = CACHE_READ_RATES.get(model, DEFAULT_CACHE_READ_RATE)
    return {
        "cache read": usage.get("cache_read_input_tokens", 0) * read_rate,
        "cache write": (written - written_1h) * WRITE_5M_RATE + written_1h * WRITE_1H_RATE,
        "uncached input": usage.get("input_tokens", 0) * UNCACHED_RATE,
        "output": usage.get("output_tokens", 0) * OUTPUT_RATE,
    }


def read_session(path: Path, root: Path) -> tuple[Session, list[datetime]]:
    """Collapse streamed transcript lines into one Call per API message id."""
    usage: dict[str, tuple[str, str, dict]] = {}
    tool_ids: defaultdict[str, set[str]] = defaultdict(set)
    compactions: list[datetime] = []
    with path.open(encoding="utf-8", errors="replace") as lines:
        for line in lines:
            if '"assistant"' not in line and '"compact_boundary"' not in line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("subtype") == "compact_boundary":
                compactions.append(parse_time(entry["timestamp"]))
                continue
            message = entry.get("message") or {}
            if entry.get("type") != "assistant" or not message.get("usage"):
                continue
            if message.get("model") == "<synthetic>":
                continue
            first_seen = usage[message["id"]][1] if message["id"] in usage else entry["timestamp"]
            usage[message["id"]] = (message.get("model", ""), first_seen, message["usage"])
            for block in message.get("content") or []:
                if block.get("type") == "tool_use":
                    tool_ids[message["id"]].add(block["id"])
    calls = [
        Call(
            at=parse_time(at),
            context=u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0),
            tools=len(tool_ids[mid]),
            cost=price(model, u),
        )
        for mid, (model, at, u) in usage.items()
    ]
    calls.sort(key=lambda c: c.at)
    relative = path.relative_to(root)
    return Session(relative.parts[0], str(relative), "subagents" in relative.parts, calls, 0), compactions


def bucket(context: int) -> str:
    if context <= 200_000:
        return "<=200k"
    return "200-400k" if context <= 400_000 else ">400k"


def share(part: float, whole: float) -> str:
    return f"{part / whole:6.1%}" if whole else "   n/a"


def report(root: Path, since: datetime, until: datetime, top: int) -> str:
    sessions: list[Session] = []
    first_contexts: dict[bool, list[int]] = {False: [], True: []}
    compactions = 0
    for path in root.rglob("*.jsonl"):
        if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < since:
            continue
        session, compacted_at = read_session(path, root)
        if session.calls and since <= session.calls[0].at < until:
            first_contexts[session.subagent].append(session.calls[0].context)
        session.calls = [c for c in session.calls if since <= c.at < until]
        session.compactions = sum(since <= at < until for at in compacted_at)
        compactions += session.compactions
        if session.calls:
            sessions.append(session)

    parts: Counter[str] = Counter()
    buckets: Counter[str] = Counter()
    projects: Counter[str] = Counter()
    tool_calls = single_tool_calls = 0
    subagent_cost = 0.0
    for session in sessions:
        cost = session.total()
        projects[session.project] += cost
        subagent_cost += cost if session.subagent else 0.0
        for call in session.calls:
            parts.update(call.cost)
            buckets[bucket(call.context)] += sum(call.cost.values())
            tool_calls += call.tools > 0
            single_tool_calls += call.tools == 1
    total = sum(parts.values())
    ranked = sorted(sessions, key=Session.total, reverse=True)
    top_decile = sum(s.total() for s in ranked[: max(1, len(ranked) // 10)])
    main_count = sum(not s.subagent for s in sessions)

    def median(values: list[int]) -> str:
        return f"{int(statistics.median(values)):,}" if values else "n/a"

    out = [
        f"Window: {since:%Y-%m-%d} .. {until:%Y-%m-%d} (UTC, end exclusive)",
        f"Sessions: main={main_count} subagent={len(sessions) - main_count}"
        f"  API calls: {sum(len(s.calls) for s in sessions):,}  compactions: {compactions}",
        "Cost unit: one uncached input token = 1.",
        "",
        "Cost composition",
        *(f"  {name:<16}{share(parts[name], total)}" for name in PARTS),
        "",
        "Cost by context size at call",
        *(f"  {name:<16}{share(buckets[name], total)}" for name in CONTEXT_BUCKETS),
        "",
        f"Tool-using calls with exactly one tool  {share(single_tool_calls, tool_calls)}",
        f"Subagent share of cost                 {share(subagent_cost, total)}",
        f"Top 10% of sessions share of cost      {share(top_decile, total)}",
        f"Median first-call context              main={median(first_contexts[False])} subagent={median(first_contexts[True])}",
        "",
        f"Cost by project (top {top})",
        *(f"  {share(cost, total)}  {name}" for name, cost in projects.most_common(top)),
        "",
        f"Most expensive sessions (top {top})",
        *(
            f"  {share(s.total(), total)}  calls={len(s.calls)} max context={max(c.context for c in s.calls) // 1000:,}k"
            f" compactions={s.compactions}  {s.name}"
            for s in ranked[:top]
        ),
    ]
    return "\n".join(out)


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path.home() / ".claude" / "projects", help="transcript root")
    parser.add_argument("--since", type=parse_date, help="first UTC day included, YYYY-MM-DD (default: 14 days ago)")
    parser.add_argument("--until", type=parse_date, help="first UTC day excluded, YYYY-MM-DD (default: now)")
    parser.add_argument("--top", type=int, default=10, help="rows in the project and session rankings")
    args = parser.parse_args()
    until = args.until or datetime.now(timezone.utc)
    since = args.since or until - timedelta(days=14)
    if since >= until:
        raise ValueError(f"--since {since:%Y-%m-%d} must be before --until {until:%Y-%m-%d}")
    print(report(args.root, since, until, args.top))


if __name__ == "__main__":
    main()
