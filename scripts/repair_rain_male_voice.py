#!/usr/bin/env python3
"""Repair only Minato's prosody; retain Kaho's exact approved WAV files."""
import dataclasses
import hashlib
import json
import shutil
import os
from pathlib import Path

import numpy as np
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
from redub_rain import ROOT, RUNTIME, SOURCE, FF, SR, read, write, run, stamp

PREVIOUS=ROOT/'outputs/romance/rain/chapters/ch01/act01/refined'
OUT=ROOT/'outputs/romance/rain/chapters/ch01/act01/male_voice_v3'
# Only punctuation changes. No words, meanings or Chinese translations changed.
SPOKEN={
    'L002':'よかった、ベンチに置いてあったから。',
    'L004':'濡れそうだったから預かってました。',
    'L006':'絵を描くんですね。',
    'L008':'つもり？',
    'L010':'わかります。ここ雨の音が近いですよね。',
    'L012':'ほんとだ。言われるまで気づかなかった。',
    'L014':'じゃあもう少し聞いていられますね。',
    'L016':'僕はみなとです。',
    'L018':'うん、だいたい。かほさんも？',
    'L020':'じゃあまた会えるかもしれませんね。',
    'L022':'また明日。',
}


def silence_spans(data):
    mono=data.mean(axis=1);n=int(.01*SR)
    rms=np.sqrt(np.mean(mono[:len(mono)//n*n].reshape(-1,n)**2,axis=1))
    flags=rms<.002;spans=[];start=None
    for i,quiet in enumerate(flags):
        if quiet and start is None:start=i
        if not quiet and start is not None:
            if i-start>=18 and start>3:spans.append({'start':round(start*.01,2),'duration':round((i-start)*.01,2)})
            start=None
    return spans


def main():
    for folder in ['audio','renders','qa','subtitles']:(OUT/folder).mkdir(parents=True,exist_ok=True)
    s=Synthesizer(Onnxruntime.load_once(filename=(os.environ.get('VOICEVOX_ONNXRUNTIME') or str(RUNTIME/'onnxruntime/lib/libvoicevox_onnxruntime.1.17.3.dylib'))),
        OpenJtalk(RUNTIME/'dict/open_jtalk_dic_utf_8-1.11'),acceleration_mode='CPU',cpu_num_threads=4)
    with VoiceModelFile.open(RUNTIME/'models/vvms/4.vvm') as model:s.load_voice_model(model)
    lines=json.loads((PREVIOUS/'dialogue_timed.json').read_text())
    voices=np.zeros((120*SR,2),np.float32);female=np.zeros_like(voices);male=np.zeros_like(voices)
    timed=[];checks=[];srt=[]
    for i,line in enumerate(lines):
        line=dict(line);ident=line['line_id'];path=OUT/'audio'/f'{ident}.wav'
        old=read(PREVIOUS/line['audio_file'])
        if line['speaker']=='female':
            shutil.copy2(PREVIOUS/line['audio_file'],path)
            data=read(path)
            assert path.read_bytes()==(PREVIOUS/line['audio_file']).read_bytes()
        else:
            q=s.create_audio_query(SPOKEN[ident],11)
            q.speed_scale=.94
            q.pitch_scale=0.0
            q.intonation_scale=1.0
            q.pre_phoneme_length=.07;q.post_phoneme_length=.13
            q.output_sampling_rate=24000;q.output_stereo=False
            # Preserve the model's intra-phrase contours. Only punctuation pauses
            # are bounded; no phonemes are removed or cut from synthesized speech.
            for phrase in q.accent_phrases:
                if phrase.pause_mora:
                    pause=phrase.pause_mora
                    if isinstance(pause,dict):pause['vowel_length']=min(.15,pause['vowel_length'])
                    else:pause.vowel_length=min(.15,pause.vowel_length)
            raw=OUT/'audio'/f'{ident}_native24.wav'
            raw.write_bytes(s.synthesis(q,11))
            # Native-rate synthesis followed by bandlimited resampling. No atempo,
            # pitch shift, per-phoneme stitching, or silence removal after synthesis.
            run([FF,'-v','error','-y','-i',raw,'-af',
                 'aresample=48000:filter_size=64:phase_shift=10:cutoff=0.97,highpass=f=60,lowpass=f=11500',
                 '-ar',SR,'-ac',2,path])
            data=read(path)
            rms=float(np.sqrt(np.mean(data**2)));peak=float(np.max(np.abs(data)))
            data*=min(.105/max(rms,1e-6),.65/max(peak,1e-6))
            n=min(240,len(data)//2);data[:n]*=np.linspace(0,1,n)[:,None];data[-n:]*=np.linspace(1,0,n)[:,None]
            write(path,data)
            oldspans=silence_spans(old);newspans=silence_spans(data)
            checks.append({'line':ident,'previous_duration':len(old)/SR,'new_duration':len(data)/SR,
                'old_internal_pauses_ge180ms':oldspans,'new_internal_pauses_ge180ms':newspans,
                'spoken':SPOKEN[ident],'waveform_replaced':path.read_bytes()!=(PREVIOUS/line['audio_file']).read_bytes()})
            line.update(query=dataclasses.asdict(q),spoken_text=SPOKEN[ident],tempo_adjustment=1.0,
                        voice_revision='native tone / continuous sentence / punctuation pause repair')
        slot=(lines[i+1]['start']-.24 if i+1<len(lines) else 115)-line['start']
        assert len(data)/SR<slot, (ident,len(data)/SR,slot)
        lo=round(line['start']*SR);hi=lo+len(data);voices[lo:hi]+=data
        (male if line['speaker']=='male' else female)[lo:hi]+=data
        line.update(end=round(line['start']+len(data)/SR,3),audio_file=str(path.relative_to(OUT)),
                    wav_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        timed.append(line)
        srt.extend([str(i+1),f"{stamp(line['start'])} --> {stamp(line['end']+.12)}",line['zh_CN'],''])
        print(ident,line['speaker'],round(len(data)/SR,3),flush=True)
    write(OUT/'audio/voice.wav',voices);write(OUT/'audio/female_ja.wav',female);write(OUT/'audio/male_ja.wav',male)
    duck=np.ones(len(voices),np.float32)
    for line in timed:
        lo=max(0,int((line['start']-.15)*SR));hi=min(len(duck),int((line['end']+.25)*SR))
        duck[lo:hi]=.58;n=min(int(.14*SR),(hi-lo)//2)
        duck[lo:lo+n]=np.linspace(1,.58,n);duck[hi-n:hi]=np.linspace(.58,1,n)
    # Retain Kaho's previous subtle reflection. Keep Minato direct and clear.
    reflected=voices.copy();delay=int(.055*SR);reflected[delay:]+=female[:-delay,::-1]*.035
    mix=reflected+read(SOURCE/'audio/bgm_original.wav')*duck[:,None]*1.1+read(SOURCE/'audio/rain_original.wav')*.85
    mix*=min(1,.90/float(np.max(np.abs(mix))))
    write(OUT/'audio/mix.wav',mix)
    run([FF,'-v','error','-y','-i',OUT/'audio/mix.wav','-af','loudnorm=I=-16:TP=-1.5:LRA=9','-ar',SR,'-ac',2,OUT/'audio/mix_mastered.wav'])
    (OUT/'dialogue_timed.json').write_text(json.dumps(timed,ensure_ascii=False,indent=2)+'\n')
    (OUT/'subtitles/zh-CN.srt').write_text('\n'.join(srt))
    manifest=json.loads((PREVIOUS/'audio/voice_manifest.json').read_text())
    manifest['voices']['male'].update(pitch=0.0,speed=.94,intonation=1.0,pause_max_seconds=.15,
        native_sample_rate=24000,postprocess='64-tap SWR resampling, gentle EQ; no time stretch or pitch shift')
    manifest.update(revision='male_voice_v3',female_source='refined/audio/*.wav, byte-for-byte copied',male_lines_regenerated=11)
    (OUT/'audio/voice_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    (OUT/'qa/voice_repair.json').write_text(json.dumps({'female_unchanged':True,'male_count':len(checks),
        'human_listening_review':False,'checks':checks},ensure_ascii=False,indent=2))
    shutil.copy2(PREVIOUS/'VOICE_CREDITS.md',OUT/'VOICE_CREDITS.md')


if __name__=='__main__':main()
