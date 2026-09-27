"""Offline authoring path; release remains gated on actual media and human review."""

from pathlib import Path

from ..contracts import GateError, check_duration, check_reference
from ..io import ROOT, read_json, slug, write_json, write_text
from .content_dedup import check_new_content


def series_root(series_id: str, output_root: str | None = None) -> Path:
    clean = slug(series_id)
    if clean != series_id or not clean:
        raise GateError("series_id must be a lowercase ASCII slug")
    return Path(output_root or ROOT / "outputs" / "romance") / clean


def create_series(series_id: str = "after-the-rain-route", output_root: str | None = None) -> dict:
    root = series_root(series_id, output_root)
    female = ROOT / "references" / "female_lead_master.png"
    male = ROOT / "references" / "male_lead_master.png"
    check_reference(female)
    check_reference(male)
    for source, dest in [(female, root / "references" / "female_lead_master.png"),
                         (male, root / "references" / "male_lead_master.png")]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_bytes(source.read_bytes())
    write_text(root / "series_bible" / "series_bible.md", "# 雨停前的末班路\n\n原创都市二次元短剧。两位成年通勤者在同一座小站因一本落下的笔记相识。每章只推进一个具体选择。角色身份以双母版为准，声音与音乐尚待配置。\n")
    write_text(root / "series_bible" / "relationship.md", "# Relationship\n\n第 1 章陌生；第 2 章记住彼此的小事；第 3 章主动约见。实际状态以 continuity/state.json 为准。\n")
    write_text(root / "series_bible" / "locations.md", "# Locations\n\n青岚站东口：有雨棚、蓝色长椅和朝南的列车时刻牌。可重复地点，不可复用旧镜头。\n")
    write_json(root / "series_bible" / "timeline.json", {"season": "early autumn", "chapters": 3})
    if not (root / "continuity" / "state.json").exists():
        write_json(root / "continuity" / "state.json", {"last_chapter": 0, "relationship": "strangers", "known_facts": [], "location": "青岚站东口", "weather": "rain", "contact_exchanged": False})
    if not (root / "continuity" / "used_content_index.json").exists():
        write_json(root / "continuity" / "used_content_index.json", {"dialogue_hashes": [], "shot_hashes": []})
    write_json(root / "continuity" / "voices.json", {"female": {"locale": "ja-JP", "voice_id": None}, "male": {"locale": "ja-JP", "voice_id": None}, "status": "unconfigured; do not claim voice continuity"})
    return {"romance_series_root": str(root), "status": "series_planned"}


def _srt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    sec, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{sec:02},{millis:03}"


def create_chapter(series_id: str, chapter_number: int, chapter_prompt: str = "",
                   duration_sec: int = 120, quality: str = "draft", output_root: str | None = None) -> dict:
    check_duration(duration_sec, romance=True)
    if quality not in {"draft", "final"}:
        raise GateError("quality must be draft or final")
    root = series_root(series_id, output_root)
    if not (root / "series_bible" / "series_bible.md").exists():
        raise GateError("create_romance_series must run first")
    state_path = root / "continuity" / "state.json"
    state = read_json(state_path)
    if chapter_number != state["last_chapter"] + 1:
        raise GateError("chapters must be planned in order from continuity state")
    fixture = ROOT / "examples" / "romance" / f"ch{chapter_number:03d}.json"
    if not fixture.exists():
        raise GateError("No authored chapter fixture. Supply a new reviewed script before extending the series.")
    data = read_json(fixture)
    lines = data["dialogue"]
    shots = data["shots"]
    ids = [line["line_id"] for line in lines]
    if len(ids) != len(set(ids)):
        raise GateError("duplicate line_id")
    for line in lines:
        if not all(line.get(key) for key in ("ja", "zh_CN", "speaker", "shot_id")):
            raise GateError("Japanese/Chinese subtitle binding incomplete")
        if line["speaker"] not in {"female", "male"} or line["end"] <= line["start"]:
            raise GateError("invalid dialogue timing or speaker")
        if line["end"] > duration_sec:
            raise GateError("dialogue exceeds chapter duration")
        if line["zh_CN"].count("\n") > 1:
            raise GateError("subtitle exceeds two lines")
    if not set(line["shot_id"] for line in lines).issubset({shot["shot_id"] for shot in shots}):
        raise GateError("dialogue references unknown shot")
    index_path = root / "continuity" / "used_content_index.json"
    index = read_json(index_path)
    report = check_new_content(lines, shots, index)
    chapter = root / "chapters" / f"ch{chapter_number:03d}"
    write_json(chapter / "script" / "dialogue_timed.json", lines)
    write_text(chapter / "script" / "dialogue_ja.md", "\n\n".join(f"{x['line_id']} {x['speaker']}: {x['ja']}" for x in lines))
    write_text(chapter / "script" / "dialogue_zh-CN.md", "\n\n".join(f"{x['line_id']} {x['speaker']}: {x['zh_CN']}" for x in lines))
    write_json(chapter / "storyboard" / "storyboard.json", shots)
    srt = "\n\n".join(f"{i}\n{_srt_time(x['start'])} --> {_srt_time(x['end'])}\n{x['zh_CN']}" for i, x in enumerate(lines, 1))
    write_text(chapter / "subtitles" / "zh-CN.srt", srt)
    write_json(chapter / "continuity" / "chapter_content_fingerprint.json", report)
    write_text(chapter / "qa" / "content_dedup_report.md", "# Content dedup\n\nExact text and shot signature checks passed. Image perceptual and video segment checks are pending.\n")
    write_text(chapter / "qa" / "subtitle_accuracy_report.md", "# Subtitle accuracy\n\nLine IDs and timing bind. Japanese→Chinese semantic accuracy requires human bilingual review.\n")
    for name in ("character_lock_report", "voice_report", "bgm_originality_report"):
        write_text(chapter / "qa" / f"{name}.md", "# Pending\n\nNo rendered media exists; cannot pass this gate.\n")
    write_text(chapter / "qa" / "qa_report.md", "# QA\n\nStatus: PLANNING ONLY. No final MP4 may be released from this path.\n")
    write_json(chapter / "cost_report.json", {"currency": "USD", "planning": 0, "media": None})
    next_state = {**state, **data["state_after"], "last_chapter": chapter_number}
    write_json(state_path, next_state)
    write_json(index_path, {"dialogue_hashes": index["dialogue_hashes"] + report["dialogue_hashes"],
                            "shot_hashes": index["shot_hashes"] + report["shot_hashes"]})
    if quality == "final":
        raise GateError(f"Chapter planning saved at {chapter}. Final needs Japanese TTS, bilingual subtitle review, original music, visual QA, rendering, and media dedup.")
    return {"romance_series_root": str(root), "chapter_dir": str(chapter),
            "dialogue_ja": str(chapter / "script" / "dialogue_ja.md"),
            "dialogue_zh_CN": str(chapter / "script" / "dialogue_zh-CN.md"),
            "subtitle_accuracy_report": str(chapter / "qa" / "subtitle_accuracy_report.md"),
            "content_dedup_report": str(chapter / "qa" / "content_dedup_report.md"),
            "qa_report": str(chapter / "qa" / "qa_report.md"), "final_mp4": None,
            "final_clean_mp4": None, "status": "planning_only"}
