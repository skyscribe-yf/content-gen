---
name: manim-article-video
description: 根据公众号文章（weixin.md）素材生成 Manim 动画风格的微信视频号成品——分镜脚本、配音（可选 MiniMax 克隆 TTS 整段生成，或作者口播逐段录音）、Manim 竖屏动画场景、一键构建（mux 配音 + 无缝拼接 + 黄色字幕烧录 + 品牌尾卡）。Use when user mentions "视频号", "微信视频", "Manim 动画", "manim 风格视频", "给文章做视频", "shipinhao", 或要求把某篇文章做成动画视频。
version: 2.1.0
metadata:
  openclaw:
    homepage: internal
---

# 文章 → Manim 动画视频号成品

本 SKILL 是流程索引，详细内容拆到 `docs/` 下各专题文件（与 AGENTS.md 同款模式）。**开始任何一步前先读对应 docs 文件全文**。

## When to Use

- 用户要求把某篇公众号文章做成视频号（shipinhao）视频，尤其提到「Manim / 动画风格 / 数学动画」
- 用户说「对 XX 这篇文章做一个微信视频」「给文章配视频」「做成 3Blue1Brown 风格」等

## 用户输入模式

1. **标题指代文章，不给路径**：按标题关键词 grep 定位 `content/<日期>-<主题>/`，确认后读 `weixin.md`
2. **风格词口语化**：「Many 动画风格」= Manim；「微信视频」= 视频号成品
3. **极简确认**：用户常只回「manim」「go」「haole」= 继续，不要停下来再问
4. **sudo 停下交用户**：系统依赖安装等 sudo 操作停下来给出指令，用户执行完回「haole」再继续
5. **规格先问、微调自主**：竖屏/时长/**配音方式（TTS 克隆 / 口播）** 大方向 `ask_user_question`（仅首次，用户认可推荐项）；语速、缓冲、字幕等微调直接取定稿值（见 docs/decisions.md），不问
6. **配音方式在 Step 2 问清并全程一致**：选 TTS 克隆 → Step 4A；选口播 → Step 4B。中途禁止切换
7. **段间停顿是红线**：成片必须验证静音段，段间缓冲 0.1s

## 前置条件

1. **文章**：`content/<日期>-<主题>/weixin.md`（内容唯一基准，同 AGENTS.md 多平台一致性规则）
2. **Manim**：`pip3 install manim`；系统依赖 `libpango1.0-dev libcairo2-dev`（sudo 装，交给用户执行）。⚠️ **版本坑（2026-08-15）**：v0.21 起 `DecimalNumber` 默认 `mob_class=MathTex`（需 latex）；本机已装 `texlive-latex-extra/latex-recommended/science + dvisvgm`，`MathTex` 可渲染复杂公式，但 `scripts/manim_helpers.py` 的 `counter_value` 仍显式 `mob_class=Text` 规避依赖（数字用 Text 足够）；升级后先单场景 -ql 冒烟确认兼容再大规模渲染（见 [pitfalls.md](docs/pitfalls.md)）
3. **中文字体**：Noto Sans CJK SC（`/usr/share/fonts/opentype/noto/`），Manim `Text(..., font="Noto Sans CJK SC")`
4. **API Key**：`MINIMAX_API_KEY`（`scripts/minimax_tts.py`，默认 **speech-2.8-turbo**，hd 用 `--model speech-2.8-hd`）；MiMo 旧脚本 `scripts/xiaomi_mimo_tts.py` 弃用（无时间戳，切分需收费 ASR，不用于视频配音）
5. **克隆音色**：`branding/my-voice-denoised.wav`（作者声音，MiniMax 克隆参考；原始录音 `branding/my-voice-original.m4a`，旧版备份 `my-voice-old-20260810.wav`）。voice_id 缓存于 `branding/.minimax_voice_id`（7 天内用过即永久保留，删除后重新克隆即可）。**默认配音用克隆音色，不用内置音色**
6. **工具**：ffmpeg、`scripts/manim_video_build.py`、`scripts/tts_split.py`、`scripts/add_tts_tags.py`、`scripts/voice_process.py`（口播模式用）、`scripts/voice_studio.py`（口播录音室，agent 后台编排，见 [docs/step4b-recording.md](docs/step4b-recording.md)）、品牌图 `avatar-sjai.png`（项目根目录）

## ⛔ 硬性门禁：先声音，后动画（用户拍板 2026-08-17）

**配音/录音未完成并确认前，禁止开始设计动画**（scenes.py 的 at() 排布、元素出现时间、滞留时间）。动画时间轴必须完全挂在实际语音时间线上，与切分出的字幕时间线**完全对应**：

- **声音就绪标志**：TTS 模式 = `tts/s1..s8.wav` 切分验证通过 + `VOICE_DUR` 实测值；口播模式 = `voice_process.py` 完成 + 门禁 4/5 通过 + `tts/pauses.json` 生成。禁止用预估时长设计动画（音画错位返工的直接根因）
- **出现时间** = 对应台词字幕的起始时间戳（`at(t)` 精确挂接）；**滞留时间** = 到本句字幕结束 / 下一句字幕开始（FadeOut 不得晚于下一句字幕出现）
- 时间轴锚点来源：`tts/pauses.json`（口播，静音结束点 = 下一句起点）或 `full.subtitle.json`（TTS 句子时间戳）
- 详情见 [docs/step5-scenes.md](docs/step5-scenes.md) 时序门禁；QA 清单 A14 核查

## 全流程（8 步 + 质量检查）

| 步骤 | 内容 | 详情 |
|---|---|---|
| Step 1 | 定位文章 + 读素材 | [docs/step1-2-input.md](docs/step1-2-input.md) |
| Step 2 | 规格确认 + 配音方式门禁（仅首次，问一次） | [docs/step1-2-input.md](docs/step1-2-input.md) |
| Step 3 | 分镜脚本 storyboard.md + 台词爆点节奏（硬性）+ **插图位规划**（比喻/场景配概念图、数字/结构配脚本画图，见 [docs/vividness.md](docs/vividness.md)） | [docs/step3-storyboard.md](docs/step3-storyboard.md) |
| Step 4A | TTS 克隆整段配音 + 时间戳切分（门禁 1-2） | [docs/step4a-tts.md](docs/step4a-tts.md) |
| Step 4B | 口播录音 + 修音 + 停顿分析（门禁 1-5，替代 4A） | [docs/step4b-recording.md](docs/step4b-recording.md) |
| Step 5 | 写 Manim 场景 scenes.py（工具在 `scripts/manim_helpers.py`（含 `layout_page`/`page_stack`），模板 `scripts/manim_scene_template.py`；**整页规划** + 布局规范 0-28 硬性；**生动化三件套**：counter_value/transition_out/概念图嵌入，见 [docs/vividness.md](docs/vividness.md)；**≥6 场景新写可多 agent 并行**，见 [docs/multi-agent-scenes.md](docs/multi-agent-scenes.md)） | [docs/step5-scenes.md](docs/step5-scenes.md) |
| Step 6 | 渲染验证：`-ql` 冒烟 → `-qm` 成品 → **派 QA** | [docs/step6-render.md](docs/step6-render.md) |
| Step 7 | 一键构建（mux + 拼接 + 字幕 + 烧录） | [docs/step7-build.md](docs/step7-build.md) |
| Step 8 | 成片验证 + 归档（**再派 QA**） | [docs/step8-verify.md](docs/step8-verify.md) |

### 质量检查环节（硬性，Step 6 渲染后 + Step 8 构建后各一次）

渲染完成和 build 完成**都必须派 `.pi/agents/manim-qa-reviewer` subagent 跑质量检查**，逐项过 [docs/qa-checklist.md](docs/qa-checklist.md)（A 组 20 项渲染后检查 + B 组 7 项成片检查）。QA 输出 PASS/FAIL + 证据；**任一项 FAIL → 修复 → 重渲染 → 重跑 QA，全 PASS 才能宣称完成**。QA 不通过就交付 = 用户时间轴反馈事故（S7 残影 5s、弧线穿圆 3009 像素）的直接根因。

```bash
# 主 agent 派 QA（渲染后）：
subagent(agent="manim-qa-reviewer", task="QA 检查 <shipinhao目录> 渲染产物（A 组）")
# 主 agent 派 QA（构建后）：
subagent(agent="manim-qa-reviewer", task="QA 检查 <shipinhao目录> 成品（B 组）")
# ⚠️ manim-qa-reviewer 默认模型已固定为 ollama-cloud/deepseek-v4-flash:0731
# （2026-08-19 用户拍板，.pi/agents/manim-qa-reviewer.md 已配），派发时无需显式传 model
```

QA subagent 为 review-only（不改文件），发现的问题由主 agent 修复。

## 规则速查

- **卡片样式**（2026-08-16 用户拍板）：文本方框统一 `_card()`/`boxed()`：实心 `CARD_FILL=#2C3F60` + 圆角 `RoundedRectangle(corner_radius=0.18)`；高亮色只做强调，不给默认卡底——详见 [docs/step5-scenes.md](docs/step5-scenes.md) 规范 29
- **字幕同步**（2026-08-16 用户反馈）：字幕与声音不同步而声音与画面同步时，先查 build 是否用了 `tts/sentence-boundaries.json` 逐句 start/end（优先级：manual > sentence-boundaries > pauses 兜底 > full.subtitle）；用户报「XX:XX 声音滞后」时的诊断/精修/复验全套方法见 [docs/av-sync.md](docs/av-sync.md)（MiMo ASR 内容验证 + silencedetect 局限 + validate_sentence_ts 防线）；详情 [docs/step7-build.md](docs/step7-build.md)、[docs/pitfalls.md](docs/pitfalls.md) #42
- **整页规划**（2026-08-16 用户拍板）：每次换页都按该页全部元素的稳定状态组装整页 box → `page_stack()` → `layout_page()` 垂直居中；上下留白相等且各 ≤ 显示带 30%（内容高度 ≥40%，不足会 ValueError）；闪烁/强调装饰不参与整页 box——详见 [docs/step5-scenes.md](docs/step5-scenes.md)「整页规划」
- **生动化三件套**（2026-08-15 新增）：AI 概念图嵌入（yairouter+make_round_logo，禁数字）+ 数据动效（counter_value/grow_bar/轨迹 Create，数字台词必配动效）+ 场景转场（transition_out）——详见 [docs/vividness.md](docs/vividness.md)
- **动效库 v2**（2026-08-18 新增）：镜头推拉（camera_zoom_to，必须成对）+ 形变（morph_to）+ 轨迹追踪点（trace_dot）+ 关键词强调（emphasize）+ 呼吸微动（breathe，≤3%）——详见 [docs/vividness.md](docs/vividness.md) 第四节
- **多 agent 并行写 scenes**（2026-08-15 新增）：≥6 场景新写时，≤4 并行 writer 只写不渲染、合并后渲染、review-fix 循环——详见 [docs/multi-agent-scenes.md](docs/multi-agent-scenes.md)
- **生效决策表**（用户拍板 49 条，勿再返工）：[docs/decisions.md](docs/decisions.md)
- **常见坑**（43 条快速自查）：[docs/pitfalls.md](docs/pitfalls.md)
- **发布要点**（扩展链接/封面安全区）：[docs/publish.md](docs/publish.md)
- **质量检查清单**（QA subagent 执行依据）：[docs/qa-checklist.md](docs/qa-checklist.md)
