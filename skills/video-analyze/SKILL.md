---
name: video-analyze
description: Analyze the content of a video — summarize, answer questions about what happens or what's said, extract key points. Trigger when the user gives a URL or a local video file and asks to "summarize", "transcribe", "explain what's in", "extract the key points from", or "what does this video say about X". Different from the `video-export` skill, which only downloads the file. Skip if the user only wants the file or a thumbnail.
---

# video-analyze

Primary tool: **`ponty`** — a CLI built on top of Google's Gemini API by [yanndebray/merleau](https://github.com/yanndebray/merleau). Gemini is the only major LLM with native video input (Claude doesn't take video; GPT-4o requires frame extraction); `ponty` lets you point at a YouTube URL or local file and ask in one command. Use it as the default unless one of the fallback cases below applies.

## Default path — `ponty`

1. **Confirm install.**

   ```bash
   command -v ponty || uv tool install merleau
   ```

   Provides a single executable, `ponty`. Source / issues: https://github.com/yanndebray/merleau

2. **Set the API key** if not already set. The package reads `GOOGLE_API_KEY` via `python-dotenv`, so a `.env` next to the working directory or an exported env var both work.

   ```bash
   export GOOGLE_API_KEY="..."
   ```

3. **Run.**

   ```bash
   # Default prompt: "Explain what happens in this video"
   ponty "https://youtu.be/<id>"

   # Custom prompt + export to markdown
   ponty -p "List every CLI command shown, with the approximate timestamp." \
         -e md \
         "https://youtu.be/<id>"

   # Local file
   ponty -p "Summarize the demo in 5 bullets." \
         /path/to/recording.mp4

   # Switch model (more accurate / more expensive)
   ponty -m gemini-2.5-pro <video>

   # Hide cost output (useful when piping)
   ponty --no-cost <video>
   ```

4. **Read the result.** `ponty` prints the analysis to stdout and shows token + cost info underneath. With `-e md` it also writes a `.md` file next to the video / next to cwd. Pipe to a file or to `claude` if you want post-processing.

## What ponty handles natively

- **YouTube URLs** (the `youtube.com/watch?v=`, `youtu.be/`, and `youtube.com/shorts/` shapes) — Gemini fetches the video itself; you don't need yt-dlp.
- **Local video files** — uploaded to Gemini's file API, processed, then queried.
- **Long videos** — Gemini 2.5 Flash has a 2 M-token context, comfortable up to ~2 hours.
- **Visual content** — because the model sees frames natively, it'll describe what's on screen, not just what's said. Useful for CLI / IDE demos.

## Picking the prompt

`ponty -p "..."`. The prompt drives everything; default is a generic "Explain what happens in this video", which is rarely what you actually want.

| Task | Prompt to use |
|---|---|
| Tutorial / demo summary | `"Summarize what the speaker demonstrates and what they conclude. Note timestamps of key transitions."` |
| Feature extraction (CLI demos) | `"List every command, tool, and flag the speaker types, in order, with approximate timestamps."` |
| Q&A | `"Answer this question using only what the video shows: <question>. If the answer isn't in the video, say so."` |
| Talk → bullet notes | `"You are taking notes for someone who can't attend. 6-8 bullets covering the main claims and any concrete numbers cited."` |
| Determining content type | `"Is this a marketing demo, a tutorial, a conference talk, or a vlog? Cite one timestamp supporting the answer."` |

## Fallback path — yt-dlp + whisper

Use this when:

- No Gemini API key available and the user doesn't want to set one up.
- Cost matters and the video is long (Gemini bills per token; an hour of video is ~$0.10–0.40).
- The user needs a **verbatim transcript with word-level timestamps** for editing or accessibility — `ponty` summarizes rather than transcribes.

```bash
# Audio only — smaller, faster than full video
yt-dlp -f "bestaudio[ext=m4a]/bestaudio" \
       --extract-audio --audio-format m4a \
       -o "%(id)s.%(ext)s" "<URL>"

# Transcribe with faster-whisper (CPU)
uv run --with faster-whisper python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
segs, info = m.transcribe('VIDEO_ID.m4a', vad_filter=True)
with open('transcript.txt', 'w') as f:
    for s in segs: f.write(f'[{s.start:.1f}] {s.text.strip()}\n')
"

# Summarize / Q&A with Claude (or any LLM you have available)
```

For login-walled or YouTube-bot-blocked URLs, add `--cookies-from-browser firefox` to the yt-dlp call.

## Known failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `ponty: error: GOOGLE_API_KEY not set` | env var missing | `export GOOGLE_API_KEY=...` or drop into `.env` |
| `Sign in to confirm you're not a bot` (yt-dlp fallback only) | YouTube bot wall, esp. on cloud IPs | `--cookies-from-browser firefox`; `ponty` itself doesn't hit this because Gemini fetches server-side |
| Video over 2h | Exceeds Gemini's context | Pre-trim with `ffmpeg -i in.mp4 -t 7200 -c copy out.mp4` and analyze the segment most likely to contain the answer |
| Gemini refuses (safety filter) | Triggered on adult / violent content classification | Acknowledge, summarize what you can from metadata + the user's own description |
| Cost surprise | Verbose prompts on long videos = lots of output tokens | Use `gemini-2.5-flash` (default — cheap), keep prompts terse, or pre-segment the video |

## Don'ts

- **Don't reproduce copyrighted creative content verbatim.** If the video is a song, comedy bit, audiobook, movie, or other creative work, refuse a verbatim transcript and offer a summary or brief quotes instead.
- **Don't run face / identity recognition** on the video. If the user asks "who's in this," ask back — that crosses a different line.
- **Don't post the raw output to public hosts** without explicit user permission. The summary is the user's working copy.
- **Don't trust ponty's output for legal or medical fact-finding.** Gemini hallucinates on technical terms and proper nouns at roughly the same rate as Whisper.

## Output template (when summarizing for delivery)

```
**<Inferred title or topic>** — <duration> · <speaker if obvious>

Key points:
- <point 1>
- <point 2>
- <point 3>

Tools / names mentioned: <list>

What the speaker concludes / recommends: <one sentence>

Caveats: <anything the model seemed uncertain about, or that the
video shows visually but the model misread>
```

Trim to taste — short videos get 2-3 bullets, hour-long talks get 6-8.
