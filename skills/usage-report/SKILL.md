---
name: usage-report
description: Generate a Claude Code token-usage and cost report from local session logs (~/.claude/projects/*/*.jsonl). Produces a markdown report and optionally sends it to the user via a configured channel (e.g. Telegram). Use when the user invokes /usage-report (or /usage_report) or asks for "usage", "cost", "tokens", "how much have I spent on Claude Code". Named usage-report (not usage) to avoid clashing with Claude Code's built-in /usage command.
---

# usage-report skill

Produce a Claude Code usage/cost report from local session logs and deliver it to the user.

## Steps

1. **Run the script**: `python3 ~/.claude/skills/usage-report/usage.py`
   - It walks `~/.claude/projects/*/*.jsonl`, aggregates per session, estimates cost using standard Anthropic pricing.
   - On success, prints the absolute path of the generated markdown file to stdout (e.g. `/tmp/claude-usage-20260516-203145.md`).
   - On failure (no sessions found), exits non-zero with a message to stderr.

2. **Capture the path** from stdout — that's the report file.

3. **Deliver the report.** If a messaging channel is configured (e.g. Telegram via the `mcp__plugin_telegram_telegram__reply` tool), send the markdown file as an attachment with a one-line caption stating the grand-total cost (parse it from the report). The user's chat_id should come from session context (e.g. the inbound message's `chat_id`, or an env var like `TELEGRAM_CHAT_ID`) — do not hard-code it in the skill. If no channel is configured, just summarize the totals in the terminal.

4. **In the terminal**, respond in one sentence: cost total + sessions count. Don't dump the per-session table — the markdown file is the dashboard.

## Notes

- Pricing assumes standard Anthropic public rates. The 1M-context model variant may add a surcharge on prompts > 200k tokens — flag this only if the user asks.
- Cache reads typically dominate volume but are cheap (~10% of input rate); don't be alarmed by the large numbers.
- If the script errors, surface the error — do not silently fall back to a hand summary.
