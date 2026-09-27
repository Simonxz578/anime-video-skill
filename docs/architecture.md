# MVP architecture decision

The Python package owns source packs, scripts, storyboard timing, continuity, subtitle binding and release gates. The official Python MCP SDK exposes the same orchestration via stdio when installed; a minimal stdio fallback covers offline planning without PyPI. The Remotion folder defines a deterministic 1080×1920/30 fps composition contract, but the current Python pipeline does not claim a rendered export. All media adapters are unimplemented and report `blocking_missing`.

OpenMontage is an external workflow reference only; its AGPL code is not copied. Remotion is an optional external compositor with its own license. A stock-footage fallback is intentionally excluded because it breaks the fixed-character visual IP. Later integration can add independently licensed image/TTS/music adapters, but a final release must only succeed after content and technical QA actually pass.
