"""Availability report without printing secrets."""

import importlib.util
import os
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
available = ["Python", "female reference", "male reference"]
optional = []
blocking = []
for label, executable in [("Node", "node"), ("FFmpeg", "ffmpeg"), ("ffprobe", "ffprobe")]:
    (available if shutil.which(executable) else optional).append(label)
(available if importlib.util.find_spec("mcp") else optional).append("MCP Python SDK")
for name in ("OPENAI_API_KEY", "IMAGE_PROVIDER", "TTS_PROVIDER", "MUSIC_PROVIDER"):
    (available if os.getenv(name) else optional).append(name)
for name in ("character_master.png", "female_lead_master.png", "male_lead_master.png"):
    if not (root / "references" / name).exists():
        blocking.append(name)
for title, values in [("AVAILABLE", available), ("OPTIONAL MISSING", optional), ("BLOCKING MISSING", blocking)]:
    print(title)
    for value in values:
        print("-", value)

