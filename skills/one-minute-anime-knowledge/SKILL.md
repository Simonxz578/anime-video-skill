---
name: one-minute-anime-knowledge
description: Create blue-white anime knowledge shorts or original two-minute Japanese-dialogue romance motion films with fixed character references, Chinese subtitles, and 1080p 30fps delivery. Use for physics/history shorts and continuing romance chapters; verify all media before claiming a finished video.
---

# Anime knowledge video and romance chapters

Repository: `Simonxz578/anime-video-skill`. Keep the existing skill directory name for installation compatibility.

## Video format — required

- **1080p, 30 fps constant frame rate.** Default portrait delivery: **1080 × 1920**, 9:16. If the user requests landscape: **1920 × 1080**, 16:9.
- MP4, H.264, `yuv420p`, AAC stereo at 48 kHz, `faststart`.
- Knowledge: target 60 seconds. Romance: target **120 seconds / 3600 frames**.
- Verify the encoded file with `ffprobe`; container labels and timeline settings alone are insufficient. Never stretch a shorter incomplete sequence to satisfy duration.
- Deliver a subtitled version, a clean version, the timed subtitle file, and technical QA. Clearly describe illustration/camera/rain animation as a motion-illustration film; do not claim lip sync or full character animation when absent.

Use this repository's `anime-video` CLI or `anime-video-mcp` tools for requests like “做一分钟黑洞科普”, “一分钟理解安史之乱”, “Cambridge 为什么是学院制大学”, or “继续言情短剧下一章，日语对白中文字幕”. Keep the female and male reference images in `references/` as immutable identity masters.

## Route the request

- Knowledge: identify the series and topic. Use `create_episode` or `anime-video episode`. For a topic without a curated source pack, obtain and verify authoritative sources, then supply a pack in the documented schema. Never invent citations or turn draft notes into fact-checked final claims.
- Romance: run `create_romance_series` once, then `create_romance_chapter` in order. Read `continuity/state.json` and `used_content_index.json` before a new chapter. Japanese dialogue is the source for Chinese subtitles; preserve `line_id` and seek bilingual review for meaning.

## Release gates

The `anime-video` CLI and MCP planning tools still return `planning_only`; their media provider placeholders must not be mistaken for finished video. An actual local motion-film compositor is now available separately at `scripts/render_motion_film.py`. It consumes an authored manifest and prepared character-reference-conditioned artwork. It does not generate artwork or provide a general text-to-video adapter.

## Produce a romance motion film

1. Read the user's chapter brief, series bible, continuity and used-content index. For a new series establish adult characters, names, relationship state, original plot and 3–6 note motif. Reuse identity masters, never prior-chapter footage.
2. Author a complete 120-second Japanese dialogue source with faithful Chinese translations, line IDs, quiet beats and camera cuts. Review names, negation, numbers, speaker intent and reading time. See `examples/rain/ch001.json` for a complete authored chapter.
3. Use the available image generation tool with both supplied character references and an approved location reference. Generate new shot artwork; inspect face, hair, eyes, costume, skin, female black socks and male weapon absence. Put the approved images in `<chapter>/assets/` with the filenames in the manifest.
4. Generate fixed voices. The local fallback uses macOS `say` (Kyoko and Eddy Japanese), with explicit character-name pronunciation; check every file for nonzero duration. Do not silently replace a configured series voice. Record provider and voice IDs. Local TTS remains synthetic and should not be described as actor performance.
5. Run the compositor's `--phase audio`, inspect the actual line durations, and resolve any overlap. It synthesizes an original five-note piano/pad score, rain and distant train ambience, ducks music during dialogue, and writes the mix plus SRT.
6. Render `--phase preview` and inspect a frame. Then `--phase render` produces a subtitled film and a clean film with camera moves and independently animated rain. Use `--phase qa` for frame count, 1080p/30fps, codec, duration, decode checks and contact sheet.
7. Inspect the contact sheet and subtitle meaning. Record subjective checks as agent-reviewed or pending human review, never manufacture scores or listening approval. Copy the verified film to the series `videos/` directory and update continuity/content fingerprints only after successful rendering.

Example (macOS, Python with NumPy/Pillow/OpenCV; FFmpeg installed):

```bash
python scripts/render_motion_film.py --manifest examples/rain/ch001.json \
  --project outputs/romance/rain/chapters/ch001 --phase all
```

See [local rendering instructions](../../docs/motion-film.md) for dependencies, inputs and limits. For knowledge releases also require verified research. Do not substitute unrelated stock imagery, fabricate a passing QA report or claim a nonexistent file. If a required capability is missing, complete independent work and identify the specific missing capability.

For implementation details and commands, read [README_zh-CN.md](../../README_zh-CN.md).
