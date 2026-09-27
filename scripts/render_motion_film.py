#!/usr/bin/env python3
"""Render prepared, reference-conditioned artwork into a 1080p motion film.

No image generation or voice cloning is performed here. macOS `say` provides
Japanese speech. Pillow draws typography; OpenCV composites animated footage;
FFmpeg encodes H.264/AAC. All timings come from the authored manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import time
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SR = 48000


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def run(args):
    return subprocess.run([str(x) for x in args], check=True, capture_output=True)


def stamp(t):
    ms = round(t * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def validate(m):
    if m['duration'] != 120:
        raise ValueError('This romance compositor requires a complete 120-second chapter')
    if (m['width'], m['height'], m['fps']) not in ((1080, 1920, 30), (1920, 1080, 30)):
        raise ValueError('Delivery must be 1080p at 30 fps')
    cursor = 0
    for s in m['shots']:
        if abs(s['start'] - cursor) > .001 or s['end'] <= s['start']:
            raise ValueError('Shots must cover the complete timeline without gaps or overlaps')
        if min(s['zoom']) < 1:
            raise ValueError('Camera zoom may not expose empty borders')
        cursor = s['end']
    if cursor != m['duration']:
        raise ValueError('Storyboard length does not match delivery duration')
    previous = -1
    for line in m['dialogue']:
        if not (previous < line['start'] < m['duration']):
            raise ValueError('Dialogue must be ordered and within the timeline')
        previous = line['start']
        if not line['ja'] or not line['zh_CN'] or line['speaker'] not in m['voices']:
            raise ValueError('Each line needs Japanese, Chinese and a configured voice')


def write_wav(path, array):
    a = np.asarray(array)
    if np.max(np.abs(a)) >= 1:
        raise ValueError('Refusing to write clipped audio')
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1 if a.ndim == 1 else a.shape[1])
        out.setsampwidth(2)
        out.setframerate(SR)
        out.writeframes((a * 32767).astype('<i2').tobytes())


def read_wav(path):
    with wave.open(str(path)) as source:
        if source.getframerate() != SR or source.getsampwidth() != 2:
            raise ValueError('Expected 48 kHz PCM16 voice file')
        return np.frombuffer(source.readframes(source.getnframes()), '<i2').astype(np.float32).reshape(-1, source.getnchannels()) / 32768


def prepare_audio(m, project, ffmpeg):
    folder = project / 'audio'
    folder.mkdir(parents=True, exist_ok=True)
    timed, srt = [], []
    voices = np.zeros((round(m['duration'] * SR), 2), np.float32)
    duck = np.ones(len(voices), np.float32)
    for i, source in enumerate(m['dialogue']):
        line = dict(source, line_id=f'L{i+1:03}')
        voice = m['voices'][line['speaker']]
        # Explicit readings keep character names consistent without changing meaning.
        spoken = line['ja'].replace('夏帆', 'かほ').replace('湊', 'みなと')
        digest = hashlib.sha256((spoken + json.dumps(voice)).encode()).hexdigest()
        raw, wav = folder / f'{line["line_id"]}.aiff', folder / f'{line["line_id"]}.wav'
        cache = folder / f'{line["line_id"]}.sha256'
        if not wav.exists() or wav.stat().st_size < SR or not cache.exists() or cache.read_text() != digest:
            run(['say', '-v', voice['id'], '-r', str(voice['rate']), '-o', raw, spoken])
            run([ffmpeg, '-y', '-v', 'error', '-i', raw, '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le', wav])
            cache.write_text(digest)
        data = read_wav(wav)
        if len(data) < SR * .25 or np.max(np.abs(data)) < .001:
            raise ValueError(f'Empty speech for {line["line_id"]}; macOS speech service may require access outside sandbox')
        # Keep natural speech intact; ripple starts only into available quiet beats.
        requested_start = line['start']
        if timed:
            line['start'] = max(line['start'], timed[-1]['end'] + .4)
        if line['start'] + len(data)/SR > m['duration'] - 3:
            raise ValueError(f'{line["line_id"]}: speech exceeds the film; revise dialogue or voice rate')
        if line['start'] != requested_start:
            line['requested_start'] = requested_start
            print(f"timing {line['line_id']}: {requested_start:.2f} -> {line['start']:.2f}s", flush=True)
        peak = float(np.max(np.abs(data)))
        data *= min(.72/peak, 3)
        start = round(line['start']*SR)
        voices[start:start+len(data)] += data
        line['end'] = round(line['start'] + len(data)/SR, 3)
        line['audio_file'] = str(wav.relative_to(project))
        line['script_sha256'] = digest
        line['meaning_check'] = 'agent_reviewed'
        timed.append(line)
        srt += [str(i+1), f"{stamp(line['start'])} --> {stamp(line['end']+.2)}", line['zh_CN'], '']
        lo, hi = max(0, start-int(.2*SR)), min(len(duck), start+len(data)+int(.3*SR))
        duck[lo:hi] = .32
        ramp = min(int(.16*SR), hi-lo)
        duck[lo:lo+ramp] = np.linspace(1,.32,ramp)
        duck[hi-ramp:hi] = np.linspace(.32,1,ramp)
        print(f"voice {line['line_id']}: {line['end']-line['start']:.2f}s", flush=True)
    save_json(project/'script/dialogue_timed.json', timed)
    save_json(project/'audio/voice_manifest.json', {'provider':'macOS Speech Synthesis', 'voices':m['voices'], 'locale':'ja-JP', 'lines':timed, 'peak_dbfs':20*math.log10(float(np.max(np.abs(voices))))})
    (project/'subtitles/zh-CN.srt').write_text('\n'.join(srt))
    (project/'script/dialogue.md').write_text('\n\n'.join(f"{x['line_id']} · {x['speaker']} · {x['start']:.2f}s\n\n{x['ja']}\n\n{x['zh_CN']}" for x in timed))
    write_wav(folder/'voice.wav', voices)
    rng = np.random.default_rng(20260927)
    music = np.zeros_like(voices)

    def note(at, midi, duration, gain, pan=0):
        start = int(at*SR)
        count = min(int(duration*SR), len(music)-start)
        if count <= 0: return
        t = np.arange(count, dtype=np.float32)/SR
        freq = 440*2**((midi-69)/12)
        tone = np.zeros(count, np.float32)
        for harmonic, weight in [(1,1),(2,.28),(3,.12),(4,.045)]:
            tone += weight*np.sin(2*np.pi*freq*harmonic*t)*np.exp(-t*(.5+.22*harmonic))
        tone *= (1-np.exp(-t*120))*np.minimum(1, (duration-t)/.2)*gain
        music[start:start+count,0] += tone*math.sqrt((1-pan)/2)
        music[start:start+count,1] += tone*math.sqrt((1+pan)/2)

    # Authored five-note leitmotif. No sampled music or third-party melodies.
    beat = 60/m['motif']['bpm']
    for cycle, origin in enumerate([1.5,15,28.5,42,55.5,69,82.5,96,109]):
        for j,(pitch,position) in enumerate(zip(m['motif']['notes_midi'],m['motif']['beats'])):
            note(origin+position*beat, pitch, 6, .042 if cycle < 6 else .054, (j-2)*.13)
        bass = [50,47,43,45][cycle%4]
        for n,p in enumerate([bass,bass+7,bass+14]):
            note(origin+n*3.3, p, 9, .032, -.18+n*.18)
    # Very quiet original sustained pad, with slow harmonic movement.
    for section,bass in enumerate([50,47,43,45,50,47,43,50]):
        lo,hi = int(section*15*SR), int((section+1)*15*SR)
        t = np.arange(hi-lo,dtype=np.float32)/SR
        env = np.minimum(1,t/3)*np.minimum(1,(15-t)/4)
        pad = sum(np.sin(2*np.pi*440*2**((n-69)/12)*t) for n in [bass,bass+7,bass+14])*.003
        music[lo:hi] += (pad*env)[:,None]
    # Discrete stereo room echoes; original synthesis only.
    dry = music.copy()
    for delay,gain in [(.17,.22),(.31,.14),(.53,.08)]:
        shift=int(delay*SR)
        music[shift:] += dry[:-shift,::-1]*gain
    music *= duck[:,None]
    ambient = rng.normal(0,1,voices.shape).astype(np.float32)
    # Rain's fine high-frequency texture plus a low soft station wash.
    for ch in range(2):
        smooth = np.convolve(ambient[:,ch],np.ones(13,dtype=np.float32)/13,'same')
        ambient[:,ch] = (.65*ambient[:,ch]+.8*smooth)*.006
    for at in np.arange(1.2,m['duration'],1.73):
        n=int(.12*SR); t=np.arange(n,dtype=np.float32)/SR
        drip=np.sin(2*np.pi*(1700*t-1900*t*t))*np.exp(-45*t)*.012
        i=int(at*SR); n=min(n,len(ambient)-i)
        ambient[i:i+n,int(at)%2] += drip[:n]
    # Distant, soft train approach at the end; no copyrighted sound samples.
    lo=int(107*SR); t=np.arange(len(ambient)-lo,dtype=np.float32)/SR
    approach=np.minimum(1,t/8)*np.minimum(1,(13-t)/2)
    train=(np.sin(2*np.pi*83*t)+.4*np.sin(2*np.pi*167*t))*.003*approach
    ambient[lo:] += train[:,None]
    all_t=np.arange(len(voices),dtype=np.float32)/SR
    fade=np.minimum(1,all_t/1.4)*np.minimum(1,(m['duration']-all_t)/3)
    music*=fade[:,None]; ambient*=fade[:,None]
    mix=voices+music+ambient
    peak=float(np.max(np.abs(mix)))
    if peak>.89: mix*=.89/peak
    write_wav(folder/'bgm_original.wav', music)
    write_wav(folder/'rain_original.wav', ambient)
    write_wav(folder/'mix.wav', mix)
    save_json(project/'audio/mix_stats.json', {'peak_dbfs':20*math.log10(float(np.max(np.abs(mix)))), 'sample_rate':SR, 'channels':2,'duration':len(mix)/SR,'music_duck_gain':.32,'music_source':'original additive synthesis','human_listening_review':False})
    print('audio mix complete',flush=True)


def wrap(text, font, max_width):
    lines=['']
    for c in text:
        if font.getlength(lines[-1]+c)>max_width:
            lines.append(c)
        else: lines[-1]+=c
    if len(lines)>2: raise ValueError('Subtitle exceeds two lines; split or shorten it')
    return lines


def text_tile(text, font, width, label=None):
    lines=wrap(text,font,width-100)
    h=50+len(lines)*60+(30 if label else 0)
    im=Image.new('RGBA',(width,h))
    draw=ImageDraw.Draw(im)
    draw.rounded_rectangle((6,3,width-6,h-3),radius=16,fill=(4,12,25,167))
    y=20
    if label:
        small=ImageFont.truetype(font.path,23)
        draw.text((width/2,y),label,font=small,anchor='mt',fill=(179,201,222,255))
        y+=35
    for line in lines:
        draw.text((width/2,y),line,font=font,anchor='mt',fill=(246,249,251,255),stroke_width=1,stroke_fill=(0,5,16,200))
        y+=60
    return np.asarray(im)


def composite(frame, rgba, x, y, opacity=1):
    h,w=rgba.shape[:2]
    roi=frame[y:y+h,x:x+w]
    a=rgba[:,:,3:4].astype(np.float32)*(opacity/255)
    roi[:]=(rgba[:,:,:3][:,:,::-1]*a+roi*(1-a)).astype(np.uint8)


def title_tile(m, font_path, width, closing=False):
    im=Image.new('RGBA',(width,340))
    d=ImageDraw.Draw(im)
    serif=ImageFont.truetype(font_path,150 if not closing else 90)
    d.text((width/2,15),m['series'],font=serif,anchor='mt',fill=(244,249,255,255),stroke_width=2,stroke_fill=(10,25,50,180))
    small=ImageFont.truetype(font_path,32)
    y=196 if not closing else 145
    d.line((width*.36,y,width*.64,y),fill=(193,213,230,220),width=1)
    d.text((width/2,y+28),'第 一 章  ·  '+m['chapter']+('  完' if closing else ''),font=small,anchor='mt',fill=(235,243,251,255),stroke_width=1,stroke_fill=(10,25,50,180))
    if closing:
        d.text((width/2,y+85),'明天，同一班车。',font=ImageFont.truetype(font_path,27),anchor='mt',fill=(205,221,236,255))
    return np.asarray(im)


def render(m, project, ffmpeg, font_path, preview=False):
    width,height,fps=m['width'],m['height'],m['fps']
    total=round(m['duration']*fps) if not preview else 180
    images={}
    for shot in m['shots']:
        path=project/'assets'/shot['asset']
        if shot['asset'] not in images:
            img=cv2.imread(str(path))
            if img is None: raise FileNotFoundError(path)
            ih,iw=img.shape[:2]
            # Layout fit only: original reference-conditioned artwork is kept untouched.
            ratio=max(width/iw,height/ih)
            img=cv2.resize(img,(math.ceil(iw*ratio),math.ceil(ih*ratio)),interpolation=cv2.INTER_CUBIC)
            top=(img.shape[0]-height)//2; left=(img.shape[1]-width)//2
            images[shot['asset']]=img[top:top+height,left:left+width].copy()
    timed=json.loads((project/'script/dialogue_timed.json').read_text())
    font=ImageFont.truetype(font_path,42)
    captions=[text_tile(x['zh_CN'],font,width-120) for x in timed]
    opening=title_tile(m,font_path,width)
    ending=title_tile(m,font_path,width,True)
    chapter=f"ch{m['chapter_number']:03}"
    outputs=[project/'renders'/('preview.mp4' if preview else f'{chapter}_final.mp4')]
    if not preview: outputs.append(project/'renders'/f'{chapter}_clean.mp4')
    encoders=[]
    for path in outputs:
        args=[ffmpeg,'-y','-v','warning','-f','rawvideo','-pixel_format','bgr24','-video_size',f'{width}x{height}','-framerate',str(fps),'-i','pipe:0','-i',str(project/'audio/mix.wav'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','19','-threads','3','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar',str(SR),'-t',str(total/fps),'-movflags','+faststart',str(path)]
        encoders.append(subprocess.Popen(args,stdin=subprocess.PIPE,stderr=open(path.with_suffix('.encode.log'),'w')))
    rng=np.random.default_rng(20260927)
    drops=[(rng.uniform(-80,width+80),rng.uniform(-height,height),rng.uniform(750,1400),rng.uniform(16,45),rng.uniform(.12,.27)) for _ in range(145)]
    shot_index=0; began=time.monotonic(); last_frame=None
    try:
        for frame_no in range(total):
            t=frame_no/fps
            while t>=m['shots'][shot_index]['end']: shot_index+=1
            shot=m['shots'][shot_index]
            p=(t-shot['start'])/(shot['end']-shot['start'])
            # Smooth endpoint velocity; restrained 2–6% moves per shot.
            u=p*p*(3-2*p)
            zoom=shot['zoom'][0]+u*(shot['zoom'][1]-shot['zoom'][0])
            ax,ay=shot['anchor']
            matrix=np.array([[zoom,0,(1-zoom)*width*ax],[0,zoom,(1-zoom)*height*ay]],np.float32)
            frame=cv2.warpAffine(images[shot['asset']],matrix,(width,height),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
            # Independent foreground rain, mostly beyond shelter edges; clear faces.
            wet=frame.copy()
            is_detail=shot['asset']=='shot06.png'
            for x0,y0,speed,length,strength in drops:
                y=(y0+t*speed)%(height+90)-45
                x=(x0+t*32)%(width+100)-50
                if not is_detail and 190<x<width-130 and 470<y<height-240: continue
                value=int(160+strength*250)
                cv2.line(wet,(int(x),int(y)),(int(x-6),int(y+length)),(value,min(255,value+10),min(255,value+20)),1,cv2.LINE_AA)
            if is_detail:
                for k,(x,y) in enumerate([(350,1570),(750,1390),(890,1740)]):
                    phase=(t*.75+k*.34)%1
                    radius=int(10+phase*85)
                    cv2.ellipse(wet,(x,y),(radius,max(1,int(radius*.22))),0,0,360,(160,184,201),1,cv2.LINE_AA)
            cv2.addWeighted(wet,.24,frame,.76,0,frame)
            # Atmosphere dissolve on opening/closing only; dialogue cuts remain clean.
            if shot_index in [0,13,20] and p<.06 and last_frame is not None:
                cv2.addWeighted(frame,min(1,p/.06),last_frame,1-min(1,p/.06),0,frame)
            if t<.8: frame=(frame*(.35+.65*t/.8)).astype(np.uint8)
            clean=frame
            final=clean.copy()
            if .8<t<6.6:
                alpha=min(1,(t-.8)/1,(6.6-t)/.8)
                composite(final,opening,0,240,max(0,alpha))
            if t>115:
                composite(final,ending,0,190,min(1,(t-115)/1.2))
            for i,line in enumerate(timed):
                if line['start']<=t<line['end']+.2:
                    tile=captions[i]
                    composite(final,tile,60,height-170-tile.shape[0])
                    break
            encoders[0].stdin.write(final.tobytes())
            if len(encoders)>1: encoders[1].stdin.write(clean.tobytes())
            if frame_no in [90,300,570,780,1020,1350,1740,2010,2250,2580,2940,3330,3510]:
                cv2.imwrite(str(project/'qa'/f'frame_{frame_no:04}.jpg'),final)
            if frame_no%150==0: print(f'render {frame_no}/{total} ({frame_no/max(.1,time.monotonic()-began):.1f} fps)',flush=True)
            if frame_no+1==total or (frame_no+1)/fps>=shot['end']: last_frame=clean.copy()
    finally:
        for encoder in encoders:
            if encoder.stdin: encoder.stdin.close()
        codes=[encoder.wait() for encoder in encoders]
    if any(codes): raise RuntimeError(f'Encoding failed: {codes}; see encode logs')
    print('render complete',flush=True)


def qa(m, project, ffmpeg):
    probe=str(Path(ffmpeg).with_name('ffprobe')) if '/' in ffmpeg else 'ffprobe'
    path=project/'renders'/f"ch{m['chapter_number']:03}_final.mp4"
    report=json.loads(run([probe,'-v','error','-count_frames','-show_format','-show_streams','-of','json',path]).stdout)
    video=next(s for s in report['streams'] if s['codec_type']=='video')
    audio=next(s for s in report['streams'] if s['codec_type']=='audio')
    checks={'resolution':(video['width'],video['height'])==(m['width'],m['height']), 'fps':video['avg_frame_rate']=='30/1', 'frame_count':int(video['nb_read_frames'])==round(m['duration']*m['fps']), 'duration':abs(float(report['format']['duration'])-m['duration'])<.05, 'h264':video['codec_name']=='h264', 'aac':audio['codec_name']=='aac'}
    save_json(project/'qa/ffprobe.json',report)
    # Decode validation catches broken packets independently of the frame generator.
    run([ffmpeg,'-v','error','-i',path,'-f','null','-'])
    checks['decode']=True
    samples=[]
    cap=cv2.VideoCapture(str(path))
    for seconds in [3,10,19,26,34,45,58,67,75,86,98,111,117]:
        cap.set(cv2.CAP_PROP_POS_MSEC,seconds*1000)
        ok,frame=cap.read()
        if not ok: raise RuntimeError(f'Could not decode QA frame at {seconds}s')
        thumb=cv2.resize(frame,(216,384))
        cv2.putText(thumb,f'{seconds:03}s',(10,25),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,255,255),1,cv2.LINE_AA)
        samples.append(thumb)
    cap.release()
    sheet=np.full((384*3,216*5,3),(16,22,32),np.uint8)
    for i,frame in enumerate(samples): sheet[(i//5)*384:(i//5+1)*384,(i%5)*216:(i%5+1)*216]=frame
    cv2.imwrite(str(project/'qa/contact_sheet.jpg'),sheet)
    save_json(project/'qa/technical_checks.json',checks)
    if not all(checks.values()): raise RuntimeError(f'Failed technical QA: {checks}')
    print(json.dumps(checks),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--phase',choices=['audio','render','preview','qa','all'],default='all')
    parser.add_argument('--ffmpeg',default=shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg')
    parser.add_argument('--font',default='/System/Library/Fonts/Hiragino Sans GB.ttc')
    args=parser.parse_args()
    m=json.loads(args.manifest.read_text()); validate(m)
    for folder in ['script','storyboard','assets','audio','subtitles','qa','renders']:
        (args.project/folder).mkdir(parents=True,exist_ok=True)
    save_json(args.project/'storyboard/manifest.json',m)
    if args.phase in ['audio','all']: prepare_audio(m,args.project,args.ffmpeg)
    if args.phase in ['render','preview','all']: render(m,args.project,args.ffmpeg,args.font,args.phase=='preview')
    if args.phase in ['qa','all']: qa(m,args.project,args.ffmpeg)


if __name__=='__main__': main()
