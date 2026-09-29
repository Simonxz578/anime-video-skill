# 六 Skill 获取与实际使用记录

检查日期：2026-09-28。上游 HEAD 通过 GitHub API 查询；选定模块按提交固定安装至 `~/.codex/skills`。完整仓库没有复制进主项目。生成视频 API 与 Seedance 均未调用。

| Skill 仓库 | 安装状态 | 版本 / commit | 本次使用 |
|---|---|---|---|
| heygen-com/hyperframes | 已安装核心、动画、CLI、audio、general-video、creative、media-use | CLI 0.8.81；bee6a8e17d9198e734907b06e2c6f167529893e3 | HTML/GSAP分镜时间轴、静态检查、720p渲染 |
| browser-use/video-use | 已安装完整小型Skill | b877063835e6ea6e457124da7e28a0ae26691dc3 | 本地FFmpeg剪辑方法、timeline_view可视检查；跳过ElevenLabs |
| remotion-dev/skills | 已安装best-practices/markup/render/captions/multimedia | Skill 4.0.529；cf49eff5d4463b33966b6618c83f7295797dd028 | 帧计时、字幕与编码方法；不声称用Remotion运行时渲染 |
| calesthio/generative-media-skills | 已安装连续性、镜头、分镜、音乐、拟音、QA、FFmpeg、Seedance方法模块 | 8c85352d5d75d4dcbe58480bd138e37b9742bab1 | 身份/道具/空间锁定、音乐motif、交付QA；无付费provider |
| Agentchengfeng/chengfeng-videocut-skills | 方法文档已安装；Runtime未安装/未改动 | a33b43e08c34fa8beeb5e78498e852f4e80975a5 | cut/subtitle/visual/export方法。dry-run成功；doctor拒绝：Cannot execute Codex CLI: spawnSync codex ENOENT；上游公开Runtime版本亦低于新工作台要求，按用户允许降级为方法参考 |
| dexhunter/seedance2-skill | 已安装中文提示词Skill | 516284d5bab58361bfdfed3cc96cee3e837d4c44 | 多参考素材说明、保留/修改边界、动作语言。原Skill针对2.0，2.5时长信息另外核实官方 |

## 安装路线说明

HyperFrames官方 `npx hyperframes skills update` 在大型仓库获取阶段长时间停滞；采用Codex官方skill-installer的Git稀疏获取方式安装所需目录，保留固定commit。没有为安装Skill重构主仓库。

成峰安装日志保留在本地工作区。方法安装不等同于其Studio/Runtime可运行，不使用虚假“全部运行成功”状态。

## 2.5资料核对

[ByteDance Seed官方2026-07-31说明](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5)：介绍最长30秒与时间戳编辑。小云雀具体入口能力须以用户之后上传时界面为准。本次只交付导演母版和手动编辑提示词。

## 本地声音与资产

VOICEVOX Core 0.17.0 CPU；女声雨晴はう Style 10，男声玄野武宏 Style 11。复用第一幕male_voice_v3 preset；没有真人声纹克隆。原创《雨》五音motif重新编配，无第三方音乐或付费API。图片通过Codex内置imagegen生成，参考用户两张人物母版及已完成第一幕画面。视频是图片导演animatic，不是连续人体生成动画。

## 在新环境恢复 Skill

所有目录与提交见 [upstream-skills.lock.json](../config/upstream-skills.lock.json)。使用已安装 Codex 的官方 skill-installer，按条目指定 `--repo`、`--ref`、`--path`、`--name` 和 `--method git`；先检查目标名字是否已经存在，避免覆盖用户修改。示例：

```bash
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo browser-use/video-use --ref b877063835e6ea6e457124da7e28a0ae26691dc3 \
  --path . --name video-use --method git
```

安装 Skill 只增加方法文档；VOICEVOX、FFmpeg、HyperFrames、ComfyUI 的运行依赖必须按各自说明安装。若本机没有官方安装器，可以在临时目录 checkout 对应固定提交后复制记录的 Skill 目录；不要把整套上游仓库提交进本项目。
