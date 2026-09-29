#!/usr/bin/env python3
"""The user's approved detail-montage edition of Rain / Chapter 1 / Act 1.

Uses existing character artwork and dialogue. Camera motion and montage are
intentional; this does not claim generated character animation or lip sync.
"""
import argparse
import json
import math
import subprocess
import time
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/romance/rain/chapters/ch001'
OUT = ROOT / 'outputs/romance/rain/chapters/ch01/act01/montage'
FFMPEG = os.environ.get('FFMPEG_BIN', 'ffmpeg')
SANS = os.environ.get('ANIME_CJK_FONT', '/System/Library/Fonts/Hiragino Sans GB.ttc')
SERIF = os.environ.get('ANIME_SERIF_FONT', '/System/Library/Fonts/Supplemental/Songti.ttc')
# End, artwork, start/end zoom, start/end center, transition, narrative purpose.
EDIT = [
 (1.6,6,1.75,1.88,(.52,.76),(.54,.78),'cut','雨滴与倒影，引入雨声'),
 (4.6,1,1.0,1.04,(.5,.5),(.5,.49),'dissolve','车站建立镜头与片名'),
 (7,3,1.75,1.90,(.5,.69),(.51,.67),'cut','湊手里的笔记本'),
 (9.4,2,1.5,1.6,(.55,.31),(.56,.30),'cut','夏帆认出笔记本'),
 (10.5,2,2.15,2.2,(.54,.25),(.56,.25),'cut','眼神特写'),
 (12.7,3,1.18,1.24,(.5,.43),(.5,.40),'cut','湊回应'),
 (14.5,3,1.70,1.8,(.51,.66),(.51,.65),'cut','持本细节'),
 (16.5,4,1.03,1.1,(.5,.49),(.51,.46),'cut','递本：男左女右'),
 (17.9,4,1.60,1.7,(.53,.38),(.57,.38),'cut','同一本笔记本，交接特写'),
 (20,7,1.65,1.72,(.73,.67),(.74,.64),'dissolve','夏帆已独自抱住笔记本'),
 (22.4,7,1.95,2.03,(.23,.35),(.24,.35),'cut','湊解释，书已归还'),
 (24.5,7,1.1,1.04,(.5,.5),(.5,.5),'cut','双人反应'),
 (27,7,1.6,1.65,(.72,.63),(.73,.60),'cut','夏帆珍惜笔记本'),
 (30.5,7,1.78,1.88,(.75,.46),(.76,.44),'cut','抬眼与笑意'),
 (33.5,7,2.0,2.07,(.22,.35),(.24,.36),'cut','湊询问画画'),
 (36.6,2,1.55,1.66,(.55,.30),(.54,.29),'cut','夏帆解释'),
 (39.5,6,1.0,1.07,(.5,.5),(.52,.52),'dissolve','雨中的车站，画外对白'),
 (42,7,2.05,2.14,(.22,.35),(.24,.35),'cut','本来？反应特写'),
 (45.6,7,1.8,1.9,(.75,.46),(.76,.44),'cut','夏帆讲起看雨'),
 (49,6,1.62,1.72,(.56,.78),(.60,.79),'dissolve','水面与暖光'),
 (51.7,7,1.05,1.10,(.49,.49),(.48,.48),'cut','两人开始留意雨声'),
 (54.8,7,1.92,2.0,(.24,.36),(.25,.35),'cut','湊的目光'),
 (57.2,6,1.65,1.75,(.48,.17),(.50,.16),'cut','屋檐上的雨声'),
 (60.2,6,1.7,1.8,(.54,.80),(.58,.81),'cut','地面上的涟漪'),
 (62,7,1.96,2.04,(.76,.44),(.76,.43),'dissolve','夏帆安静地听雨'),
 (65,7,1.96,2.03,(.23,.35),(.24,.36),'cut','湊的回应'),
 (68,7,1.03,1.0,(.5,.5),(.5,.5),'cut','双人停顿'),
 (70,6,1.85,1.96,(.50,.79),(.54,.80),'dissolve','雨滴留白'),
 (72,8,1.15,1.20,(.52,.53),(.52,.52),'dissolve','车站与等待'),
 (74.7,7,1.85,1.92,(.75,.45),(.76,.44),'cut','电车晚点五分钟'),
 (76,6,1.1,1.16,(.5,.48),(.52,.48),'cut','雨声连接两人'),
 (79.8,7,1.93,2.01,(.23,.35),(.24,.35),'cut','能再听一会儿'),
 (81.2,7,1.08,1.12,(.5,.5),(.51,.5),'cut','准备互相介绍'),
 (85,2,1.65,1.78,(.55,.30),(.55,.28),'cut','夏帆，姓名字幕'),
 (89,7,1.98,2.10,(.23,.35),(.24,.34),'cut','湊，姓名字幕'),
 (91.8,7,1.80,1.90,(.75,.45),(.76,.43),'cut','夏帆询问日常'),
 (94,7,1.08,1.14,(.5,.5),(.51,.49),'cut','关系拉近'),
 (96.6,7,1.96,2.04,(.23,.35),(.24,.34),'cut','湊回答'),
 (98.6,6,1.75,1.85,(.48,.77),(.52,.79),'dissolve','雨声中的短暂停顿'),
 (101.4,7,1.8,1.9,(.75,.45),(.76,.44),'cut','夏帆谈起画材店'),
 (104,7,1.65,1.73,(.72,.67),(.73,.65),'cut','笔记本与新的日常'),
 (106.8,7,1.95,2.03,(.23,.35),(.24,.34),'cut','也许还能再见'),
 (109,7,1.07,1.0,(.5,.5),(.5,.5),'dissolve','双人约定'),
 (111.1,7,1.85,1.96,(.75,.45),(.76,.43),'cut','夏帆：明天见'),
 (114,7,1.99,2.08,(.23,.35),(.24,.34),'cut','湊：明天见'),
 (117.2,8,1.15,1.06,(.52,.53),(.50,.51),'dissolve','两人并肩望向列车'),
 (120,8,1.06,1.0,(.50,.51),(.50,.50),'continuous','结尾：雨与明日'),
]

class Film:
    def __init__(self,width=1080,height=1920):
        self.w,self.h,self.scale=width,height,width/1080
        self.images={n:cv2.imread(str(SOURCE/f'assets/shot{n:02}.png')) for n in range(1,9)}
        self.lines=json.loads((SOURCE/'script/dialogue_timed.json').read_text())
        self.shots=[];start=0
        for end,n,z0,z1,c0,c1,transition,purpose in EDIT:
            self.shots.append(dict(start=start,end=end,asset=f'shot{n:02}.png',n=n,zoom=[z0,z1],centers=[c0,c1],transition=transition,purpose=purpose))
            start=end
        self.captions=[self.caption(x['zh_CN']) for x in self.lines]
        self.opening=self.card('雨','第一章节','第一幕 · 初见',True)
        self.closing=self.card('また、明日。','第一幕 · 初见  完','明天，同一班车。',False)
        self.names={"female":self.namecard('夏 帆','K A H O'),"male":self.namecard('湊','M I N A T O')}
        self.rng=np.random.default_rng(27092026)
        self.drops=self.rng.uniform(0,1,(80,4))
        self.subtitle_shade=np.zeros((self.h,self.w,1),np.float32)
        y0=round(self.h*.77)
        self.subtitle_shade[y0:,:,0]=np.linspace(0,.27,self.h-y0)[:,None]

    def font(self,path,size):return ImageFont.truetype(path,max(12,round(size*self.scale)))
    def caption(self,text):
        f=self.font(SANS,48);maxw=self.w*.83;lines=['']
        if f.getlength(text)>maxw:
            candidates=[i+1 for i,c in enumerate(text[:-1]) if c in '，。；' and f.getlength(text[:i+1])<=maxw and f.getlength(text[i+1:])<=maxw]
            if candidates:
                split=min(candidates,key=lambda i:abs(f.getlength(text[:i])-f.getlength(text[i:])))
                lines=[text[:split],text[split:]]
            else:
                for c in text:
                    if f.getlength(lines[-1]+c)>maxw:lines.append(c)
                    else:lines[-1]+=c
        else:lines=[text]
        if len(lines)>2:raise ValueError(text)
        h=round((30+len(lines)*66)*self.scale)
        im=Image.new('RGBA',(self.w,h));d=ImageDraw.Draw(im)
        for i,line in enumerate(lines):
            d.text((self.w/2,round((12+i*66)*self.scale)),line,font=f,anchor='mt',fill=(248,248,244,255),stroke_width=max(1,round(2*self.scale)),stroke_fill=(8,14,25,225))
        return np.asarray(im)

    def card(self,hero,eyebrow,detail,opening):
        im=Image.new('RGBA',(self.w,round(420*self.scale)));d=ImageDraw.Draw(im)
        x=self.w/2
        d.text((x,18*self.scale),eyebrow,font=self.font(SANS,28),anchor='mt',fill=(223,233,239,245),stroke_width=1,stroke_fill=(10,20,35,130))
        d.text((x,75*self.scale),hero,font=self.font(SERIF,180 if opening else 78),anchor='mt',fill=(249,248,238,255),stroke_width=1,stroke_fill=(20,30,40,80))
        y=(286 if opening else 208)*self.scale
        d.line((x-50*self.scale,y,x+50*self.scale,y),fill=(229,219,190,230),width=max(1,round(self.scale)))
        d.text((x,y+30*self.scale),detail,font=self.font(SANS,35),anchor='mt',fill=(239,242,240,255),stroke_width=1,stroke_fill=(12,24,35,150))
        return np.asarray(im)

    def namecard(self,name,latin):
        im=Image.new('RGBA',(round(390*self.scale),round(160*self.scale)));d=ImageDraw.Draw(im)
        d.line((5*self.scale,12*self.scale,5*self.scale,125*self.scale),fill=(231,217,183,240),width=max(1,round(2*self.scale)))
        d.text((28*self.scale,4*self.scale),name,font=self.font(SERIF,64),fill=(249,246,234,255),stroke_width=1,stroke_fill=(15,25,45,160))
        d.text((32*self.scale,100*self.scale),latin,font=self.font(SANS,21),fill=(219,230,239,245))
        return np.asarray(im)

    def paste(self,frame,tile,x,y,alpha=1):
        x,y=round(x),round(y);h,w=tile.shape[:2]
        a=tile[:,:,3:4].astype(np.float32)*(max(0,min(1,alpha))/255)
        frame[y:y+h,x:x+w]=(frame[y:y+h,x:x+w]*(1-a)+tile[:,:,:3][:,:,::-1]*a).astype(np.uint8)

    def camera(self,shot,t):
        p=np.clip((t-shot['start'])/(shot['end']-shot['start']),0,1)
        u=p*p*(3-2*p)
        z=shot['zoom'][0]*(1-u)+shot['zoom'][1]*u
        cx=shot['centers'][0][0]*(1-u)+shot['centers'][1][0]*u
        cy=shot['centers'][0][1]*(1-u)+shot['centers'][1][1]*u
        im=self.images[shot['n']];ih,iw=im.shape[:2]
        ratio=max(self.w/iw,self.h/ih)*z
        cropw,croph=self.w/ratio,self.h/ratio
        left=np.clip(cx*iw-cropw/2,0,iw-cropw);top=np.clip(cy*ih-croph/2,0,ih-croph)
        matrix=np.float32([[ratio,0,-left*ratio],[0,ratio,-top*ratio]])
        return cv2.warpAffine(im,matrix,(self.w,self.h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)

    def frame(self,t):
        ix=next(i for i,s in enumerate(self.shots) if t<s['end'])
        shot=self.shots[ix];frame=self.camera(shot,t)
        dt=t-shot['start']
        if ix and shot['transition']=='dissolve' and dt<.30:
            a=dt/.30;a=a*a*(3-2*a)
            frame=cv2.addWeighted(self.camera(self.shots[ix-1],shot['start']),1-a,frame,a,0)
        wet=frame.copy()
        for x,y,speed,length in self.drops:
            xx=(x*self.w+t*17*self.scale)%(self.w+40)-20
            yy=(y*self.h+t*(630+speed*600)*self.scale)%(self.h+80)-40
            if shot['n']!=6 and self.w*.13<xx<self.w*.9:continue
            cv2.line(wet,(round(xx),round(yy)),(round(xx-3*self.scale),round(yy+(10+length*25)*self.scale)),(207,211,217),max(1,round(self.scale)),cv2.LINE_AA)
        frame=cv2.addWeighted(frame,.88,wet,.12,0)
        fade=min(1,t/.32,(120-t)/.9)
        if fade<1:frame=(frame*max(0,fade)).astype(np.uint8)
        clean=frame.copy()
        if 1.72<t<4.55:
            alpha=min(1,(t-1.72)/.4,(4.55-t)/.38)
            self.paste(frame,self.opening,0,115*self.scale,alpha)
        if 115<t<119.6:
            alpha=min(1,(t-115)/.8,(119.6-t)/.65)
            self.paste(frame,self.closing,0,140*self.scale,alpha)
        for start,end,key in [(81.3,84.6,'female'),(85.2,88.6,'male')]:
            if start<t<end:
                a=min(1,(t-start)/.4,(end-t)/.35)
                self.paste(frame,self.names[key],68*self.scale,(137-12*a)*self.scale,a)
        for i,line in enumerate(self.lines):
            if line['start']<=t<line['end']+.2:
                frame=(frame*(1-self.subtitle_shade)).astype(np.uint8)
                tile=self.captions[i]
                self.paste(frame,tile,0,self.h*.91-tile.shape[0])
                break
        return frame,clean

def prepare():
    for n in ['renders','qa','audio','subtitles']: (OUT/n).mkdir(parents=True,exist_ok=True)
    # Reuse the exact, already measured Japanese performances and original score.
    subprocess.run([FFMPEG,'-v','error','-y','-i',str(SOURCE/'audio/mix.wav'),'-af',
        'highpass=f=55,loudnorm=I=-16:TP=-1.5:LRA=9','-ar','48000','-ac','2',str(OUT/'audio/mix_mastered.wav')],check=True)
    (OUT/'subtitles/zh-CN.srt').write_bytes((SOURCE/'subtitles/zh-CN.srt').read_bytes())

def inspect():
    film=Film(540,960)
    times=[.8,3.0,5.6,8.1,10,11.5,13.6,15.6,17.1,18.8,21.4,25.9,29,35,43.5,50.5,56,63.5,73,78,82,86,99.7,105.4,110,113,116.3,118.5]
    sheet=Image.new('RGB',(270*7,500*4),(15,22,32));d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        f,_=film.frame(t)
        cv2.imwrite(str(OUT/'qa'/f'preview_{t:05.1f}.jpg'),f)
        thumb=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((270,480))
        x=i%7*270;y=i//7*500;sheet.paste(thumb,(x,y));d.text((x+8,y+482),f'{t:.1f}s',fill='white')
    sheet.save(OUT/'qa/montage_contact.jpg')
    manifest={'title':'雨','chapter':1,'act':1,'act_title':'初见','duration':120,'width':1080,'height':1920,'fps':30,
        'method':'User-authorized detail montage: reference artwork, reframing, camera motion, cuts, dissolves and rain; no lip-sync or full-character-animation claim.',
        'authorization':'2026-09-28 user explicitly accepted enlarged-detail montage if local video generation remains unstable.',
        'shots':film.shots,'dialogue':film.lines,'references':['references/female_lead_master.png','references/male_lead_master.png']}
    (OUT/'edit_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

def render(preview=False):
    film=Film(540,960) if preview else Film()
    duration=20 if preview else 120
    names=['preview.mp4'] if preview else ['rain_ch01_act01_final.mp4','rain_ch01_act01_clean.mp4']
    procs=[]
    for name in names:
        target=OUT/'renders'/name
        cmd=[FFMPEG,'-y','-v','warning','-f','rawvideo','-pixel_format','bgr24','-video_size',f'{film.w}x{film.h}','-framerate','30','-i','pipe:0',
            '-i',str(OUT/'audio/mix_mastered.wav'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','18','-threads','3',
            '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-t',str(duration),'-movflags','+faststart',str(target)]
        procs.append(subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=open(target.with_suffix('.log'),'w')))
    began=time.monotonic()
    try:
        for f in range(duration*30):
            final,clean=film.frame(f/30)
            procs[0].stdin.write(final.tobytes())
            if len(procs)>1:procs[1].stdin.write(clean.tobytes())
            if f%150==0:print(f'Render {f}/{duration*30}; {f/max(1,time.monotonic()-began):.1f} fps',flush=True)
    finally:
        for p in procs:p.stdin.close()
        codes=[p.wait() for p in procs]
    if any(codes):raise RuntimeError(codes)
    print('RENDER COMPLETE',time.monotonic()-began,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','inspect','preview','render'])
    a=parser.parse_args()
    {'prepare':prepare,'inspect':inspect,'preview':lambda:render(True),'render':render}[a.phase]()
