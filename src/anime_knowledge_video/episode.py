"""A truthful offline path and explicit final production gate."""

from pathlib import Path

from .contracts import GateError, SERIES, check_duration, check_reference
from .io import ROOT, slug, write_json, write_text
from .research import load_pack, save_research
from .storyboard import build_storyboard


def create_episode(topic: str, series: str = "cosmos", duration_sec: int = 60,
                   quality: str = "draft", research_pack: str | None = None,
                   output_root: str | None = None) -> dict:
    if series not in SERIES:
        raise GateError(f"series must be one of {sorted(SERIES)}")
    check_duration(duration_sec)
    if quality not in {"draft", "final"}:
        raise GateError("quality must be draft or final")
    reference = ROOT / "references" / "character_master.png"
    check_reference(reference)
    topic_id = slug(topic)
    pack = load_pack(topic_id, research_pack)
    if pack["series"] != series:
        raise GateError("source pack series does not match request")
    project = Path(output_root or ROOT / "projects") / topic_id
    save_research(pack, project)
    script = pack["script"]
    if len(script) < 6:
        raise GateError("script needs at least six editorial beats")
    write_json(project / "brief.json", {"topic": topic, "series": series, "duration_sec": duration_sec, "quality": quality})
    write_json(project / "script" / "script.json", {"language": "zh-CN", "beats": script, "estimated_tts_duration": None})
    write_text(project / "script" / "script.md", "# " + topic + "\n\n" + "\n\n".join(x["text"] for x in script))
    shots = build_storyboard(script, duration_sec, str(reference))
    write_json(project / "storyboard" / "storyboard.json", shots)
    write_json(project / "assets" / "manifests" / "assets.json", {"reference": str(reference), "generated": [], "status": "pending"})
    write_json(project / "cost_report.json", {"llm": 0, "images": 0, "video_clips": 0, "tts": 0, "music": 0, "rendering": 0, "currency": "USD", "note": "offline planning only"})
    write_text(project / "qa" / "qa_report.md", "# QA\n\nStatus: PLANNING ONLY. Character, audio, subtitle, visual, and render QA are pending.\n")
    if quality == "final":
        raise GateError(f"Planning saved at {project}. Final requires live research review, media providers, Remotion/FFmpeg rendering, and human character QA; no MP4 was claimed.")
    return {"project_dir": str(project), "storyboard_json": str(project / "storyboard" / "storyboard.json"),
            "sources_md": str(project / "research" / "sources.md"), "qa_report": str(project / "qa" / "qa_report.md"),
            "cost_report": str(project / "cost_report.json"), "final_mp4": None, "status": "planning_only"}
