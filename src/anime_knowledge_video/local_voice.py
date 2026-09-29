"""Local VOICEVOX 0.17 speech with the Rain v3 character presets.

Optional native dependencies are loaded only for synthesis. No cloud fallback.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import uuid
import wave
from pathlib import Path

from .io import ROOT, write_json

PRESETS = {
    "female": dict(style_id=10, model="0.vvm", credit="VOICEVOX:雨晴はう",
                   speed=1.02, pitch=0.006, intonation=1.10, pause_max=0.22,
                   pre=0.045, post=0.09),
    "male": dict(style_id=11, model="4.vvm", credit="VOICEVOX:玄野武宏",
                 speed=0.94, pitch=0.0, intonation=1.0, pause_max=0.15,
                 pre=0.07, post=0.13),
}


def runtime_paths():
    root = Path(os.environ.get("VOICEVOX_RUNTIME", ROOT / "outputs/local-voice-provider/runtime"))
    override = os.environ.get("VOICEVOX_ONNXRUNTIME")
    candidates = sorted((root / "onnxruntime/lib").glob("*voicevox_onnxruntime*"))
    lib = Path(override) if override else next((p for p in candidates if p.is_file()), None)
    return root, lib, root / "dict/open_jtalk_dic_utf_8-1.11"


def voice_preset(speaker):
    if speaker not in PRESETS:
        raise ValueError("speaker must be female or male")
    return dict(PRESETS[speaker])


def health():
    root, lib, dictionary = runtime_paths()
    checks = {
        "voicevox_core": importlib.util.find_spec("voicevox_core") is not None,
        "numpy": importlib.util.find_spec("numpy") is not None,
        "ffmpeg": bool(shutil.which(os.environ.get("FFMPEG_BIN", "ffmpeg"))),
        "onnxruntime": lib is not None and lib.is_file(),
        "dictionary": (dictionary / "sys.dic").is_file(),
        "female_model": (root / "models/vvms/0.vvm").is_file(),
        "male_model": (root / "models/vvms/4.vvm").is_file(),
    }
    return dict(provider="voicevox_core", local_only=True, cloud_fallback=False,
                ready=all(checks.values()), checks=checks, presets=PRESETS)


def synthesize(text: str, speaker: str, output_dir="outputs/local-voice",
               max_duration_sec: float | None = None):
    """Create a new WAV and manifest, never replace a prior utterance in place."""
    preset = voice_preset(speaker)
    if not isinstance(text, str) or not text.strip() or len(text) > 4000:
        raise ValueError("text must contain 1–4000 characters")
    if max_duration_sec is not None and not 0 < max_duration_sec <= 600:
        raise ValueError("max_duration_sec must be in (0, 600]")
    out = (ROOT / output_dir).resolve()
    if not out.is_relative_to((ROOT / "outputs").resolve()):
        raise ValueError("output_dir must be inside this checkout's outputs/")
    status = health()
    if not status["ready"]:
        missing = [k for k, v in status["checks"].items() if not v]
        raise RuntimeError("Local voice dependencies missing: " + ", ".join(missing))
    import numpy as np
    from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

    root, lib, dictionary = runtime_paths()
    s = Synthesizer(Onnxruntime.load_once(filename=str(lib)), OpenJtalk(dictionary),
                    acceleration_mode="CPU", cpu_num_threads=4)
    with VoiceModelFile.open(root / "models/vvms" / preset["model"]) as model:
        s.load_voice_model(model)
    q = s.create_audio_query(text, preset["style_id"])
    q.speed_scale, q.pitch_scale = preset["speed"], preset["pitch"]
    q.intonation_scale = preset["intonation"]
    q.pre_phoneme_length, q.post_phoneme_length = preset["pre"], preset["post"]
    q.output_sampling_rate, q.output_stereo = 24000, False
    for phrase in q.accent_phrases:
        if phrase.pause_mora:
            p = phrase.pause_mora
            if isinstance(p, dict):
                p["vowel_length"] = min(preset["pause_max"], p["vowel_length"])
            else:
                p.vowel_length = min(preset["pause_max"], p.vowel_length)
        if speaker == "female" and phrase.moras and not phrase.is_interrogative:
            if phrase.moras[-1].pitch > 0:
                phrase.moras[-1].pitch -= 0.025
    native = s.synthesis(q, preset["style_id"])
    with tempfile.TemporaryDirectory(prefix="anime-voice-") as tmp:
        raw, resampled = Path(tmp) / "native.wav", Path(tmp) / "resampled.wav"
        raw.write_bytes(native)
        subprocess.run([os.environ.get("FFMPEG_BIN", "ffmpeg"), "-v", "error", "-y",
                        "-i", str(raw), "-af",
                        "aresample=48000:filter_size=64:phase_shift=10:cutoff=0.97,"
                        "highpass=f=60,lowpass=f=11500", "-ar", "48000", "-ac", "2",
                        str(resampled)], check=True, capture_output=True)
        with wave.open(str(resampled)) as w:
            data = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, 2)
            data = data.astype(np.float32) / 32768
    active = np.flatnonzero(np.max(np.abs(data), axis=1) > 0.002)
    if not len(active):
        raise RuntimeError("Synthesis returned silence")
    data = data[max(0, active[0] - 1680):min(len(data), active[-1] + 3360)]
    duration = len(data) / 48000
    if max_duration_sec is not None and duration > max_duration_sec:
        raise ValueError(f"Speech needs {duration:.3f}s; slot is {max_duration_sec}s. "
                         "Adjust timing; no speech was truncated or time-stretched.")
    rms, peak = float(np.sqrt(np.mean(data ** 2))), float(np.max(np.abs(data)))
    data *= min(0.10 / max(rms, 1e-6), 0.63 / max(peak, 1e-6))
    n = min(240, len(data) // 2)
    data[:n] *= np.linspace(0, 1, n)[:, None]
    data[-n:] *= np.linspace(1, 0, n)[:, None]
    out.mkdir(parents=True, exist_ok=True)
    ident = speaker + "-" + uuid.uuid4().hex[:12]
    path = out / (ident + ".wav")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes((data * 32767).astype("<i2").tobytes())
    (out / (ident + "_native24.wav")).write_bytes(native)
    result = dict(status="synthesized", provider="VOICEVOX Core 0.17.0 local CPU",
                  speaker=speaker, text=text, preset=preset, query=dataclasses.asdict(q),
                  audio_file=str(path), duration_sec=duration, sample_rate=48000, channels=2,
                  time_stretch=False, human_listening_review=False,
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    write_json(out / (ident + ".json"), result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["health", "synthesize"])
    parser.add_argument("--speaker", choices=list(PRESETS))
    parser.add_argument("--text")
    parser.add_argument("--output-dir", default="outputs/local-voice")
    parser.add_argument("--max-duration", type=float)
    args = parser.parse_args()
    if args.action == "health":
        result = health()
    else:
        if not args.speaker or not args.text:
            parser.error("--speaker and --text are required")
        result = synthesize(args.text, args.speaker, args.output_dir, args.max_duration)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
