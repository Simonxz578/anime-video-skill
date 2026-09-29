#!/usr/bin/env python3
"""Second montage edit: new local character voices and continuous transitions."""
import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
import render_rain_montage as base

OUT=base.ROOT/'outputs/romance/rain/chapters/ch01/act01/refined'
# Fewer cuts, sustained reactions, notebook ownership unchanged.
EDIT=[
 (1.8,6,1.62,1.67,(.52,.76),(.53,.77),'rain','雨声引入'),
 (4.8,1,1.0,1.035,(.5,.5),(.5,.49),'rain','车站与片名'),
 (7,3,1.65,1.72,(.5,.68),(.51,.67),'soft','湊持有笔记本'),
 (10.5,2,1.53,1.63,(.55,.30),(.55,.29),'soft','夏帆认出笔记本'),
 (14.642,3,1.20,1.28,(.5,.43),(.5,.41),'soft','湊回应'),
 (18.8,4,1.05,1.22,(.51,.46),(.53,.43),'soft','递出与接过，连续推近'),
 (20,7,1.62,1.65,(.72,.66),(.73,.65),'soft','夏帆已经持有笔记本'),
 (24.5,7,1.92,1.98,(.23,.35),(.24,.35),'soft','湊解释'),
 (30.5,7,1.63,1.74,(.73,.47),(.74,.45),'soft','夏帆感谢，珍惜画作'),
 (33.5,7,1.94,2.00,(.23,.35),(.24,.35),'soft','湊问起画画'),
 (37.8,2,1.53,1.61,(.55,.30),(.55,.29),'soft','夏帆谈雨中的车站'),
 (39.5,6,1.04,1.07,(.5,.5),(.51,.51),'rain','雨景插入'),
 (42,7,1.94,1.99,(.23,.35),(.24,.35),'soft','疑问与反应'),
 (47.8,7,1.72,1.83,(.74,.46),(.75,.44),'soft','夏帆的叙述与目光'),
 (49,6,1.54,1.57,(.53,.77),(.54,.78),'rain','雨声接续对白'),
 (54.8,7,1.08,1.14,(.5,.5),(.5,.49),'soft','两人开始一起听雨'),
 (58,6,1.56,1.61,(.48,.19),(.50,.18),'rain','屋檐细节'),
 (62,6,1.64,1.70,(.54,.77),(.56,.78),'rain','水面细节'),
 (67,7,1.92,2.00,(.23,.35),(.24,.35),'soft','湊温柔回应'),
 (72,8,1.10,1.17,(.51,.52),(.52,.51),'rain','安静等待'),
 (76,7,1.76,1.84,(.74,.45),(.75,.44),'soft','电车晚点'),
 (81.2,7,1.93,2.01,(.23,.35),(.24,.35),'soft','可以多听一会儿'),
 (85,2,1.62,1.72,(.55,.30),(.55,.29),'soft','夏帆介绍自己'),
 (89,7,1.95,2.03,(.23,.35),(.24,.35),'soft','湊介绍自己'),
 (94,7,1.74,1.83,(.74,.45),(.75,.44),'soft','夏帆询问日常'),
 (98.622,7,1.94,2.02,(.23,.35),(.24,.35),'soft','湊回答'),
 (104,7,1.72,1.82,(.74,.46),(.75,.44),'soft','夏帆谈画材店'),
 (109,7,1.94,2.02,(.23,.35),(.24,.35),'soft','下次再见的期待'),
 (112,7,1.77,1.85,(.74,.45),(.75,.44),'soft','夏帆：明天见'),
 (115,7,1.95,2.01,(.23,.35),(.24,.35),'soft','湊：明天见'),
 (120,8,1.12,1.025,(.51,.52),(.50,.50),'rain','并肩望向列车，片尾'),
]


def ease(x):
    x=float(np.clip(x,0,1))
    return x*x*x*(x*(x*6-15)+10)


class RefinedFilm(base.Film):
    def __init__(self,width=1080,height=1920):
        super().__init__(width,height)
        self.lines=json.loads((OUT/'dialogue_timed.json').read_text())
        self.captions=[self.caption(x['zh_CN']) for x in self.lines]
        credit=Image.new('RGBA',(self.w,round(116*self.scale)))
        d=ImageDraw.Draw(credit)
        for y,text in [(8,'VOICEVOX:雨晴はう'),(51,'VOICEVOX:玄野武宏')]:
            d.text((self.w/2,y*self.scale),text,font=self.font(base.SANS,28),anchor='mt',
                   fill=(235,238,240,245),stroke_width=1,stroke_fill=(10,18,30,220))
        self.credit=np.asarray(credit)

    def state(self,s,t):
        # Overlap handles: neither outgoing nor incoming camera freezes at a cut.
        p=np.clip((t-s['start']+.45)/(s['end']-s['start']+.9),0,1)
        u=ease(p)
        z=math.exp(math.log(s['zoom'][0])*(1-u)+math.log(s['zoom'][1])*u)
        c=np.array(s['centers'][0])*(1-u)+np.array(s['centers'][1])*u
        return np.array([z,*c])

    def raster(self,n,state):
        z,cx,cy=state;im=self.images[n];ih,iw=im.shape[:2]
        ratio=max(self.w/iw,self.h/ih)*z
        cropw,croph=self.w/ratio,self.h/ratio
        left=np.clip(cx*iw-cropw/2,0,iw-cropw);top=np.clip(cy*ih-croph/2,0,ih-croph)
        return cv2.warpAffine(im,np.float32([[ratio,0,-left*ratio],[0,ratio,-top*ratio]]),
            (self.w,self.h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)

    def picture(self,t):
        i=next(i for i,s in enumerate(self.shots) if t<s['end'])
        shot=self.shots[i]
        for right in [i,i+1]:
            if not 0<right<len(self.shots):continue
            a,b=self.shots[right-1:right+1]
            nearby=a['n']==b['n'] and np.linalg.norm(np.array(a['centers'][1])-b['centers'][0])<.22
            duration=.90 if nearby else (.72 if b['transition']=='rain' else .42)
            boundary=b['start'];lo=boundary-duration/2
            if lo<=t<lo+duration:
                u=ease((t-lo)/duration);sa=self.state(a,t);sb=self.state(b,t)
                if nearby:
                    # One coherent image transform, avoiding duplicated eyes / faces.
                    return self.raster(a['n'],sa*(1-u)+sb*u),shot
                return cv2.addWeighted(self.raster(a['n'],sa),1-u,self.raster(b['n'],sb),u,0),shot
        return self.raster(shot['n'],self.state(shot,t)),shot

    def frame(self,t):
        frame,shot=self.picture(t)
        # Subpixel rain moves continuously; avoid integer-coordinate stepping.
        wet=frame.copy()
        for x,y,speed,length in self.drops:
            xx=(x*self.w+t*12*self.scale)%(self.w+40)-20
            yy=(y*self.h+t*(510+speed*400)*self.scale)%(self.h+80)-40
            if self.w*.13<xx<self.w*.9:continue
            p1=(round(xx*16),round(yy*16));p2=(round((xx-2*self.scale)*16),round((yy+(10+length*21)*self.scale)*16))
            cv2.line(wet,p1,p2,(204,212,219),max(1,round(self.scale)),cv2.LINE_AA,shift=4)
        frame=cv2.addWeighted(frame,.92,wet,.08,0)
        fade=min(1,t/.5,(120-t)/1.2)
        if fade<1:frame=(frame*max(0,fade)).astype(np.uint8)
        clean=frame.copy()
        if 1.72<t<4.55:
            alpha=min(1,(t-1.72)/.5,(4.55-t)/.45)
            self.paste(frame,self.opening,0,115*self.scale,alpha)
        if 115<t<119.6:
            alpha=min(1,(t-115)/.8,(119.6-t)/.65)
            self.paste(frame,self.closing,0,140*self.scale,alpha)
            # Credits travel with both deliverables, including the subtitle-free one.
            self.paste(frame,self.credit,0,1675*self.scale,alpha)
            self.paste(clean,self.credit,0,1675*self.scale,alpha)
        for start,end,key in [(81.3,84.6,'female'),(85.2,88.6,'male')]:
            if start<t<end:
                a=ease(min((t-start)/.5,(end-t)/.45,1))
                self.paste(frame,self.names[key],68*self.scale,(137-10*a)*self.scale,a)
        for i,line in enumerate(self.lines):
            if line['start']<=t<line['end']+.12:
                frame=(frame*(1-self.subtitle_shade)).astype(np.uint8)
                tile=self.captions[i];alpha=min(1,(t-line['start'])/.08)
                self.paste(frame,tile,0,self.h*.91-tile.shape[0],alpha)
                break
        return frame,clean


def inspect():
    film=RefinedFilm(540,960)
    times=[3,6,8,12,16,19,22,27,32,36,40,44,51,57,60,64,70,74,78,83,87,91,96,102,107,110,113,117]
    sheet=Image.new('RGB',(270*7,500*4),(15,22,32));d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        f,_=film.frame(t);im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((270,480))
        x=i%7*270;y=i//7*500;sheet.paste(im,(x,y));d.text((x+8,y+482),f'{t}s',fill='white')
    sheet.save(OUT/'qa/contact.jpg')
    (OUT/'edit_manifest.json').write_text(json.dumps({'duration':120,'fps':30,'width':1080,'height':1920,
        'method':'Illustrated detail montage, not continuous character animation','shots':film.shots,
        'voice_manifest':'audio/voice_manifest.json','changes':['47 segments reduced to 31','moving camera through centered dissolves','geometric blends for nearby same-artwork reframing','new local Japanese voices','subtitles retimed','voice credits embedded']},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['inspect','preview','render']);args=parser.parse_args()
    base.EDIT=EDIT;base.OUT=OUT;base.Film=RefinedFilm
    for n in ['renders','qa','audio','subtitles']:(OUT/n).mkdir(parents=True,exist_ok=True)
    if args.phase=='inspect':inspect()
    else:base.render(args.phase=='preview')
