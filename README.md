# anime-video-skill

A Codex Agent Skill and local MCP server for **planning** cited blue-white anime knowledge shorts and an original continuing romance series. The female and male masters supplied with this project are in `references/`.

**Video standard: 1080p, 30fps.** Portrait: 1080×1920; landscape when requested: 1920×1080. H.264/AAC MP4.

**Version 0.3.0:** production planning, local VOICEVOX dialogue (including the repaired Rain v3 male voice), illustrated film/montage scripts, a 30-second HyperFrames director-reference workflow, and a loopback-only ComfyUI video adapter. Both official and minimal MCP servers expose local voice and video tools. Project-wide media placeholder tools remain separate.

The current two-minute film is **《雨》第一章 · 第一幕《初见》**. The new day2 photo scene explicitly uses **720×1280, 30fps, 30 seconds / 900 frames**. Both delivered works are illustrated animatics, without generated continuous body motion or lip synchronization. Generated images, audio, video and weights stay in ignored `outputs/`.

- [Production workflows](docs/production-workflows.md): scripts, dependencies, expected assets, finishing and QA.
- [Local voice](docs/local-voice.md): setup, fixed presets, CLI/MCP and credits.
- [Local video provider](docs/local-video-provider.md): single-shot gate and CPU/MPS diagnostic findings. Wan 5B has not passed; 14B/LTX-2.5 are untested.
- [Six upstream skills](docs/upstream-skills.md) and [pinned paths](config/upstream-skills.lock.json).
- [Day2 script/timeline/Seedance handoff](examples/rain/day2/) and [中文说明](README_zh-CN.md).

Quick check with Python 3.10+:

```bash
python -m pip install -e '.[mcp]'
anime-video episode '为什么夜空是黑的？' --series cosmos --quality draft
anime-video romance-series
anime-video romance-chapter 1
anime-video-mcp
# Optional VOICEVOX runtime required for synthesis (see local voice guide):
anime-video-voice health
anime-video-voice synthesize --speaker male --text 'だから、撮りたくなるんだよ。'
```

The MCP process speaks stdio and does not print a startup banner. The official SDK is preferred; a minimal dependency-free stdio implementation supports offline planning when PyPI is unavailable. The skill is at `skills/one-minute-anime-knowledge/SKILL.md`.
