#!/usr/bin/env python3
"""Build the locked 900-frame director animatic and production handoff."""
import json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/romance/rain/day2_photo_demo'
HF=OUT/'hyperframes'
SHOTS=[
 ('S01',0,120,'S01_walk.png','并排沿湿润街道走近；朋友距离',1.0,1.025),
 ('S02',120,240,'S02_puddle.png','两人看向水洼中的天空倒影',1.015,1.04),
 ('S03_start',240,310,'S03_camera_low.png','相机仍在胸前，湊回答',1.0,1.018),
 ('S03_end',310,363,'S03_camera_up.png','相机举到眼前，对准夏帆',1.018,1.025),
 ('S04',363,480,'S04_turn.png','12.10秒快门，夏帆回头',1.0,1.025),
 ('S05',480,630,'S05_show.png','湊放低相机，把后屏转向夏帆',1.0,1.027),
 ('S06_insert',630,666,'S06_insert.png','后屏中特写：夏帆暖光侧脸',1.0,1.015),
 ('S06_reaction',666,750,'S06_reaction.png','夏帆满意，湊观察她的反应',1.01,1.026),
 ('S07_start',750,789,'S07_start.png','从看相机到抬头，提议合影',1.0,1.01),
 ('S07_end',789,840,'S07_phone_up.png','夏帆举起手机前上方，双人进入自拍构图',1.0,1.015),
 ('S08',840,897,'S08_selfie.png','两人同时看手机镜头微笑；29.5–29.9秒hold',1.0,1.016),
]

def main():
 missing=[f for _,_,_,f,*_ in SHOTS if not (OUT/'assets/keyframes'/f).is_file()]
 if missing:raise FileNotFoundError('Prepare approved keyframes before building: '+', '.join(missing))
 if not (HF/'assets/gsap.min.js').is_file():raise FileNotFoundError('Place GSAP 3.14.2 at hyperframes/assets/gsap.min.js; see docs/production-workflows.md')
 HF.mkdir(parents=True,exist_ok=True)
 timeline=dict(title='雨后天晴合影',kind='illustrated reference animatic',width=720,height=1280,fps=30,duration=30,total_frames=900,
  identity_references=['assets/references/kaho_master.png','assets/references/minato_master.png'],location='assets/location_master.png',
  shots=[dict(id=id,start_frame=a,end_frame_exclusive=b,start=a/30,end=b/30,keyframe='assets/keyframes/'+f,action=action,scale_start=s0,scale_end=s1,transition='cut') for id,a,b,f,action,s0,s1 in SHOTS],
  black_frames=[897,900],shutters=[12.1,29.5],final_photo_hold=[29.5,29.9],
  dialogue=json.loads((OUT/'audio/dialogue_timed.json').read_text()),audio='audio/final_original_mix.wav',
  motion_note='Only gentle editorial push on still keyframes. Body animation and lipsync remain for Seedance; never claimed as generated continuous animation.')
 (OUT/'production_timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
 (HF/'BRIEF.md').write_text('---\nworkflow: general-video\nflow: automation\nstoryboard: no\nmessage: 雨停后的第二天，从看照片到第一次双人自拍\naspect: 720x1280\nlanguage: ja\nlength: 30s\n---\n\n## Intent\n用户已锁定八段对白及镜头，授权直接完成渲染。沿用第一幕身份、服装、声线与五音主题。\n\n## Assets\n母版、11张关键帧、48kHz本地配音与原创混音由上一级项目提供。\n\n## Notes\n仅导演参考animatic。禁止字幕进入无字母版，禁止标题结尾卡。无付费视频API；不提交Seedance。\n')
 (HF/'frame.md').write_text('# Design truth\n\n保持用户角色母版和统一街道原貌：海军蓝服装、蓝瞳、暖金阳光、雨蓝阴影。左树/红砖铁栏，右奶油墙/鼠尾草绿篷。\n\n人物表情与相机/手机是焦点；画面全幅，不加装饰图形。字幕仅在最终预览压制，沿用白字细暗描边。\n\n只允许1–4%的缓慢推进，所有动作通过清楚的前后关键帧呈现。无假口型/插值变脸。最后双人自拍持0.4秒，随后0.1秒黑场。\n')
 (HF/'compositions').mkdir(exist_ok=True)
 (HF/'assets/keyframes').mkdir(parents=True,exist_ok=True)
 board='---\nmode: autonomous\n---\n\n# Locked storyboard\n'
 mounts=[]
 for id,a,b,f,action,s0,s1 in SHOTS:
  duration=(b-a)/30;move_duration=(885-a)/30 if id=='S08' else duration
  board+=f'\n## Frame {id}\nstatus: animated\nsrc: compositions/{id}.html\nrule: coordinate-target-zoom (bounded central push)\n{a/30:.3f}–{b/30:.3f}s — {action}\n'
  src=OUT/'assets/keyframes'/f
  if src.exists():shutil.copy2(src,HF/'assets/keyframes'/f)
  html=f'''<!doctype html><html><head><meta charset="utf-8"></head><body><template>
<style>#root{{position:absolute;inset:0;width:100%;height:100%;overflow:hidden;background:#000}} .plate{{display:block;width:100%;height:100%;object-fit:cover;will-change:transform}}</style>
<div id="root" data-composition-id="{id}" data-width="720" data-height="1280" data-duration="{duration}"><img id="plate-{id}" class="plate" src="assets/keyframes/{f}" alt="{action}" data-layout-allow-overflow></div>
<script>const tl=gsap.timeline({{paused:true}});tl.fromTo('#plate-{id}',{{scale:{s0}}},{{scale:{s1},duration:{move_duration},ease:'none'}},0);window.__timelines['{id}']=tl;</script>
</template></body></html>'''
  (HF/'compositions'/f'{id}.html').write_text(html)
  mounts.append(f'<section class="clip" id="mount-{id}" data-composition-id="{id}" data-composition-src="compositions/{id}.html" data-start="{a/30}" data-duration="{duration}" data-track-index="0" data-width="720" data-height="1280"></section>')
 # Last 3 frames intentionally black, timeline length still exactly 30.
 (HF/'STORYBOARD.md').write_text(board)
 (HF/'index.html').write_text('''<!doctype html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=720,height=1280"><title>Rain day2 director reference</title><script src="assets/gsap.min.js"></script><style>html,body{margin:0;width:100%;height:100%;background:#000}#root{position:relative;width:100%;height:100%;overflow:hidden}.clip{position:absolute;inset:0;width:100%;height:100%}</style></head><body><div id="root" data-composition-id="rain-day2" data-width="720" data-height="1280" data-duration="30">'''+''.join(mounts)+'''<section class="clip" id="cut-black" data-start="29.9" data-duration="0.1" data-track-index="0" style="background:#000"></section></div><script>const tl=gsap.timeline({paused:true});window.__timelines['rain-day2']=tl;</script></body></html>''')
 screenplay='# 《雨》雨后天晴合影 · 30秒锁定剧本\n\n第二天下午，雨停后的车站街道。服装与第一幕相同；轻松朋友距离。\n\n'
 for id,a,b,f,action,s0,s1 in SHOTS:screenplay+=f'- **{a/30:.2f}–{b/30:.2f}s {id}**：{action}。\n'
 screenplay+='\n## 锁定对白\n\n'
 for l in timeline['dialogue']:screenplay+=f"- {l['start']:.2f}–{l['end']:.2f}s {'夏帆' if l['speaker']=='female' else '湊'}：{l['ja']}\n  {l['zh_CN']}\n"
 screenplay+='\n音乐保留D–F♯–A–E–C♯五音主题，72 BPM；对白优先，远处电车与偶尔滴水，两次快门。最后0.4秒hold，然后切黑，无片名。\n'
 (OUT/'screenplay_30s.md').write_text(screenplay)
 print('PROJECT_READY; missing=',[f for _,_,_,f,*_ in SHOTS if not (OUT/'assets/keyframes'/f).exists()])

if __name__=='__main__':main()
