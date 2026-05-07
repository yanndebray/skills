---
name: compress-video
description: >
  Reduce video file size using ffmpeg with H.264 encoding. Use when the user
  asks to compress a video, shrink a video file, reduce video size, or make
  a video smaller. Requires ffmpeg in PATH.
---

# Compress Video Skill

Reduce video file size using ffmpeg with H.264 encoding.

## When to use

Use when the user asks to compress a video, reduce video size, shrink a video file, or make a video smaller.

## Prerequisites

- ffmpeg installed and available in PATH

## Usage

```bash
ffmpeg -i input.mp4 -vcodec libx264 -crf 28 -preset slow output.mp4
```

## Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `-vcodec` | `libx264` | H.264 video codec |
| `-crf` | `28` | Constant Rate Factor (0-51). Higher = smaller file, lower quality. Default 23, 28 gives good compression with acceptable quality |
| `-preset` | `slow` | Encoding speed preset. Slower = better compression. Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow |

## Workflow

1. Ask the user for the input video file path (or use the file they provide)
2. Suggest an output filename (e.g., `input_compressed.mp4`)
3. Run the ffmpeg command
4. Report the before/after file sizes

## Customization

- For higher quality: lower the CRF value (e.g., `-crf 23`)
- For smaller files: raise the CRF value (e.g., `-crf 32`)
- For faster encoding: use `-preset medium` or `-preset fast`
- To also reduce resolution: add `-vf scale=1280:720` (or similar)
- To keep audio unchanged: add `-acodec copy`
