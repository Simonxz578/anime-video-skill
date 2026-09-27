"""Checks that protect the deliverable contract."""

from pathlib import Path

SERIES = {"physics", "cosmos", "china_history", "world_history", "university_history"}
SHOT_FIELDS = {
    "shot_id", "start", "end", "narration", "purpose", "composition",
    "character_presence", "character_pose", "foreground", "background",
    "factual_visuals", "generated_visuals", "camera_motion", "text_overlay",
    "sfx", "transition", "generation_prompt", "negative_prompt",
    "reference_images", "reconstruction", "qa_notes",
}


class GateError(ValueError):
    """Production must stop rather than silently invent a passing artifact."""


def check_duration(duration: int, romance: bool = False) -> None:
    low, high = (115, 125) if romance else (55, 65)
    if not low <= duration <= high:
        raise GateError(f"duration must be {low}–{high} seconds")


def check_storyboard(shots: list[dict], duration: int) -> None:
    if not shots:
        raise GateError("storyboard is empty")
    cursor = 0.0
    for shot in shots:
        missing = SHOT_FIELDS - shot.keys()
        if missing:
            raise GateError(f"{shot.get('shot_id', '?')} missing {sorted(missing)}")
        if abs(shot["start"] - cursor) > 0.01 or shot["end"] <= shot["start"]:
            raise GateError("storyboard has a gap, overlap, or reversed shot")
        cursor = shot["end"]
    if abs(cursor - duration) > 0.01:
        raise GateError("storyboard does not cover requested duration")


def check_reference(path: Path) -> None:
    if not path.is_file() or path.stat().st_size < 1000:
        raise GateError(f"missing character master: {path}")

