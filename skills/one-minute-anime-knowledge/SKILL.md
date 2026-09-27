---
name: one-minute-anime-knowledge
description: Plan cited, blue-white anime knowledge shorts or original Japanese-dialogue romance chapters using the fixed character references. Use for one-minute physics/history video requests or two-minute continuing romance chapters; media release is gated until providers and QA are complete.
---

# Anime knowledge video and romance chapters

Use this repository's `anime-video` CLI or `anime-video-mcp` tools for requests like “做一分钟黑洞科普”, “一分钟理解安史之乱”, “Cambridge 为什么是学院制大学”, or “继续言情短剧下一章，日语对白中文字幕”. Keep the female and male reference images in `references/` as immutable identity masters.

## Route the request

- Knowledge: identify the series and topic. Use `create_episode` or `anime-video episode`. For a topic without a curated source pack, obtain and verify authoritative sources, then supply a pack in the documented schema. Never invent citations or turn draft notes into fact-checked final claims.
- Romance: run `create_romance_series` once, then `create_romance_chapter` in order. Read `continuity/state.json` and `used_content_index.json` before a new chapter. Japanese dialogue is the source for Chinese subtitles; preserve `line_id` and seek bilingual review for meaning.

## Release gates

The current implementation creates an offline planning pack. It does **not** create video, voice, music, or a passing final QA report. Report `planning_only` accurately. For an actual release, require verified research, reference-locked visuals, fixed licensed voices, original or licensed music, 1080×1920/30 fps H.264/AAC rendering, contact sheet and ffprobe QA. If a gate is unavailable, stop and name the missing capability once. Do not substitute unrelated stock imagery or claim a nonexistent `final.mp4`.

For implementation details and commands, read [README_zh-CN.md](../../README_zh-CN.md).

