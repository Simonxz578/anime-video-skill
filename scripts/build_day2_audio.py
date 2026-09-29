#!/usr/bin/env python3
"""Reproducible local VOICEVOX dialogue and original Rain-motif score."""
import dataclasses, hashlib, json, wave
import os
from pathlib import Path
import numpy as np
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
from redub_rain import ROOT, RUNTIME, SR, FF, read, write, run, stamp

OUT=ROOT/'outputs/romance/rain/day2_photo_demo'
LINES=[
 ('D01','female',4.0,7.98,'ねえ、雨上がりの街って、ちょっときれいだね。','你看，雨后的街道，还挺好看的。'),
 ('D02','male',8.15,11.9,'だから、撮りたくなるんだよ。','所以才会想拍下来。'),
 ('D03','female',12.45,15.8,'今、私のこと撮った？','你刚才拍我了？'),
 ('D04','male',16.12,20.85,'ごめん。なんか、いい感じだったから。','抱歉。就是觉得刚才挺好看的。'),
 ('D05','female',22.0,24.8,'……悪くないかも。','……好像还不错。'),
 ('D06','female',25.02,27.9,'じゃ、今度は一緒に撮ろ。','那这次一起拍吧。'),
 ('D07','male',28.0,28.96,'え、今？','诶，现在？'),
 ('D08','female',29.0,29.53,'今。','就现在。'),
]

def main():
 for folder in ['audio','qa','subtitles','renders']:(OUT/folder).mkdir(parents=True,exist_ok=True)
 s=Synthesizer(Onnxruntime.load_once(filename=(os.environ.get('VOICEVOX_ONNXRUNTIME') or str(RUNTIME/'onnxruntime/lib/libvoicevox_onnxruntime.1.17.3.dylib'))),OpenJtalk(RUNTIME/'dict/open_jtalk_dic_utf_8-1.11'),acceleration_mode='CPU',cpu_num_threads=4)
 for n in [0,4]:
  with VoiceModelFile.open(RUNTIME/f'models/vvms/{n}.vvm') as m:s.load_voice_model(m)
 stems={x:np.zeros((SR*30,2),np.float32) for x in ['female','male']};timed=[]
 for ident,sex,start,deadline,ja,zh in LINES:
  sid=10 if sex=='female' else 11;q=s.create_audio_query(ja,sid)
  q.speed_scale=1.02 if sex=='female' else .94;q.pitch_scale=.006 if sex=='female' else 0
  q.intonation_scale=1.10 if sex=='female' else 1.0
  q.pre_phoneme_length=.045 if sex=='female' else .07;q.post_phoneme_length=.09 if sex=='female' else .13
  q.output_sampling_rate=24000;q.output_stereo=False
  for phrase in q.accent_phrases:
   if phrase.pause_mora:
    p=phrase.pause_mora;limit=.22 if sex=='female' else .15
    if isinstance(p,dict):p['vowel_length']=min(limit,p['vowel_length'])
    else:p.vowel_length=min(limit,p.vowel_length)
   if sex=='female' and phrase.moras and not phrase.is_interrogative and phrase.moras[-1].pitch>0:phrase.moras[-1].pitch-=.025
  raw=OUT/'audio'/f'{ident}_native24.wav';path=OUT/'audio'/f'{ident}.wav'
  raw.write_bytes(s.synthesis(q,sid))
  run([FF,'-v','error','-y','-i',raw,'-af','aresample=48000:filter_size=64:phase_shift=10:cutoff=0.97,highpass=f=60,lowpass=f=11500','-ar',SR,'-ac',2,path])
  data=read(path)
  active=np.flatnonzero(np.max(np.abs(data),axis=1)>.002)
  data=data[max(0,active[0]-int(.035*SR)):min(len(data),active[-1]+int(.07*SR))]
  duration=len(data)/SR
  # Never time-stretch or concatenate phonemes. Any fit change must be explicit.
  print(ident,sex,'duration',round(duration,3),'slot',deadline-start,flush=True)
  rms=float(np.sqrt(np.mean(data**2)));peak=float(np.max(np.abs(data)))
  data*=min(.10/max(rms,1e-6),.63/max(peak,1e-6));n=240
  data[:n]*=np.linspace(0,1,n)[:,None];data[-n:]*=np.linspace(1,0,n)[:,None];write(path,data)
  end=start+duration
  if end>deadline:raise ValueError(f"{ident}: speech ends at {end:.3f}s after slot deadline {deadline}s; adjust timing, never truncate")
  lo=round(start*SR);stems[sex][lo:lo+len(data)]+=data
  timed.append(dict(id=ident,speaker=sex,start=start,end=end,slot_deadline=deadline,ja=ja,zh_CN=zh,style_id=sid,query=dataclasses.asdict(q),tempo_adjustment=1.0,audio_file=str(path.relative_to(OUT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 for sex,data in stems.items():write(OUT/'audio'/f'{sex}_ja.wav',data)
 voice=stems['female']+stems['male'];write(OUT/'audio/dialogue_mix.wav',voice)
 (OUT/'audio/dialogue_timed.json').write_text(json.dumps(timed,ensure_ascii=False,indent=2))
 manifest=json.loads((OUT/'assets/references/voice_manifest_v3.json').read_text())
 manifest.update(revision='day2_reuse_act1_v3',count=8,female_lines_regenerated=5,male_lines_regenerated=3,female_source='same style 10 and base preset; new locked dialogue',human_listening_review=False)
 (OUT/'audio/voice_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 # 72 BPM, unchanged D-F#-A-E-C# series motif, brighter Dmaj9 harmonies.
 rng=np.random.default_rng(4721);N=30*SR;bgm=np.zeros((N,2),np.float32)
 def add(buf,x,at,pan=0):
  i=round(at*SR);n=min(len(x),len(buf)-i)
  if n>0:buf[i:i+n,0]+=x[:n]*(1-pan*.3);buf[i:i+n,1]+=x[:n]*(1+pan*.3)
 def note(midi,duration,amp,kind='piano'):
  t=np.arange(round(duration*SR))/SR;f=440*2**((midi-69)/12)
  if kind=='pad':
   env=np.minimum(t/.45,1)*np.minimum((duration-t)/.6,1)
   x=sum(np.sin(2*np.pi*f*(1+d)*t) for d in [-.0007,0,.0007])/3
   return (x*env*amp).astype(np.float32)
  env=(1-np.exp(-t*180))*np.exp(-t/(.85 if kind=='piano' else .42))*np.minimum((duration-t)/.12,1)
  x=sum(a*np.sin(2*np.pi*f*k*t)*np.exp(-t*(k-1)*.5) for k,a in [(1,1),(2,.3),(3,.12),(4,.06)])
  return (x*env*amp).astype(np.float32)
 beat=60/72
 for base in [.6,10.6,20.6]:
  for midi,b in zip([74,78,81,76,73],[0,1.5,3,5,7]):add(bgm,note(midi,3.2,.026),base+b*beat,(-1 if midi%2 else 1)*.2)
 for base,chord in [(0,[50,57,61,66]),(6.67,[47,54,61,66]),(13.33,[55,62,66,69]),(20,[50,57,61,66]),(26.67,[50,57,62,66])]:
  for midi in chord:add(bgm,note(midi,min(7,30-base),.005,'pad'),base,(midi%3-1)*.5)
  for j in range(8):
   at=base+j*beat
   if at<29.3:add(bgm,note(chord[j%len(chord)]+12,1.8,.011,'acoustic'),at,(-1)**j*.6)
 # Dialogue ducking with smooth shoulders.
 duck=np.ones(N,np.float32)
 for l in timed:
  lo=max(0,int((l['start']-.12)*SR));hi=min(N,int((l['end']+.16)*SR));duck[lo:hi]=.52
  n=min(int(.1*SR),(hi-lo)//2);duck[lo:lo+n]=np.linspace(1,.52,n);duck[hi-n:hi]=np.linspace(.52,1,n)
 bgm*=duck[:,None];bgm[:SR]*=np.linspace(0,1,SR)[:,None];bgm[-int(.5*SR):]*=np.linspace(1,0,int(.5*SR))[:,None]
 write(OUT/'audio/bgm.wav',bgm)
 amb=np.zeros_like(bgm);t=np.arange(N)/SR
 # Quiet broadband outdoor air and a distant tram passing; not a rain bed.
 noise=rng.normal(0,1,N).astype(np.float32);soft=np.convolve(noise,np.ones(160)/160,mode='same')
 amb[:,0]=soft*.017;amb[:,1]=np.roll(soft,800)*.015
 for at in [1.7,6.1,18.9,23.5]:
  tt=np.arange(int(.2*SR))/SR;x=.014*np.sin(2*np.pi*(1500*tt-1100*tt**2))*np.exp(-tt*35)
  add(amb,x,at,(-1 if at<10 else 1)*.7)
 tram=(np.sin(2*np.pi*(88*t+.13*t*t))*.0015+soft*.024)*np.exp(-((t-7.0)/4.8)**2)
 amb[:,0]+=tram;amb[:,1]+=np.roll(tram,1300)
 for at in [12.1,29.5]:
  tt=np.arange(int(.23*SR))/SR
  x=rng.normal(0,1,len(tt))*.025*(np.exp(-tt*85)+.6*np.exp(-np.maximum(tt-.055,0)*80)*(tt>.055))
  x+=.018*np.sin(2*np.pi*1400*tt)*np.exp(-tt*70)
  add(amb,x,at)
 amb[:int(.2*SR)]*=np.linspace(0,1,int(.2*SR))[:,None];amb[-int(.12*SR):]*=np.linspace(1,0,int(.12*SR))[:,None]
 write(OUT/'audio/ambience_sfx.wav',amb)
 mix=voice+bgm+amb;write(OUT/'audio/mix_pre_master.wav',mix)
 run([FF,'-v','error','-y','-i',OUT/'audio/mix_pre_master.wav','-af','loudnorm=I=-16:TP=-1.5:LRA=8','-ar',SR,'-ac',2,OUT/'audio/final_original_mix.wav'])
 srt=[]
 ass='[Script Info]\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\nWrapStyle: 0\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Hiragino Sans GB,32,&H00FFFFFF,&H000000FF,&H80202020,&H80000000,0,0,0,0,100,100,0,0,1,1.4,0,2,36,36,112,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
 def ast(t):return f'{int(t)//3600}:{int(t)//60%60:02}:{t%60:05.2f}'
 for i,l in enumerate(timed):
  end=min(l['end']+.06,timed[i+1]['start']-.02 if i+1<len(timed) else 29.5)
  srt.extend([str(i+1),f"{stamp(l['start'])} --> {stamp(end)}",l['zh_CN'],''])
  ass+=f"Dialogue: 0,{ast(l['start'])},{ast(end)},Default,,0,0,0,,{l['zh_CN']}\n"
 (OUT/'subtitles/zh-CN.srt').write_text('\n'.join(srt));(OUT/'subtitles/zh-CN.ass').write_text(ass)
 (OUT/'VOICE_CREDITS.md').write_text('# 音声クレジット\n\n夏帆：VOICEVOX:雨晴はう（Style 10）\n\n湊：VOICEVOX:玄野武宏（Style 11）\n\n第一幕 v3 同一角色 preset；本地 CPU 合成，无真人声纹克隆。发布时请将本署名放在视频描述中。\n')
 print('AUDIO_READY',flush=True)

if __name__=='__main__':main()
