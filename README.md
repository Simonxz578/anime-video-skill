# anime-video-skill

A Codex Agent Skill and local MCP server for **planning** cited blue-white anime knowledge shorts and an original continuing romance series. The female and male masters supplied with this project are in `references/`.

**Video standard: 1080p, 30fps.** Portrait: 1080×1920; landscape when requested: 1920×1080. H.264/AAC MP4.

**Current status:** offline knowledge/romance planning plus a working local motion-illustration film compositor. The new renderer consumes prepared character-conditioned artwork and an authored timeline; it creates Japanese speech, Chinese subtitles, original synthesized music, animated rain and camera moves. The MCP media placeholders remain blocked and are not connected to this renderer. See [中文说明](README_zh-CN.md) and [rendering guide](docs/motion-film.md).

The original two-minute chapter **《雨》第一章：初遇** is authored in `examples/rain/ch001.json`. Its generated media lives in the local `outputs/romance/rain/` folder and is excluded from Git. This is an illustrated motion film, with no lip synchronization or generated character-body animation.

Quick check with Python 3.10+:

```bash
python -m pip install -e '.[mcp]'
anime-video episode '为什么夜空是黑的？' --series cosmos --quality draft
anime-video romance-series
anime-video romance-chapter 1
anime-video-mcp
```

The MCP process speaks stdio and does not print a startup banner. The official SDK is preferred; a minimal dependency-free stdio implementation supports offline planning when PyPI is unavailable. The skill is at `skills/one-minute-anime-knowledge/SKILL.md`.
