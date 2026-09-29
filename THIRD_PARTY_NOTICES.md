# Third-party notices

No third-party source code, music, font, or model weight is vendored in this repository. The supplied character images are user-provided assets.

The local motion-film renderer optionally uses NumPy, Pillow, OpenCV and an installed FFmpeg executable. macOS supplies the speech voices and system font; neither voice model nor font binaries are distributed here. Generated speech is subject to the operating system's applicable terms. The sample score and rain are synthesized from authored notes and procedural noise, with no imported soundtrack samples.

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk): optional dependency; see its [license](https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE).
- [Remotion](https://github.com/remotion-dev/remotion): optional compositor dependency; see its [license and eligibility terms](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md).
- [OpenMontage](https://github.com/calesthio/OpenMontage): architectural reference only, no code copied; [AGPL-3.0](https://github.com/calesthio/OpenMontage/blob/main/LICENSE).

## Current production dependencies

- [VOICEVOX Core](https://github.com/VOICEVOX/voicevox_core) 0.17.0: local optional CPU runtime. Core license and each model/voice's terms apply separately. Required Rain credits: **VOICEVOX:雨晴はう / VOICEVOX:玄野武宏**. No voice/model binaries are distributed here.
- HyperFrames CLI 0.8.81 and GSAP 3.14.2 are external runtime dependencies. Obtain their packages upstream and follow their respective licenses; bundled JS is not committed.
- ComfyUI, ComfyUI-GGUF, PyTorch and Wan weights remain separate installations. A local adapter does not grant rights to redistribute their code or weights.
- The six external Skill repositories are recorded in [upstream-skills.md](docs/upstream-skills.md) and the pinned lock file. This repository publishes our integration instructions and production scripts, not copied upstream Skill contents. Remotion and Chengfeng were method references for the day2 production; their engines did not render that film.
