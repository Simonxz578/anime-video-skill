# anime-video-skill · 蓝白二次元视频 Skill + MCP

这个仓库提供 Codex Agent Skill、本地 MCP 服务和离线可重复的**策划流程**。输入已收录的主题，会输出带来源的 claims、中文脚本、60 秒分镜、成本占位和明确标为待完成的 QA 报告。原创言情系列提供双人物母版、三章日语对白、逐句对应中文字幕、120 秒分镜及连续性/文本去重检查。

**输出格式固定为 1080p、30fps。** 默认竖屏 1080×1920（9:16）；用户要求横屏时为 1920×1080（16:9）。MP4 / H.264 / yuv420p / AAC 48kHz 双声道。言情章节目标 120 秒，即 3600 帧。

新增可运行的本地成片路径：`scripts/render_motion_film.py`。输入已生成并验收的角色参考图条件化场景、原创分镜和日中对白，可实际生成日语配音、中文字幕、原创合成配乐、雨声、慢速镜头与独立雨滴动画，再导出字幕版和无字幕版 MP4，并执行 ffprobe 与解码检查。完整例子是《雨》第一章《初遇》：`examples/rain/ch001.json`。它是动态插画短片，没有口型同步或逐帧角色肢体动画。详见 [成片制作说明](docs/motion-film.md)。

原来的 `anime-video` / MCP 接口仍是策划路径，`quality=final` 仍会停在尚未接通的 provider 门槛。Remotion 是合成示例；新成片脚本使用 OpenCV/Pillow + FFmpeg，不依赖 Remotion。

## 安装

需要 Python 3.10+。离线运行可用 `python -m pip install -e .`；若可访问 PyPI，建议安装官方 MCP SDK：`python -m pip install -e '.[mcp]'`。未安装 SDK 时使用仓库内的最小 stdio MCP 实现。安装后运行：

```bash
python -m pip install -e '.[mcp]'
python scripts/doctor.py
anime-video episode '为什么夜空是黑的？' --series cosmos --quality draft
```

当前主题示例的来源是 NASA 的奥伯斯佯谬资料。运行会在 `projects/episode-de0c641dc1/` 写出 `research/sources.md`、`claims.json`、`factcheck_report.md`、`script/`、`storyboard/`、`qa/`。事实资料是经编入仓库的示例；正式发布前仍需重新核验链接、表述和画面。

其余五个候选 brief 在 `examples/candidates.json`。它们还没有研究包和脚本，直接生成时会给出缺失提示。若要输入新 topic，可提供符合 `examples/episode-de0c641dc1.json` 结构的自有研究包：每条 claim 需来源、URL、置信度、限制条件及画面含义。不要用未经核验的文本冒充已完成研究。

## 言情系列

```bash
anime-video romance-series
anime-video romance-chapter 1
anime-video romance-chapter 2
anime-video romance-chapter 3
```

产物集中在 `outputs/romance/after-the-rain-route/`。对白中的 `ja` 是中文字幕的语义母本，`line_id` 与时间戳用于绑定。自动检查只覆盖结构、时间和精确文本去重；日中语义、人物脸部、声音、音乐原创性和旧画面复用都仍需人工及媒体工具检查。后续章节要读取 `continuity/state.json`；默认母版在 `references/female_lead_master.png` 和 `references/male_lead_master.png`。

## 接入 Codex MCP

在 Codex 的 MCP 配置中新增 stdio 服务。把 `command` 改成安装该包的 Python 环境中 `anime-video-mcp` 的绝对路径：

```toml
[mcp_servers.anime_video]
command = "/absolute/path/to/anime-video-mcp"
```

或用该环境的 Python 模块方式启动：

```toml
[mcp_servers.anime_video]
command = "/absolute/path/to/python"
args = ["-m", "anime_knowledge_video.server"]
```

在支持仓库 Skill 的 Agent 中打开本仓库，并使用 `skills/one-minute-anime-knowledge/SKILL.md`。MCP tool 示例：`create_episode(topic="为什么夜空是黑的？", series="cosmos", quality="draft")`；`create_romance_series()` 后调用 `create_romance_chapter(series_id="after-the-rain-route", chapter_number=1, quality="draft")`。

## 参考图与最终成片设想

三张参考图已附在 `references/`：知识系列母版和女主母版是同一张，男主是第二张。知识片目标为 55–65 秒、9:16、1080×1920、30 fps、H.264/AAC；言情章目标 120 秒、日语双声线、中文字幕。视觉策略是静帧和 2.5D 缓慢运动为主，少数镜头才采用 image-to-video。连续性高于动态数量；历史重建图要标注为重建。仓库没有原电影配乐、未授权字体或真实声优克隆。

## Provider 与配置

本地成片脚本使用 macOS 系统日语语音、程序原创声音和 FFmpeg；图像通过可用的图像生成工具另行生成。详见成片说明。MCP Python SDK 是可选运行依赖；Remotion 在 `remotion/`，仍未接入。`.env.example` 的未来 provider 变量不会自动启用尚未实现的 MCP adapter。主观画面和语言检查必须如实标记为 Agent 检查或待人工检查。

## 目录与上游

- `src/anime_knowledge_video/`：知识系列策划与 MCP。
- `src/anime_knowledge_video/romance/`：言情连续性、字幕绑定、文本去重。
- `skills/`：唯一 Skill 正文。
- `remotion/`：合成契约示例。
- `examples/`：一条已收录 source pack、五条候选 brief、三章原创对白。
- `projects/`、`outputs/`：运行产物，不提交 Git。

架构与第三方许可见 `docs/architecture.md` 和 `THIRD_PARTY_NOTICES.md`。OpenMontage 仅作为工作流参考，不复制其 AGPL 代码。Remotion 有独立的使用条款，使用者应查看其当前许可。

## 排错

- `No source pack`：为新主题准备并核验研究包；候选 brief 本身不足以生成脚本。
- MCP 客户端连接失败：确认指向安装本包的 Python 环境；无 SDK 时最小 stdio MCP 实现只支持 initialize、tools/list、tools/call。
- `duration must be ...`：知识视频限 55–65 秒；言情章限 115–125 秒。
- `GATE: Final requires ...`：原 MCP/CLI 策划路径的发布保护；已准备媒体时按 `docs/motion-film.md` 使用独立渲染器。
