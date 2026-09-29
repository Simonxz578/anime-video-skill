---
name: one-minute-anime-knowledge
description: Plan cited anime knowledge shorts and produce reference-locked Japanese romance motion films with local character voices, Chinese captions, original audio, and verified MP4 delivery. Use for continuing Rain chapters, voice repairs, director animatics, or local ComfyUI single-shot trials.
---

# Anime video production

Repository: `Simonxz578/anime-video-skill`. Preserve this skill's directory name for installation compatibility. Work from a full repository checkout: its scripts, examples and supporting docs are required; a standalone copy of this entry file is insufficient.

## Select the production path

- **Knowledge:** use `anime-video episode` / `create_episode` with reviewed source packs; new subjects require real research. See [README_zh-CN](../../README_zh-CN.md). Do not pass draft briefs off as cited scripts.
- **Romance planning:** initialize a series once, then chapters in order; read continuity and used-content state. Bind Japanese dialogue to Chinese subtitles by line ID. Existing CLI/MCP plans remain `planning_only` until media and review gates are met.
- **Rain continuation or repair:** read [production preferences](../../docs/rain-production-preferences.md) and [production workflows](../../docs/production-workflows.md). Preserve current masters, location continuity, notebook ownership and the latest v3 voices.
- **Voice:** use the working [local VOICEVOX CLI/MCP](../../docs/local-voice.md). Never silently revert a series to system speech. Use full-sentence synthesis, native pitch, bounded punctuation pauses and measured timing; adjust slots instead of truncating/stretching syllables. Record voice IDs, credits and queries. Do not claim celebrity participation or cloning.
- **30-second Rain director reference:** use [day2 examples](../../examples/rain/day2/production_timeline.json), audio/project builders, HyperFrames and FFmpeg finishing. Read [six upstream skill records](../../docs/upstream-skills.md) only for relevant methods; installation does not mean every upstream runtime is active.
- **Actual generated character motion:** use [LOCAL_VIDEO_PROVIDER](../../docs/local-video-provider.md). Run one 4–6s sample before batch production; inspect consecutive frames, stable faces, identities and correct handoff. Wan 5B has not passed; 14B and LTX-2.5 remain untested. Never substitute a zoom/pan and call this test passed.

## Delivery and identity

Default MP4: 1080p, constant 30fps, H.264/yuv420p, AAC stereo 48kHz, faststart; portrait 1080×1920 or requested landscape 1920×1080. Knowledge targets 60 seconds; standard romance targets 120 seconds / 3600 frames. An explicit brief overrides these defaults: the rain-after-sun photo reference is **720×1280, 30 seconds / 900 frames**.

Keep the supplied character masters immutable. New artwork must use these references; inspect face/hair/eyes, navy-white costume, female socks and hand/prop continuity. Use the available reference-conditioned image tool, then prepare approved local keyframes. Scripts do not generate artwork themselves.

Use original authored music and ambience, lower music under dialogue, keep stems and credit local voices. For Rain, preserve the D–F♯–A–E–C♯ motif; the day2 arrangement uses 72 BPM. No paid API fallback is authorized for this series.

Deliver a subtitled preview, clean reference, subtitles and measured technical QA when requested. Verify the encoded MP4 with ffprobe and full decode; check actual frame count, audio timing and contact sheet. Preserve source/voice manifests and explicit agent-versus-human review status. A technical pass is not listening approval.

Describe the current illustrated/camera-motion films as director animatics or motion-illustration films, without claiming body animation or lip sync. Do not stretch an incomplete film to fake requested duration. Update continuity only after successful delivery.

## Legacy renderer

The original `scripts/render_motion_film.py` consumes an authored manifest and prepared images; see [motion-film guide](../../docs/motion-film.md). Its system voices and v2 `redub_rain.py` are historical reproduction paths. Use v3 local voices for current Rain work. `generate_voice(project_dir)` and other project-level MCP media placeholders are separate from the working `synthesize_local_voice` and local video tools.
