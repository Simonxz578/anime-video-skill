"""Official MCP Python SDK stdio server. Requires the [mcp] extra."""

from .contracts import GateError
from .episode import create_episode as plan_episode
from .io import ROOT, slug
from .local_video import LocalVideoProvider
from .local_voice import health as voice_health, synthesize as synthesize_voice
from .research import load_pack
from .romance.workflow import create_chapter, create_series
from .storyboard import build_storyboard

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None


def create_server():
    if FastMCP is None:
        raise RuntimeError("Install the MCP extra: python -m pip install -e '.[mcp]'")
    mcp = FastMCP("anime-knowledge-video")

    @mcp.tool()
    def local_voice_health() -> dict:
        """Check the optional local VOICEVOX runtime and locked Rain voice presets."""
        return voice_health()

    @mcp.tool()
    def synthesize_local_voice(text: str, speaker: str,
                               output_dir: str = "outputs/local-voice",
                               max_duration_sec: float | None = None) -> dict:
        """Create credited Japanese WAV speech; female or male, no cloud fallback."""
        return synthesize_voice(text, speaker, output_dir, max_duration_sec)

    @mcp.tool()
    def local_video_health() -> dict:
        """Check the loopback-only ComfyUI provider. Never route to a cloud API."""
        return LocalVideoProvider().health()

    @mcp.tool()
    def submit_local_video(workflow: dict) -> dict:
        """Submit one approved API graph; completion does not imply animation QA passed."""
        return LocalVideoProvider().submit(workflow)

    @mcp.tool()
    def local_video_status(prompt_id: str) -> dict:
        """Read the local job result without submitting another generation."""
        return LocalVideoProvider().status(prompt_id)

    @mcp.tool()
    def create_episode(topic: str, series: str = "cosmos", language: str = "zh-CN",
                       duration_sec: int = 60, aspect_ratio: str = "9:16",
                       quality: str = "draft", character_reference: str | None = None,
                       notes: str | None = None, research_pack: str | None = None) -> dict:
        """Plan a cited 60-second anime knowledge video; final release is gated."""
        if language != "zh-CN" or aspect_ratio != "9:16":
            raise GateError("MVP only supports zh-CN and 9:16")
        if character_reference and character_reference != str(ROOT / "references" / "character_master.png"):
            raise GateError("MVP uses the supplied immutable character master")
        return plan_episode(topic, series, duration_sec, quality, research_pack)

    @mcp.tool()
    def research_episode(topic: str, research_pack: str | None = None) -> dict:
        """Read a cited local pack. No live automatic research is claimed."""
        return load_pack(slug(topic), research_pack)

    @mcp.tool()
    def write_script(topic: str, research_pack: str | None = None) -> dict:
        """Return the reviewed example beat script from a source pack."""
        pack = load_pack(slug(topic), research_pack)
        return {"language": "zh-CN", "beats": pack["script"], "estimated_tts_duration": None}

    @mcp.tool()
    def build_storyboard(topic: str, duration_sec: int = 60,
                         research_pack: str | None = None) -> list[dict]:
        """Build a complete timed shot list from a reviewed example script."""
        pack = load_pack(slug(topic), research_pack)
        return build_storyboard(pack["script"], duration_sec,
                                str(ROOT / "references" / "character_master.png"))

    @mcp.tool()
    def generate_assets(project_dir: str) -> dict:
        """Report availability of character-conditioned image generation."""
        return {"status": "blocking_missing", "reason": "No image provider adapter configured; reference identity cannot be verified", "project_dir": project_dir}

    @mcp.tool()
    def generate_voice(project_dir: str) -> dict:
        """Report availability of fixed-voice narration."""
        return {"status": "blocking_missing", "reason": "Project-wide voice adapter is not connected; use synthesize_local_voice for Japanese dialogue", "project_dir": project_dir}

    @mcp.tool()
    def generate_music(project_dir: str) -> dict:
        """Report availability of licensed original music."""
        return {"status": "blocking_missing", "reason": "No original music provider configured", "project_dir": project_dir}

    @mcp.tool()
    def render_episode(project_dir: str) -> dict:
        """Do not publish before media and QA gates pass."""
        return {"status": "blocking_missing", "reason": "Remotion/FFmpeg render adapter not yet installed", "project_dir": project_dir}

    @mcp.tool()
    def qa_episode(project_dir: str) -> dict:
        """Report pending gates for a planning-only episode."""
        return {"status": "pending", "checks": ["live fact review", "character", "audio", "subtitles", "ffprobe", "contact sheet"], "project_dir": project_dir}

    @mcp.tool()
    def create_batch(topics: list[str], series: str = "cosmos") -> list[dict]:
        """Plan at most six curated episodes."""
        if len(topics) > 6:
            raise GateError("batch limit is six")
        return [plan_episode(topic, series=series) for topic in topics]

    @mcp.tool()
    def create_romance_series(series_id: str = "after-the-rain-route") -> dict:
        """Initialize an original romance series with locked female and male masters."""
        return create_series(series_id)

    @mcp.tool()
    def create_romance_chapter(series_id: str, chapter_number: int, chapter_prompt: str = "",
                               duration_sec: int = 120, language_spoken: str = "ja-JP",
                               subtitle_language: str = "zh-CN", quality: str = "draft",
                               female_reference: str = "references/female_lead_master.png",
                               male_reference: str = "references/male_lead_master.png",
                               continuity_mode: bool = True,
                               forbid_previous_content_reuse: bool = True) -> dict:
        """Plan a 120-second chapter with Japanese dialogue and bound Chinese captions."""
        if language_spoken != "ja-JP" or subtitle_language != "zh-CN":
            raise GateError("romance requires ja-JP speech and zh-CN subtitles")
        if not continuity_mode or not forbid_previous_content_reuse:
            raise GateError("MVP requires continuity and previous-content reuse protection")
        if female_reference != "references/female_lead_master.png" or male_reference != "references/male_lead_master.png":
            raise GateError("supplied master references are immutable in MVP")
        return create_chapter(series_id, chapter_number, chapter_prompt, duration_sec, quality)

    return mcp


def main() -> None:
    if FastMCP is None:
        from .mcp_lite import run
        run()
    else:
        create_server().run(transport="stdio")


if __name__ == "__main__":
    main()
