"""Reject exact reuse of dialogue or storyboard content across chapters."""

import hashlib
import re

from ..contracts import GateError


def normalized(text: str) -> str:
    return re.sub(r"[\W_]+", "", text.casefold(), flags=re.UNICODE)


def fingerprint(text: str) -> str:
    return hashlib.sha256(normalized(text).encode("utf-8")).hexdigest()


def check_new_content(lines: list[dict], shots: list[dict], index: dict) -> dict:
    previous_dialogue = set(index.get("dialogue_hashes", []))
    previous_shots = set(index.get("shot_hashes", []))
    dialogue_hashes = [fingerprint(line["ja"]) for line in lines]
    shot_hashes = [fingerprint(shot["composition"] + shot["action"]) for shot in shots]
    if len(dialogue_hashes) != len(set(dialogue_hashes)) or previous_dialogue.intersection(dialogue_hashes):
        raise GateError("dialogue repeats within this chapter or an earlier chapter")
    if len(shot_hashes) != len(set(shot_hashes)) or previous_shots.intersection(shot_hashes):
        raise GateError("shot composition/action repeats within this chapter or an earlier chapter")
    return {"dialogue_hashes": dialogue_hashes, "shot_hashes": shot_hashes,
            "asset_hashes": [], "video_segment_hashes": [], "status": "text-only exact-match pass; media reuse unverified"}

