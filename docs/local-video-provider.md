# LOCAL_VIDEO_PROVIDER

An additional, local-only ComfyUI adapter. Existing planning and rendering paths remain intact. No cloud fallback, subscriptions or payment setup.

## Configuration

```bash
export LOCAL_VIDEO_PROVIDER=comfyui
export LOCAL_COMFYUI_URL=http://127.0.0.1:8188
```

Start an installed ComfyUI with `--listen 127.0.0.1 --disable-api-nodes`. The adapter rejects remote URLs, credentials embedded in URLs, redirects and node types outside its reviewed local-node allowlist. Custom nodes still execute local Python; install only reviewed node packages.

```bash
PYTHONPATH=src python -m anime_knowledge_video.local_video health
PYTHONPATH=src python -m anime_knowledge_video.local_video submit \
  --workflow path/to/workflow_api.json --save path/to/job.json
PYTHONPATH=src python -m anime_knowledge_video.local_video status --prompt-id JOB_ID
```

The existing `anime-video-mcp` server also exposes `local_video_health`, `submit_local_video` and `local_video_status`, including the minimal stdio fallback. `submit_local_video` accepts a ComfyUI API graph, not the UI editor format. UI templates can be kept separately for editing. Inputs are prepared in the local ComfyUI `input/` directory; actual MP4 files are written to its `output/` directory. Returned output names are metadata, not an animation-quality verdict.

## Apple M1 Pro / 16GB pilot

- Isolated Python 3.12 arm64 + PyTorch MPS + ComfyUI.
- `city96/ComfyUI-GGUF` for quantized model/text loading.
- Initial model: Wan2.2 TI2V-5B `Q4_K_M`, UMT5-XXL `Q3_K_S`, Wan2.2 VAE.
- First run a tiny compatibility probe, then a single 4–6-second I2V test at a disclosed low native resolution. Do not claim this is native 1080p.
- MPS and CPU share 16GB; CUDA VRAM recommendations cannot be interpreted as equivalent unified-memory requirements. Monitor runtime and memory. Do not disable OS memory limits to force a render.
- A 5B I2V test does not establish that the 14B first/last-frame or LTX-2.5 model is usable. Track each separately.

Model sources (download sizes are recorded by the actual install, not hardcoded as memory requirements):

| File | ComfyUI folder | Source |
|---|---|---|
| `Wan2.2-TI2V-5B-Q4_K_M.gguf` | `models/unet` | [QuantStack](https://huggingface.co/QuantStack/Wan2.2-TI2V-5B-GGUF) |
| `umt5-xxl-encoder-Q3_K_S.gguf` | `models/text_encoders` | [city96](https://huggingface.co/city96/umt5-xxl-encoder-gguf) |
| `wan2.2_vae.safetensors` | `models/vae` | [Comfy-Org](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/tree/main/split_files/vae) |

Install artifacts, pinned upstream commits, weight hashes, logs and the MCP smoke result belong under ignored `outputs/local-video-provider/`. Do not vendor third-party code or model weights into this repository.

## Acceptance gate

A successful job only proves inference and encoding. Inspect consecutive frames and video to assess continuous character motion, face/identity stability, hand/prop continuity and correct handoff direction. Record native dimensions, fps, elapsed time, model/seed and failures. Never treat pan/zoom/rain overlays or an interpolated still as generated character motion. Batch production stays blocked until the actual single-shot result passes the user's animation criteria.

Sources: [official Wan workflows](https://docs.comfy.org/tutorials/video/wan/wan2_2), [official LTX-2](https://github.com/Lightricks/LTX-2), [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF). The requested iizcm skill currently lacks the helper scripts mentioned in its text; the requested artokun MCP currently declares end of maintenance. Installation alone is not evidence of a working video model.

## Recorded CPU/MPS diagnostic (2026-09-28)

Same conditioning/noise, seed 27092026, 128×224, 9 frames, 20 steps, CFG 5, UniPC/simple, shift 8, float32. Both CPU and MPS sampling produced corrupt frames. Decoding the same latents across devices gave mean absolute errors below 8e-7; the reference VAE roundtrip was recognizable. This points upstream of VAE decoding for this tiny test, but does not establish the exact model/configuration defect or prove all CPU resolutions fail. See [measured comparison](../examples/rain/local-video-device-comparison.json).

The 4–6-second character-motion acceptance gate remains **not passed**. Wan 14B first/last-frame and LTX-2.5 were not tested. The delivered montage/director animatic was an explicitly allowed separate editorial path.

### Reproduce the device comparison

`scripts/diagnose_local_video.py` is the actual diagnostic script, with configurable paths. It requires the previously installed ComfyUI + GGUF environment under `outputs/local-video-provider/ComfyUI` (override `LOCAL_VIDEO_HOME`), the three model files above, and a reference-conditioned two-person scene at `ComfyUI/input/rain_station_reference.png`. Use ComfyUI's Python environment and run sequentially:

```bash
python scripts/diagnose_local_video.py prepare cpu
python scripts/diagnose_local_video.py sample cpu
python scripts/diagnose_local_video.py sample mps
python scripts/diagnose_local_video.py decode cpu
python scripts/diagnose_local_video.py decode mps
```

Preparation writes conditioning and noise once; both samplers consume those exact tensors. Decoders render both sample sets and a VAE roundtrip for comparison. Each stage overwrites diagnostic artifacts; retain previous evidence first if needed. The historical [5B workflow](../examples/rain/wan22_test_api.json) also records the original 121-frame / 24fps pilot, which is separate from the 9-frame diagnostic. Its initial notebook-on-bench staging is historical; the requested final test must instead start with Minato already holding the notebook. Neither graph is an accepted animation result. This publication preserves the earlier diagnostic; it does not rerun expensive model sampling.
