# 本地日语配音（Rain v3）

当前采用 **VOICEVOX Core 0.17.0 CPU**。新增 CLI 和 MCP 工具可直接生成逐句 WAV；不依赖云端语音服务，不做真人声纹克隆。

## 安装和检查

使用 Python 3.10+，本项目实际验证环境为 macOS arm64 / Python 3.12。先按 [VOICEVOX 官方说明](https://github.com/VOICEVOX/voicevox_core) 获取 [0.17.0 发布版](https://github.com/VOICEVOX/voicevox_core/releases/tag/0.17.0) 中匹配平台的 Python wheel、VOICEVOX ONNX Runtime、Open JTalk 字典及模型。安装模型前阅读各音色条款。不要把这些二进制提交到 Git。

```bash
python3.12 -m venv outputs/local-voice-provider/venv
source outputs/local-voice-provider/venv/bin/activate
python -m pip install -e '.[mcp,render]'
# 将下面的路径替换为实际下载的匹配平台 wheel。
python -m pip install /path/to/voicevox_core-0.17.0-platform.whl
```

默认资源布局（也可用 `VOICEVOX_RUNTIME` 指向其他目录）：

```text
outputs/local-voice-provider/runtime/
  onnxruntime/lib/<matching voicevox_onnxruntime library>
  dict/open_jtalk_dic_utf_8-1.11/sys.dic
  models/vvms/0.vvm
  models/vvms/4.vvm
```

FFmpeg 必须在 PATH 中，或设置 `FFMPEG_BIN`。新语音模块自动查找 native library；无法找到时设置 `VOICEVOX_ONNXRUNTIME` 为完整文件路径。生产历史脚本的默认库名是 macOS 1.17.3 dylib，在其他平台必须设置这个变量。`.env.example` 仅为模板，程序不会自动载入 `.env`。

```bash
anime-video-voice health
anime-video-voice synthesize --speaker male \
  --text 'だから、撮りたくなるんだよ。' \
  --max-duration 4 --output-dir outputs/voice-demo
anime-video-voice synthesize --speaker female --text '今、私のこと撮った？'
```

未安装 console entry 时可使用 `PYTHONPATH=src python -m anime_knowledge_video.local_voice` 加相同参数。MCP 客户端指向这个 Python 环境中的 `anime-video-mcp`，调用 `local_voice_health` 和 `synthesize_local_voice(text, speaker, output_dir, max_duration_sec)`；完整 SDK 和轻量 stdio 实现均支持。旧 `generate_voice(project_dir)` 仍是整项目占位接口，不代表新的逐句工具不可用。

## 固定角色参数

| 角色 | 署名 | Style / model | speed / pitch / intonation | 句中停顿上限 |
|---|---|---|---|---|
| 夏帆 | VOICEVOX:雨晴はう | 10 / 0.vvm | 1.02 / 0.006 / 1.10 | 0.22 秒 |
| 湊 | VOICEVOX:玄野武宏 | 11 / 4.vvm | 0.94 / 0 / 1.00 | 0.15 秒 |

男声 v3 恢复原生音高与正常句调，整句合成；女声保持轻柔清亮。24kHz 原生语音经 64-tap SWR 转为 48kHz 双声道，轻度 EQ、首尾静音修整、5ms 淡入淡出，不做后期时间拉伸、音高移动或音节拼接。长度超过时隙时明确失败，调整时间轴或文本，不能截断台词。

每次输出唯一文件名、原始 24kHz WAV、最终 WAV 和包含文本、完整 query、参数、时长、SHA-256、署名的 JSON。`human_listening_review=false`；技术合成成功不等于听感验收。第一幕男声修复脚本会逐字节保留原女声；新场景则用相同预设重合成新台词。

传播视频时在描述中保留 **VOICEVOX:雨晴はう / VOICEVOX:玄野武宏**。模型及音色许可独立于本仓库 MIT 代码许可。
