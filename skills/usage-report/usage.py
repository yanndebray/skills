#!/usr/bin/env python3
"""Generate a Claude Code usage report from local session logs.

Reads ~/.claude/projects/**/*.jsonl, aggregates token usage per session,
estimates cost at standard Anthropic pricing, and writes a markdown report
to /tmp/claude-usage-<timestamp>.md. Prints the output path on success.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

# Standard public Anthropic pricing per million tokens.
# Note: the 1M-context tier on Opus/Sonnet 4.x may apply a ~2x surcharge to
# requests with prompts > 200k tokens — not modeled here.
PRICING = {
    "claude-opus-4-8":   {"in": 15.00, "out": 75.00, "cache_w": 18.75, "cache_r": 1.50},
    "claude-opus-4-7":   {"in": 15.00, "out": 75.00, "cache_w": 18.75, "cache_r": 1.50},
    "claude-opus-4-6":   {"in": 15.00, "out": 75.00, "cache_w": 18.75, "cache_r": 1.50},
    "claude-sonnet-4-6": {"in":  3.00, "out": 15.00, "cache_w":  3.75, "cache_r": 0.30},
    "claude-sonnet-4-5": {"in":  3.00, "out": 15.00, "cache_w":  3.75, "cache_r": 0.30},
    "claude-haiku-4-5":  {"in":  1.00, "out":  5.00, "cache_w":  1.25, "cache_r": 0.10},
}
# Default to the newest Opus when a session's model is unknown/unlisted.
FALLBACK_PRICE = PRICING["claude-opus-4-8"]


def price_for(model: str | None) -> dict[str, float]:
    if not model:
        return FALLBACK_PRICE
    # Strip 1M-context suffixes like "[1m]" if present.
    base = model.split("[")[0].strip()
    return PRICING.get(base, FALLBACK_PRICE)


def estimate_cost(model: str | None, u: dict) -> float:
    p = price_for(model)
    return (
        u["input_tokens"]                    * p["in"]      / 1_000_000
        + u["output_tokens"]                 * p["out"]     / 1_000_000
        + u["cache_creation_input_tokens"]   * p["cache_w"] / 1_000_000
        + u["cache_read_input_tokens"]       * p["cache_r"] / 1_000_000
    )


def aggregate() -> dict[str, dict]:
    paths = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
    sessions: dict[str, dict] = defaultdict(lambda: {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "turns": 0,
        "first_ts": None,
        "last_ts": None,
        "model": None,
        "project": None,
    })

    for path in paths:
        project = os.path.basename(os.path.dirname(path))
        sid_from_file = os.path.basename(path).replace(".jsonl", "")
        with open(path) as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") != "assistant":
                    continue
                usage = (rec.get("message") or {}).get("usage") or {}
                if not usage:
                    continue
                sid = rec.get("sessionId") or sid_from_file
                s = sessions[sid]
                s["project"] = project
                for k in (
                    "input_tokens",
                    "output_tokens",
                    "cache_creation_input_tokens",
                    "cache_read_input_tokens",
                ):
                    v = usage.get(k) or 0
                    if isinstance(v, int):
                        s[k] += v
                s["turns"] += 1
                ts = rec.get("timestamp")
                if ts:
                    if s["first_ts"] is None or ts < s["first_ts"]:
                        s["first_ts"] = ts
                    if s["last_ts"] is None or ts > s["last_ts"]:
                        s["last_ts"] = ts
                model = (rec.get("message") or {}).get("model")
                if model:
                    s["model"] = model
    return sessions


def fmt(n: int) -> str:
    return f"{n:,}"


def render(sessions: dict[str, dict]) -> tuple[str, dict]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    totals = defaultdict(int)
    total_cost = 0.0
    per_model_cost: dict[str, float] = defaultdict(float)
    per_project_cost: dict[str, float] = defaultdict(float)
    for s in sessions.values():
        for k in (
            "turns",
            "input_tokens",
            "output_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
        ):
            totals[k] += s[k]
        c = estimate_cost(s["model"], s)
        total_cost += c
        per_model_cost[s["model"] or "?"] += c
        per_project_cost[s["project"] or "?"] += c

    lines = [
        "# Claude Code usage report",
        "",
        f"Generated {now}. Source: `~/.claude/projects/*/*.jsonl`. "
        "Cost estimates use standard Anthropic pricing per model "
        "(1M-context tier surcharges on prompts > 200k tokens are not modeled).",
        "",
        "## Totals",
        "",
        f"- Sessions: **{len(sessions)}**",
        f"- Assistant turns: **{fmt(totals['turns'])}**",
        f"- Input tokens: **{fmt(totals['input_tokens'])}**",
        f"- Output tokens: **{fmt(totals['output_tokens'])}**",
        f"- Cache writes: **{fmt(totals['cache_creation_input_tokens'])}**",
        f"- Cache reads: **{fmt(totals['cache_read_input_tokens'])}**",
        f"- **Estimated cost: ${total_cost:,.2f}**",
        "",
        "## By model",
        "",
        "| Model | Cost |",
        "|---|---:|",
    ]
    for model, c in sorted(per_model_cost.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {model} | ${c:,.2f} |")

    lines += [
        "",
        "## By project (workspace)",
        "",
        "| Project | Cost |",
        "|---|---:|",
    ]
    for proj, c in sorted(per_project_cost.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {proj} | ${c:,.2f} |")

    lines += [
        "",
        "## Per session",
        "",
        "| Last activity | Project | Session | Model | Turns | Input | Output | Cache W | Cache R | Cost |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for sid, s in sorted(sessions.items(), key=lambda kv: kv[1]["last_ts"] or "", reverse=True):
        cost = estimate_cost(s["model"], s)
        ts = (s["last_ts"] or "")[:19].replace("T", " ")
        lines.append(
            f"| {ts} | {s['project']} | `{sid[:8]}` | {s['model'] or '?'} | "
            f"{s['turns']} | {fmt(s['input_tokens'])} | {fmt(s['output_tokens'])} | "
            f"{fmt(s['cache_creation_input_tokens'])} | {fmt(s['cache_read_input_tokens'])} | "
            f"${cost:,.2f} |"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- Cache reads typically dominate by volume but cost ~10% of input rate.",
        "- The 1M-context variant may add a surcharge on prompts > 200k tokens — not reflected.",
        "- Tool-result tokens (web fetches, large file reads) inflate cache writes.",
    ]

    summary = {
        "total_cost": total_cost,
        "total_sessions": len(sessions),
        "totals": dict(totals),
    }
    return "\n".join(lines) + "\n", summary


def main() -> int:
    sessions = aggregate()
    if not sessions:
        print("No sessions found under ~/.claude/projects/*/*.jsonl", file=sys.stderr)
        return 1
    md, _ = render(sessions)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = f"/tmp/claude-usage-{stamp}.md"
    with open(out_path, "w") as fh:
        fh.write(md)
    print(out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
