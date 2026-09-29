# 1080p / 30fps 动态插画成片

> 本文描述早期基础渲染器。当前《雨》续作请使用 [v3 本地声音](local-voice.md) 和 [生产流程](production-workflows.md)，不要回退到旧系统语音。

仓库：[Simonxz578/anime-video-skill](https://github.com/Simonxz578/anime-video-skill)。

## 安装依赖

```bash
python -m pip install numpy pillow opencv-python
brew install ffmpeg
```

需要 macOS 的 `say` 和已安装的日语声音（`say -v '?'` 可查询）。默认系统字体 `/System/Library/Fonts/Hiragino Sans GB.ttc`，字体文件不会随仓库分发。其他平台可使用 `--phase render` 合成已经准备好的音频、字幕和图片；内置配音阶段仅支持 macOS。

## 输入

`examples/rain/ch001.json` 是完整的原创 120 秒 manifest：22 句日语原文、对应中文、声线、时间轴、21 段镜头、五音主题动机及 1080×1920 / 30fps 格式。人物姓名的发音统一为「かほ」「みなと」。

先用两张 `references/` 母版生成 8 张新场景图，保存到 `outputs/romance/rain/chapters/ch001/assets/shot01.png` 至 `shot08.png`。场景说明和人物规则见 `examples/rain/art-direction.md`。渲染器不调用图像生成 API，也不会假装能从原始人物立绘自动生成场景。所有场景须经过角色外观检查。

## 运行

```bash
python scripts/render_motion_film.py \
  --manifest examples/rain/ch001.json \
  --project outputs/romance/rain/chapters/ch001 \
  --phase audio
```

在受限执行环境中，macOS 语音服务可能生成空音频。脚本会拦截空文件；需要给本地语音服务访问权限，再重新运行。脚本缓存绑定对白与声线哈希；改文稿后会重新配音。语句轻微超出预定时间槽时，后一句会顺延以保留至少0.4秒停顿，并记录 `requested_start`；若侵入片尾3秒留白，脚本停止。不会截断对白。最终字幕以实测时间为准。

同一命令依次改成 `--phase preview`（6秒）、`--phase render`（完整字幕版及净版）、`--phase qa`。也可以直接 `--phase all`。用 `--font` / `--ffmpeg` 显式指定已有工具路径。

产物：

- `script/dialogue_timed.json`、`dialogue.md`：实测配音时长。
- `subtitles/zh-CN.srt`：逐句精确绑定的中文字幕。
- `audio/voice.wav`、`bgm_original.wav`、`rain_original.wav`、`mix.wav`：分轨和混音。
- `renders/ch001_final.mp4`：中文字幕版；`ch001_clean.mp4`：无文字净版。
- `qa/ffprobe.json`、`technical_checks.json`、`contact_sheet.jpg`：编码、3600帧、120秒、解码和抽帧验证。

输出目录被 Git 忽略；生成的视频与图片不会在普通 `git add` 中误提交。

## 质量边界

成片使用高质量 AI 插画、摄像机推拉、独立前景雨滴、局部水面涟漪、原创五音钢琴合成器与雨声。没有口型同步、逐帧肢体表演或专业声优配音。系统 TTS 的韵律与情绪控制有限；听感、人物一致性和翻译应标记实际检查方式，不能把技术 QA 当作主观质量满分。影片参考图由用户提供，其他使用者须有自己的素材权限；系统声音的使用遵守其系统条款。

主脚本不会自动更新长期剧情状态。确认成片后，调用方应把章节事实、固定声线、主题动机和素材指纹存入系列的 `continuity/`、`audio/`，并将成片复制或链接到 `videos/ch001.mp4`。后续章需要新对白、新角度、新场景素材；同一角色身份可复用。
