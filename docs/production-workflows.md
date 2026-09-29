# 当前可复用的生产流程

## 能力和边界

| 路径 | 已实现 | 需要的输入 / 限制 |
|---|---|---|
| 第一幕 120 秒混剪 | `render_rain_montage.py`、`refine_rain_film.py`；平滑运动和转场、字幕、原创混音 | 既有第一幕画作及逐句时间轴；1080×1920 / 30fps |
| 第一幕男声 v3 | `repair_rain_male_voice.py`；保留女声、重新生成男声及混音 | 已有 refined 版本及原始音乐/雨声；不重新生成画面 |
| 新场景逐句配音 | `anime-video-voice` / MCP | 本地 VOICEVOX 资源；见 [配音说明](local-voice.md) |
| 雨后合影 30 秒母版 | `build_day2_audio.py` → `build_day2_project.py` → HyperFrames → `finish_day2_video.py` | 11 张批准的关键帧、角色及地点母版；720×1280 / 30fps / 900 帧 |
| 本地生成式人物视频 | ComfyUI CLI/MCP adapter | 已接入，Wan 5B 未通过画面验收；14B / LTX-2.5 未实测 |
| Seedance 交接 | 中文编辑提示词、拆段计划、无字母版 | 本轮没有提交 Seedance 或调用付费视频 API |

这两个已交付作品均为插画导演动画 / 混剪。真实人体连续动作及口型尚未通过验证。策划工具的 `planning_only`、实际 MP4 编码完成、主观画面验收是三个不同状态。

## 30 秒场景复现

本仓库提供脚本及文本示例；生成的画作、视频和语音保留在本地 `outputs/`。新 checkout 必须先准备资产，不能只克隆代码就获得同一视频。

1. 安装 `.[render]`、FFmpeg、VOICEVOX、Node.js。上次验证的 HyperFrames CLI 为 **0.8.81**，GSAP 为 **3.14.2**；上游方法版本见 [六 Skill 记录](upstream-skills.md)。字体默认 macOS，可用 `ANIME_CJK_FONT`、`ANIME_SERIF_FONT`、`ANIME_LABEL_FONT` 指定合法安装的字体路径。
2. 创建 `outputs/romance/rain/day2_photo_demo/`。按 [示例时间轴](../examples/rain/day2/production_timeline.json) 准备 `assets/keyframes/` 内全部 11 张 PNG；使用现有男女母版生成并逐张核对。把统一地点图放在 `assets/location_master.png`，男女母版放在 `assets/references/kaho_master.png`、`minato_master.png`；需要第一幕风格时另备 `act1_style.png`。将示例的 `voice_manifest_v3.json` 复制到 `assets/references/`。
3. 在 `hyperframes/assets/gsap.min.js` 放置通过官方 GSAP npm 包 **gsap@3.14.2** 获得的 `dist/gsap.min.js`。脚本不远程加载动画依赖。用该场景脚本构建，再从项目目录运行已安装的 HyperFrames CLI；渲染参数以 `hyperframes@0.8.81 render --help` 为准，输出设为 `../renders/director_picture_30s.mp4`，30fps、720×1280、30秒。

```bash
# 在仓库根目录，使用装好本地语音依赖的 Python。
python scripts/build_day2_audio.py
python scripts/build_day2_project.py
# 在 outputs/romance/rain/day2_photo_demo/hyperframes 中先 check，再 render。
# 渲染后回仓库根目录：
python scripts/finish_day2_video.py
```

`build_day2_audio.py` 固定八句日语对白、中文翻译、时隙和声音参数；超过时隙就失败。生成男女分轨、对白、72BPM 五音原创音乐、环境拟音、最终混音、SRT/ASS。快门在 12.1 和 29.5 秒。

画面构建脚本检查关键帧和 GSAP 是否齐备，再生成 HTML 分镜和时间轴。仅做小幅画面推进，最后 29.5–29.9 秒双人自拍定格，末尾三帧黑场，无标题结尾卡。

finishing 脚本输出无字幕母版及中文字幕预览，复用同一条 AAC 音轨。检查分辨率、900帧、30fps、时长、编码、完整解码和音轨一致性，并从实际编码视频抽取联系表。最后需检查人物身份、镜头衔接、字幕含义及配音听感。代码检查不能替代听看验收。

## 第一幕版本继承

- `render_motion_film.py` 是早期基础渲染器，历史上使用系统语音。
- `redub_rain.py` 是 v2 全量换声的历史脚本，男声参数已被 v3 取代。续作使用 `local_voice.py` 和 `build_day2_audio.py` 的 v3 预设。
- `refine_rain_film.py` 生成 31 段连续转场的画面。`repair_rain_male_voice.py` 仅重建男声及混音，输出到 `chapters/ch01/act01/male_voice_v3/`。
- 复用 refined 的无字幕画面，搭配 v3 `audio/mix_mastered.wav` 重新封装；中文字幕应使用 v3 `subtitles/zh-CN.srt`，不能保留旧时长字幕。女声逐句 hash 应保持一致。

[持续制作约定](rain-production-preferences.md) 保存《雨》的方向与最新版本。其他系列应建立自己的配音、角色和时长约定。
