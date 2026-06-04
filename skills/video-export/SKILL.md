---
name: video-export
description: Download/export a video from a public web URL using yt-dlp. Trigger when the user asks to "download", "export", "save", or "grab" a video and gives a URL — YouTube, LinkedIn, Twitter/X, TikTok, Vimeo, Instagram, Facebook, Reddit, or any of the ~1000 sites yt-dlp supports. Skip for plain audio podcasts (use a podcast client) or for screenshots/static images.
---

# video-export

Wraps yt-dlp to pull video files off public web pages. Hand the resulting file path back to the user; do not transcribe, summarize, or reproduce the video's spoken/written content unless the user explicitly asks for that.

## Steps

1. **Make sure yt-dlp is installed.**

   ```bash
   command -v yt-dlp >/dev/null || uv tool install yt-dlp
   ```

   If `uv` isn't available, fall back to `pipx install yt-dlp` or `pip install --user yt-dlp`.

2. **List available formats.** This catches sites with weird codecs or only-audio streams before committing to a download.

   ```bash
   yt-dlp -F "<URL>"
   ```

3. **Download.** For most sites the default merged-best selector works:

   ```bash
   mkdir -p /tmp/video-export
   yt-dlp -f "bv*+ba/b" -o "/tmp/video-export/%(id)s.%(ext)s" "<URL>"
   ```

   For LinkedIn specifically, formats are often labelled with bare numeric IDs (`0`, `1`, …) and there is no separate audio track — pick the highest-bitrate ID from step 2:

   ```bash
   yt-dlp -f 1 -o "/tmp/video-export/%(id)s.%(ext)s" "<URL>"
   ```

4. **Report the path** back to the user. If the channel supports file attachments (Telegram, Slack, Discord), attach the file directly — most chat platforms cap at 50 MB; check size first with `ls -lh`.

## Authentication for private / login-walled content

If the URL requires being logged in (private LinkedIn post, age-gated YouTube, X protected account, etc.), reuse the user's browser session:

```bash
yt-dlp --cookies-from-browser firefox -f "..." -o "..." "<URL>"
```

Swap `firefox` for whichever browser they're logged in on: `chrome`, `chromium`, `brave`, `edge`, `safari`, `opera`, `vivaldi`.

If `--cookies-from-browser` fails (e.g. non-interactive environment, locked keychain), ask the user to export cookies to a file with a browser extension like *Get cookies.txt LOCALLY* and pass `--cookies cookies.txt`.

## Common failures and fixes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ERROR: Unable to extract` on a fresh URL | yt-dlp extractor outdated | `uv tool upgrade yt-dlp` (or `--update`) |
| `HTTP Error 403` | Login required or geo-block | Try `--cookies-from-browser`; check the user can view the post in their browser |
| `Requested format is not available` | Site only offers HLS/DASH manifests | Drop the `-f` flag and let yt-dlp pick |
| Audio missing on download | Some platforms ship video and audio as separate streams; merge with ffmpeg | `apt install ffmpeg` (or `brew install ffmpeg`) and rerun |
| File too big for chat platform | Bitrate too high | Re-encode: `ffmpeg -i in.mp4 -c:v libx264 -crf 28 -preset fast out.mp4` |

## Output filename templates

yt-dlp's `-o` accepts placeholders. Useful ones:

- `%(id)s` — opaque platform ID (safe, no spaces/unicode)
- `%(title)s` — human title (may contain spaces, slashes — sanitize if scripting)
- `%(uploader)s` — channel/account name
- `%(upload_date)s` — `YYYYMMDD`
- `%(ext)s` — file extension chosen by yt-dlp

Default to `%(id)s.%(ext)s` when the file is just being shipped to chat. Use `%(uploader)s - %(title)s.%(ext)s` when archiving locally.

## Don'ts

- **Don't transcribe** the video, summarize its narration, or reproduce its on-screen text/lyrics in your reply unless the user explicitly asks for a transcript or summary. They asked you to fetch the file, not to consume its content for them.
- **Don't push** the downloaded file to any remote service (cloud storage, public URL, Drive, S3) unless the user asks you to.
- **Don't bypass paywalls or DRM.** yt-dlp refuses DRM by design; don't try to work around it. If the user is asking to circumvent a paywall they don't have access to, decline.
- **Don't keep the file** after delivering it if disk is tight. `/tmp/` self-cleans, but if you wrote to `/root` or similar, ask before leaving large files behind.
