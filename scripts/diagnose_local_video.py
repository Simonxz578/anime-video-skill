"""Controlled local CPU/MPS comparison using identical saved conditioning/noise.

Run sequentially: prepare cpu, sample cpu, sample mps, decode cpu, decode mps.
This is a numerical diagnostic, not a motion/identity acceptance test.
"""
import sys
import os
import json
import time
import hashlib
import importlib.util
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('LOCAL_VIDEO_HOME', REPO / 'outputs/local-video-provider'))
COMFY = ROOT / 'ComfyUI'
OUT = ROOT / 'device-diagnostic'
OUT.mkdir(parents=True, exist_ok=True)
if len(sys.argv) != 3 or sys.argv[1] not in ('prepare', 'sample', 'decode') or sys.argv[2] not in ('cpu', 'mps'):
    raise SystemExit('Usage: diagnose_local_video.py {prepare|sample|decode} {cpu|mps}')
phase, device = sys.argv[1:3]
sys.path.insert(0, str(COMFY))
sys.argv = ['device_diagnostic', '--fp32-unet', '--fp32-vae',
            '--fp16-text-enc', '--use-pytorch-cross-attention',
            '--disable-smart-memory', '--preview-method', 'none']
if device == 'cpu':
    sys.argv.append('--cpu')
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['DO_NOT_TRACK'] = '1'
import comfy.options
comfy.options.enable_args_parsing()
import torch
import numpy as np
from PIL import Image
import nodes
import comfy.sample
import comfy.utils
import comfy.model_management as mm
from comfy_extras.nodes_wan import Wan22ImageToVideoLatent
from comfy_extras.nodes_model_advanced import ModelSamplingSD3

torch.set_num_threads(8)
torch.set_grad_enabled(False)
spec = importlib.util.spec_from_file_location('diagnostic_gguf', COMFY / 'custom_nodes/ComfyUI-GGUF/__init__.py', submodule_search_locations=[str(COMFY / 'custom_nodes/ComfyUI-GGUF')])
pkg = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pkg
spec.loader.exec_module(pkg)
classes = pkg.NODE_CLASS_MAPPINGS
WIDTH, HEIGHT, LENGTH, STEPS, SEED = 128, 224, 9, 20, 27092026

def stats(x):
    x = x.detach().cpu().float()
    return dict(shape=list(x.shape), finite=bool(torch.isfinite(x).all()),
                min=float(x.min()), max=float(x.max()), mean=float(x.mean()),
                rms=float(x.square().mean().sqrt()))

def save_json(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')

def video(name, pixels):
    pixels = pixels.detach().cpu().float()
    np.save(OUT / (name + '.npy'), pixels.numpy())
    rgb = (pixels.clamp(0, 1).numpy() * 255).round().astype(np.uint8)
    for i in [0, len(rgb)//2, len(rgb)-1]:
        Image.fromarray(rgb[i]).save(OUT / f'{name}_frame{i:02d}.png')
    subprocess.run([os.environ.get('FFMPEG_BIN', 'ffmpeg'), '-v', 'error', '-y', '-f', 'rawvideo',
        '-pixel_format', 'rgb24', '-video_size', f'{rgb.shape[2]}x{rgb.shape[1]}',
        '-framerate', '24', '-i', '-', '-an', '-c:v', 'libx264', '-crf', '18',
        '-pix_fmt', 'yuv420p', str(OUT / (name + '.mp4'))], input=rgb.tobytes(), check=True)

t0 = time.monotonic()
print(f'BEGIN {phase} {device}, actual device={mm.get_torch_device()}', flush=True)
if phase == 'prepare':
    assert device == 'cpu'
    workflow = json.loads((REPO / 'examples/rain/wan22_test_api.json').read_text())
    clip = classes['CLIPLoaderGGUF']().load_clip('umt5-xxl-encoder-Q3_K_S.gguf', 'wan')[0]
    positive = nodes.CLIPTextEncode().encode(clip, workflow['5']['inputs']['text'])[0]
    negative = nodes.CLIPTextEncode().encode(clip, workflow['6']['inputs']['text'])[0]
    torch.save({'positive': positive, 'negative': negative}, OUT / 'conditioning.pt')
    print('Conditioning saved', stats(positive[0][0]), flush=True)
    mm.unload_all_models()
    del clip
    import gc
    gc.collect()
    vae = nodes.VAELoader().load_vae('wan2.2_vae.safetensors')[0]
    image_path = COMFY / 'input/rain_station_reference.png'
    pixels = torch.from_numpy(np.array(Image.open(image_path).convert('RGB')).astype(np.float32)/255)[None]
    latent = Wan22ImageToVideoLatent.execute(vae, WIDTH, HEIGHT, LENGTH, 1, pixels)[0]
    noise = comfy.sample.prepare_noise(latent['samples'], SEED)
    resized = comfy.utils.common_upscale(pixels.movedim(-1,1), WIDTH, HEIGHT, 'bilinear', 'center').movedim(1,-1)
    roundtrip_latent = vae.encode(resized.repeat(LENGTH,1,1,1))
    torch.save({'latent':latent, 'noise':noise, 'roundtrip_latent':roundtrip_latent, 'reference_pixels':resized}, OUT / 'inputs.pt')
    save_json('manifest.json', {'width':WIDTH,'height':HEIGHT,'frames':LENGTH,'steps':STEPS,'seed':SEED,
        'cfg':5.0,'sampler':'uni_pc','scheduler':'simple','shift':8.0,
        'diffusion_dtype':'float32','vae_dtype':'float32','gguf_dequant_dtype':'float32',
        'reference_sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
        'torch':torch.__version__, 'positive':stats(positive[0][0]),'negative':stats(negative[0][0]),
        'latent':stats(latent['samples']),'noise':stats(noise),'preparation_device':'cpu'})
elif phase == 'sample':
    data = torch.load(OUT / 'inputs.pt', weights_only=True)
    cond = torch.load(OUT / 'conditioning.pt', weights_only=True)
    model = classes['UnetLoaderGGUFAdvanced']().load_unet('Wan2.2-TI2V-5B-Q4_K_M.gguf', 'float32', 'float32', False)[0]
    model = ModelSamplingSD3().patch(model, shift=8.0)[0]
    trace = []
    def callback(step, x0, x, total):
        trace.append({'step':step,'x0':stats(x0),'x':stats(x),'elapsed':time.monotonic()-t0})
        if step in (0, 1, total-1):
            torch.save({'x0':x0.detach().cpu(),'x':x.detach().cpu()}, OUT / f'{device}_step{step:02d}.pt')
        save_json(f'{device}_trace.json',trace)
        print(f'{device} step {step+1}/{total}: {trace[-1]["x0"]}',flush=True)
    samples = comfy.sample.sample(model, data['noise'].clone(), STEPS, 5.0, 'uni_pc', 'simple',
        cond['positive'],cond['negative'],data['latent']['samples'].clone(),denoise=1.0,
        noise_mask=data['latent']['noise_mask'].clone(),callback=callback,disable_pbar=True,seed=SEED)
    torch.save(samples.detach().cpu(), OUT / f'{device}_samples.pt')
    save_json(f'{device}_sample_result.json',{'samples':stats(samples),'elapsed':time.monotonic()-t0,
        'actual_device':str(mm.get_torch_device()),'model_dtype':str(model.model.get_dtype())})
elif phase == 'decode':
    vae = nodes.VAELoader().load_vae('wan2.2_vae.safetensors')[0]
    inputs = torch.load(OUT / 'inputs.pt',weights_only=True)
    report = {}
    for source in ['roundtrip','cpu','mps']:
        latent = inputs['roundtrip_latent'] if source=='roundtrip' else torch.load(OUT/f'{source}_samples.pt',weights_only=True)
        pixels = vae.decode(latent)
        if pixels.ndim == 5:
            pixels = pixels.reshape(-1, *pixels.shape[-3:])
        name = f'{source}_decoded_{device}'
        video(name,pixels)
        report[name] = stats(pixels)
        print(name, report[name],flush=True)
    save_json(f'{device}_decode_result.json', {'images':report,'elapsed':time.monotonic()-t0})
else:
    raise ValueError(phase)
print(f'COMPLETE {phase} {device} in {time.monotonic()-t0:.2f}s', flush=True)
