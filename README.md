# skills

Reusable [Claude Code](https://claude.com/claude-code) and Claude Desktop skills.

A skill is a markdown file (`SKILL.md`) with YAML frontmatter that Claude invokes when its `description` matches what the user is asking for. Drop these into `~/.claude/skills/` (user-wide) or `<repo>/.claude/skills/` (project-scoped) to make them available.

## Skills in this repo

| Skill | What it does |
| --- | --- |
| [`compress-video`](skills/compress-video/SKILL.md) | Reduce video file size with ffmpeg (H.264). Use when asked to shrink, compress, or make a video smaller. |
| [`python-artifact`](skills/python-artifact/SKILL.md) | Build browser-based Python artifacts with Pyodide (CPython on WebAssembly) — REPLs, playgrounds, and numpy/pandas/scikit-learn/matplotlib demos that run client-side, no server. |
| [`video-export`](skills/video-export/SKILL.md) | Download a video from a public web URL (YouTube, LinkedIn, X, TikTok, …) via yt-dlp and hand the file back. |
| [`video-analyze`](skills/video-analyze/SKILL.md) | Summarize / Q&A a web or local video. Default path uses [`ponty`](https://github.com/yanndebray/merleau) (Gemini-native video understanding); falls back to yt-dlp + whisper for verbatim transcripts. |
| [`usage-report`](skills/usage-report/SKILL.md) | Generate a Claude Code token-usage and cost report from local session logs (`~/.claude/projects/*/*.jsonl`). Writes a markdown dashboard to `/tmp/`. (Named `usage-report` to avoid clashing with Claude Code's built-in `/usage`.) |

## Credits

`video-export`, `video-analyze`, and `usage-report` are contributed by [**jean-clawd**](https://github.com/jeanclawd/skills). Thanks!

## Install

Single skill:

```bash
mkdir -p ~/.claude/skills
cp -r skills/video-export ~/.claude/skills/
```

All skills:

```bash
git clone https://github.com/yanndebray/skills.git ~/.claude/skills-repo
ln -s ~/.claude/skills-repo/skills/video-export ~/.claude/skills/video-export
# repeat per skill, or symlink each directory under skills/ you want
```

After installing, restart Claude Code (or run `/skill-list`) to pick up the new skill.

## Skill format

Each skill lives in its own directory under `skills/` with a `SKILL.md` file:

```
skills/my-skill/
└── SKILL.md
```

`SKILL.md` starts with frontmatter:

```markdown
---
name: my-skill
description: One- or two-sentence description that tells Claude when to invoke this skill. Be specific about triggers.
---

# my-skill

Body — instructions Claude follows when the skill fires.
```

The `description` is the trigger. Make it specific (what phrases, what URLs, what file types) and explicit about when **not** to use the skill.
