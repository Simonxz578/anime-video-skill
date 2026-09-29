#!/usr/bin/env python3
"""Local, credited character TTS; no celebrity voice cloning or cloud calls."""
import dataclasses
import hashlib
import json
import subprocess
import wave
import os
from pathlib import Path

import numpy as np
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('VOICEVOX_RUNTIME', ROOT / 'outputs/local-voice-provider/runtime'))
SOURCE = ROOT / 'outputs/romance/rain/chapters/ch001'
OUT = ROOT / 'outputs/romance/rain/chapters/ch01/act01/refined'
FF = os.environ.get('FFMPEG_BIN', 'ffmpeg')
SR = 48000
VOICES = {
    'female': {'style_id': 10, 'credit': 'VOICEVOX:雨晴はう', 'pitch': .006, 'speed': 1.02,
               'direction': 'gentle, clear, youthful; soft endings, warm relief'},
    'male': {'style_id': 11, 'credit': 'VOICEVOX:玄野武宏', 'pitch': .035, 'speed': .92,
             'direction': 'clear young adult, restrained warmth, curious rising questions'},
}


def run(args):
    subprocess.run([str(x) for x in args], check=True, capture_output=True)


def read(path):
    with wave.open(str(path)) as w:
        assert w.getframerate() == SR and w.getsampwidth() == 2
        return np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1,w.getnchannels()).astype(np.float32)/32768


def write(path, data):
    assert np.max(np.abs(data)) < 1
    with wave.open(str(path),'wb') as w:
        w.setnchannels(data.shape[1]); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((data*32767).astype('<i2').tobytes())


def stamp(t):
    ms=round(t*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def main():
    for folder in ['audio','renders','qa','subtitles']:(OUT/folder).mkdir(parents=True,exist_ok=True)
    synth=Synthesizer(Onnxruntime.load_once(filename=(os.environ.get('VOICEVOX_ONNXRUNTIME') or str(RUNTIME/'onnxruntime/lib/libvoicevox_onnxruntime.1.17.3.dylib'))),
        OpenJtalk(RUNTIME/'dict/open_jtalk_dic_utf_8-1.11'),acceleration_mode='CPU',cpu_num_threads=4)
    for n in [0,4]:
        with VoiceModelFile.open(RUNTIME/f'models/vvms/{n}.vvm') as model:synth.load_voice_model(model)
    lines=json.loads((SOURCE/'script/dialogue_timed.json').read_text())
    stems=np.zeros((120*SR,2),np.float32)
    timed=[];srt=[]
    for i,line in enumerate(lines):
        conf=VOICES[line['speaker']];sid=conf['style_id']
        spoken=line['ja'].replace('夏帆','かほ').replace('湊','みなと')
        q=synth.create_audio_query(spoken,sid)
        q.speed_scale=conf['speed'];q.pitch_scale=conf['pitch']
        q.intonation_scale=1.10 if line['speaker']=='female' else 1.15
        q.pre_phoneme_length=.045;q.post_phoneme_length=.09
        q.output_sampling_rate=SR;q.output_stereo=True
        # Give scene-specific emotional contours without changing words or identities.
        if i in [0,2,4,14,20]:q.intonation_scale=1.17
        if i in [7,15,17,21]:q.intonation_scale=1.20
        if i in [10,11,20,21]:q.speed_scale*=.95
        # Soften phrase endings, while preserving question rises.
        for phrase in q.accent_phrases:
            if phrase.pause_mora:
                pause=phrase.pause_mora
                limit=.22 if line['speaker']=='female' else .25
                if isinstance(pause,dict):pause['vowel_length']=min(limit,pause['vowel_length'])
                else:pause.vowel_length=min(limit,pause.vowel_length)
            if phrase.moras and not phrase.is_interrogative:
                last=phrase.moras[-1]
                if last.pitch>0:last.pitch-=.025
        ident=line['line_id']; raw=OUT/'audio'/f'{ident}_raw.wav'
        raw.write_bytes(synth.synthesis(q,sid))
        data=read(raw)
        # Remove only leading/trailing silence; never cut spoken content.
        active=np.flatnonzero(np.max(np.abs(data),axis=1)>.004)
        if len(active)==0:raise ValueError(f'Empty voice {ident}')
        data=data[max(0,active[0]-int(.045*SR)):min(len(data),active[-1]+int(.12*SR))]
        slot=(lines[i+1]['start']-.30 if i+1<len(lines) else 115.0)-line['start']
        tempo=max(1.,len(data)/SR/slot)
        write(OUT/'audio'/f'{ident}_trim.wav',data)
        path=OUT/'audio'/f'{ident}.wav'
        # Time-stretch retains pitch. At most a modest speedup; no clipped dialogue.
        if tempo>1.30:raise ValueError(f'{ident}: revise prosody, tempo {tempo:.2f} is too fast')
        filters=f'atempo={tempo:.7f},highpass=f=75,lowpass=f=14500,acompressor=threshold=0.18:ratio=2:attack=15:release=140'
        run([FF,'-y','-v','error','-i',OUT/'audio'/f'{ident}_trim.wav','-af',filters,'-ar',SR,'-ac',2,path])
        data=read(path);rms=float(np.sqrt(np.mean(data**2)));peak=float(np.max(np.abs(data)))
        data*=min(.115/max(rms,1e-6),.69/max(peak,1e-6))
        fade=min(240,len(data)//2);data[:fade]*=np.linspace(0,1,fade)[:,None];data[-fade:]*=np.linspace(1,0,fade)[:,None]
        write(path,data)
        start=round(line['start']*SR);stems[start:start+len(data)]+=data
        result=dict(line,end=round(line['start']+len(data)/SR,3),audio_file=str(path.relative_to(OUT)),
                    provider='VOICEVOX CORE 0.17.0 local CPU',voice_credit=conf['credit'],style_id=sid,
                    tempo_adjustment=tempo,query=dataclasses.asdict(q),wav_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        timed.append(result)
        srt.extend([str(i+1),f"{stamp(result['start'])} --> {stamp(result['end']+.12)}",result['zh_CN'],''])
        print(f"{ident} {conf['credit']} {len(data)/SR:.2f}s / {slot:.2f}s available",flush=True)
    write(OUT/'audio/voice.wav',stems)
    bgm=read(SOURCE/'audio/bgm_original.wav');rain=read(SOURCE/'audio/rain_original.wav')
    duck=np.ones(len(stems),np.float32)
    for line in timed:
        lo=max(0,int((line['start']-.15)*SR));hi=min(len(duck),int((line['end']+.25)*SR))
        duck[lo:hi]=.58
        n=min(int(.14*SR),(hi-lo)//2)
        duck[lo:lo+n]=np.linspace(1,.58,n);duck[hi-n:hi]=np.linspace(.58,1,n)
    # A very short, low-level room reflection avoids bone-dry narration.
    reflected=stems.copy();delay=int(.055*SR);reflected[delay:]+=stems[:-delay,::-1]*.035
    mix=reflected+bgm*duck[:,None]*1.1+rain*.85
    mix*=min(1,.90/float(np.max(np.abs(mix))))
    write(OUT/'audio/mix.wav',mix)
    run([FF,'-y','-v','error','-i',OUT/'audio/mix.wav','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-ar',SR,'-ac',2,OUT/'audio/mix_mastered.wav'])
    (OUT/'dialogue_timed.json').write_text(json.dumps(timed,ensure_ascii=False,indent=2)+'\n')
    (OUT/'subtitles/zh-CN.srt').write_text('\n'.join(srt))
    (OUT/'audio/voice_manifest.json').write_text(json.dumps({'voices':VOICES,'count':len(timed),'celebrity_clone':False,'local_only':True,'all_previous_system_voices_replaced':True},ensure_ascii=False,indent=2))
    (OUT/'VOICE_CREDITS.md').write_text('# 日语配音\n\n夏帆：VOICEVOX:雨晴はう\n\n湊：VOICEVOX:玄野武宏\n\n本作使用通用角色合成音色，并非花泽香菜或松冈祯丞本人配音或声音克隆。\n\n传播此成片时请保留片尾署名。音源适用各自条款：\n\n- https://amehau.com/rules/amehare-hau-rule\n- https://www.virvoxproject.com/voicevoxの利用規約\n- https://voicevox.hiroshiba.jp/term/\n')


if __name__=='__main__':main()
