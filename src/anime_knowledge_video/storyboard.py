"""Deterministic editorial storyboard for the offline demonstration."""

from .contracts import check_storyboard


def build_storyboard(script: list[dict], duration: int, reference: str) -> list[dict]:
    count = len(script)
    shots = []
    for i, line in enumerate(script):
        start = round(i * duration / count, 3)
        end = round((i + 1) * duration / count, 3)
        shots.append({
            "shot_id": f"S{i+1:02d}", "start": start, "end": end,
            "narration": line["text"], "purpose": line["purpose"],
            "composition": "blue-white illustrated editorial frame with negative space",
            "character_presence": i in {0, count - 1},
            "character_pose": "reference-locked still, no redraw" if i in {0, count - 1} else "none",
            "foreground": "subtle paper and orbital line layers",
            "background": "deep navy starfield or a source-grounded diagram",
            "factual_visuals": line.get("visual", "conceptual diagram; label as illustration"),
            "generated_visuals": [], "camera_motion": "slow push-in; 2.5D",
            "text_overlay": line.get("title", ""), "sfx": "restrained ambience",
            "transition": "soft dissolve", "generation_prompt": "blue-white anime editorial still; preserve master identity",
            "negative_prompt": "face drift, altered hair, altered eyes, extra fingers, neon, 3D",
            "reference_images": [reference] if i in {0, count - 1} else [],
            "reconstruction": False, "qa_notes": "Human review needed for factual visual and character identity",
        })
    check_storyboard(shots, duration)
    return shots

