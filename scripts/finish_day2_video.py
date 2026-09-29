#!/usr/bin/env python3
"""Caption overlays, identical audio mux, contact sheet and measured QA."""
import hashlib,json,subprocess,wave
import os
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build_day2_project import OUT,SHOTS
FF=os.environ.get('FFMPEG_BIN', 'ffmpeg');FP=os.environ.get('FFPROBE_BIN', 'ffprobe')

def run(args):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True)
 (OUT/'qa/finishing_commands.log').open('a').write(json.dumps([str(x) for x in args],ensure_ascii=False)+'\n'+p.stderr+'\n')
 if p.returncode:raise RuntimeError(p.stderr[-4000:])
 return p.stdout

def main():
 for folder in ['qa','renders','subtitles']:(OUT/folder).mkdir(parents=True,exist_ok=True)
 preview=OUT/'renders/rain_day2_photo_demo_preview_30s.mp4';reference=OUT/'renders/rain_day2_photo_seedance_reference_30s.mp4'
 base=OUT/'renders/director_picture_30s.mp4';mix=OUT/'audio/final_original_mix.wav'
 credit='VOICEVOX:雨晴はう / VOICEVOX:玄野武宏; illustrated director animatic'
 run([FF,'-v','error','-y','-i',base,'-i',mix,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t','30','-movflags','+faststart','-metadata','comment='+credit,reference])
 lines=json.loads((OUT/'audio/dialogue_timed.json').read_text());font=ImageFont.truetype(os.environ.get('ANIME_CJK_FONT', '/System/Library/Fonts/Hiragino Sans GB.ttc'),32)
 capdir=OUT/'subtitles/plates';capdir.mkdir(exist_ok=True)
 args=[FF,'-v','error','-y','-i',reference];filters=[]
 for i,l in enumerate(lines):
  canvas=Image.new('RGBA',(720,180));d=ImageDraw.Draw(canvas)
  # Same understated white/ink outline as act1, scaled for 720px delivery.
  text=l['zh_CN'];wrapped=['']
  for c in text:
   if d.textlength(wrapped[-1]+c,font=font)>630:wrapped.append(c)
   else:wrapped[-1]+=c
  for j,line in enumerate(wrapped):d.text((360,60+j*43),line,font=font,anchor='mm',fill=(248,248,244,255),stroke_width=2,stroke_fill=(8,14,25,225))
  path=capdir/f'{i:02}.png';canvas.save(path);args+=['-i',path]
  end=min(l['end']+.06,lines[i+1]['start']-.02 if i+1<len(lines) else 29.5)
  last='0:v' if i==0 else f'v{i-1}'
  filters.append(f"[{last}][{i+1}:v]overlay=0:1080:enable='gte(t,{l['start']})*lt(t,{end})'[v{i}]")
 args+=['-filter_complex',';'.join(filters),'-map',f'[v{len(lines)-1}]','-map','0:a:0','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','copy','-r','30','-frames:v','900','-t','30','-movflags','+faststart','-metadata','comment='+credit,preview]
 run(args)
 # Contact sheet from the encoded result, one per actual keyframe segment.
 thumbw=270;thumbh=480;labelh=36;cols=4;rows=3
 sheet=Image.new('RGB',(cols*thumbw,rows*(thumbh+labelh)),(15,22,32));draw=ImageDraw.Draw(sheet)
 label=ImageFont.truetype(os.environ.get('ANIME_LABEL_FONT', '/System/Library/Fonts/Supplemental/Arial.ttf'),15)
 for i,(id,a,b,*_) in enumerate(SHOTS):
  path=OUT/'qa'/f'encoded_{id}.jpg';t=(a+b)/60
  run([FF,'-v','error','-y','-ss',f'{t:.5f}','-i',preview,'-frames:v','1','-q:v','2',path])
  im=Image.open(path).convert('RGB');im.thumbnail((thumbw,thumbh),Image.Resampling.LANCZOS)
  x=i%cols*thumbw;y=i//cols*(thumbh+labelh);sheet.paste(im,(x,y));draw.text((x+8,y+thumbh+8),f'{id} | {a/30:.2f}-{b/30:.2f}s',font=label,fill='white')
 sheet.save(OUT/'qa/contact_sheet.jpg',quality=93)
 probes={}
 for kind,path in [('preview',preview),('reference',reference)]:
  p=json.loads(run([FP,'-v','error','-show_streams','-show_format','-of','json',path]));probes[kind]=p
  v=next(s for s in p['streams'] if s['codec_type']=='video');a=next(s for s in p['streams'] if s['codec_type']=='audio')
  assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']),v['codec_name'])==(720,1280,'30/1',900,'h264')
  assert a['codec_name']=='aac' and a['channels']==2 and abs(float(p['format']['duration'])-30)<.1
  run([FF,'-v','error','-i',path,'-f','null','-'])
  run([FF,'-v','error','-y','-i',path,'-map','0:a','-c','copy','-f','hash','-hash','sha256',OUT/'qa'/f'{kind}_audio.sha256'])
  probes[kind]['file_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 assert (OUT/'qa/preview_audio.sha256').read_text()==(OUT/'qa/reference_audio.sha256').read_text()
 (OUT/'qa/media_probe.json').write_text(json.dumps(probes,ensure_ascii=False,indent=2))
 stems={}
 for name in ['female_ja','male_ja','dialogue_mix','bgm','ambience_sfx','final_original_mix']:
  with wave.open(str(OUT/'audio'/f'{name}.wav')) as w:
   stems[name]={'frames':w.getnframes(),'sample_rate':w.getframerate(),'channels':w.getnchannels(),'seconds':w.getnframes()/w.getframerate()}
  assert stems[name]['seconds']==30 and stems[name]['channels']==2
 (OUT/'qa/audio_stem_probe.json').write_text(json.dumps(stems,indent=2))
 print('FINISH_PASS',flush=True)

if __name__=='__main__':main()
