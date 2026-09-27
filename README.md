# One-minute anime knowledge video skill

A Codex Agent Skill and local MCP server for **planning** cited blue-white anime knowledge shorts and an original continuing romance series. The female and male masters supplied with this project are in `references/`.

**Current status:** installable Python package; offline planning for one curated astronomy topic and three original romance chapter fixtures; no production MP4 pipeline yet. Media tools intentionally return blocking status. See [中文说明](README_zh-CN.md) for setup and limitations.

Quick check with Python 3.10+:

```bash
python -m pip install -e '.[mcp]'
anime-video episode '为什么夜空是黑的？' --series cosmos --quality draft
anime-video romance-series
anime-video romance-chapter 1
anime-video-mcp
```

The MCP process speaks stdio and does not print a startup banner. The official SDK is preferred; a minimal dependency-free stdio implementation supports offline planning when PyPI is unavailable. The skill is at `skills/one-minute-anime-knowledge/SKILL.md`.
