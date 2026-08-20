# 质量检查清单（manim-qa-reviewer 执行依据）

QA subagent 按此清单逐项核查，输出 **PASS / FAIL + 证据**（文件:行号 / 帧图路径 / 命令输出）。任一项 FAIL → 主 agent 修复 → 重渲染 → 重跑 QA，直到全 PASS。

## A 组：渲染后检查（对 `media/videos/scenes/1920p30/S*.mp4` 无字幕帧 + scenes.py 代码审查）

| # | 检查项 | 方法 | 判据 |
|---|---|---|---|
| A1 | 每场景 `pad_to_voice()` | grep `pad_to_voice` 每个 Scene | 每个 `class S\d+` 的 construct 末尾有调用 |
| A2 | 入场方式合规 | grep `FadeIn(.*boxed\|FadeIn(l[0-9]\|FadeIn(.*txt\|FadeIn(.*_card` | 卡片无 FadeIn（应用 play_scroll_unroll）；裸文字无整段 FadeIn（应用 type_in） |
| A3 | FadeOut 对账（含段内换页） | 读 scenes.py 每个 Scene，列 FadeOut 引用的 mobject vs 该页 play/add 过的 | 无遗漏（含 Arrow/Axes/装饰/上段残留） |
| A4 | 裸魔法数字定位 | grep `move_to(UP\|move_to(DOWN\|\.shift(UP \* [0-9]` 等 | 无硬编码绝对坐标（比例坐标 `* FH/FW` 除外） |
| A5 | 像素贴边扫描 | 每场景抽 70% 时间点帧，PIL 找非背景像素到画布边缘距离 | ≤2px 即 FAIL（超界） |
| A6 | 框内文字溢出 | 每场景 30%/60%/90% 抽帧，逐个框目测 | 无文字压/出边框（badge 首字母、长英文、9 字中文） |
| A7 | 元素重叠 | 帧目测 + 已知重叠点（如中心文字 vs 相邻圆） | 同屏元素不压叠（刻意 z_index 除外） |
| A8 | 弧线穿圆（闭环图） | 抽弧线完成帧，像素级：弧线色像素到各圆心距离 | ≥ 圆半径（文字抗锯齿除外） |
| A9 | 动画中帧中间态 | 每场景抽 30%/60% 帧 | FadeIn/拉幕中间态无错位、无重叠 |
| A10 | 整页规划/安全区 | 读 scenes.py：每页是否先 `page_stack()` 组稳定 box 再 `layout_page()`（grep `next_to(head, DOWN` 应无）；每页末帧量整页 box/内容像素 | 全页使用 helper；内容最低点距底 399~800px；**上下留白相等且各 ≤ 显示带 30%**（内容高度 ≥40%，layout_page 会硬校验）；顶部不压标题、底部不压 footer。ImageMobject/曲线等透明 bbox 页以整页 bbox 为准，并复核可见内容仍在安全区 |
| A11 | 公式画面 | grep 台词含公式的场景，抽对应帧 | 出组装公式、上标锚 UR、√d 横线正确 |
| A12 | 开场小字 | S1 前 3s 帧 | 原理系列有「以 XX 为例」MUTED 行 |
| A13 | 尾卡要素 | 最后场景末帧 | 品牌图 + 黄色关注 + 当期标题 + 引导（绿色） |
| A14 | 动画时间轴 vs 字幕时间线 | 读 scenes.py 每个 `at(t)` 与 `tts/pauses.json`（口播）或 `full.subtitle.json`（TTS）对比 | 每个 at(t) 能对应一条字幕边界；元素 FadeOut 不晚于下一句字幕开始；动画设计在配音确认后进行（先声音后动画门禁） |
| A15 | 插图规范 | grep `ImageMobject` 的场景抽帧 + 检查生成 prompt | 概念图圆角无白边、风格统一（深蓝系）、不压安全区；**AI 图无数字/年份/公式**（数字走 grow_bar/counter_value）；图宽 ≤5.5、换页 FadeOut 带走图 |
| A16 | 数字动效 | grep 台词含数字（步数/分数/百分比/倍率）的场景，抽对应帧 | 出 counter_value/grow_bar/轨迹 Create 对应动效，禁止纯文字陈述数字 |
| A17 | 跨场景一致性（多 agent 模式专属） | 逐场景对比字号/间距/配色/入场/锚点精度 | 字号体系、间距密度、配色、入场方式全片统一；抽查 3 场景 at() 都能从契约包锚点表回溯；若用 transition_out 则全片统一用且都传全部元素 |
| A18 | 镜头推拉成对（动效库 v2） | grep `camera_zoom_to` 每个 Scene + 抽推近帧/末帧 | 每个推近都有对应拉回（`camera_zoom_to()` 无参）；场景末帧相机全画布（无放大残留）；推近帧内容不越安全区（A5/A10 对缩放帧同样适用） |
| A19 | 动效库 v2 合规 | grep `trace_dot`/`breathe`/`emphasize`/`morph_to` 每个 Scene | trace_dot 的 dot 换页被 FadeOut 带走；breathe 幅度 ≤3%（scale ≤1.03）；动效时长计入 at() 排布（不超台词）；emphasize 不遮挡关键文字 |
| A20 | 整页稳定 box（闪烁元素） | 读 scenes.py 每页 `page_stack(...)` 参数清单 | 红叉/circumscribe/indicate/breathe/数字滚动过程**不参与** `layout_page` box；数字用终值占位（`Rectangle` 占位 + `_cnt/move_to`），整页 box 按稳定后几何计算 |
| A21 | 卡片样式（实心+圆角） | grep `_card(`/`boxed(`；抽帧目测卡片填充 | 文本方框全部实心 `CARD_FILL=#2C3F60`、`fill_opacity=1.0`、`RoundedRectangle(corner_radius=0.18)`；无文本方框用普通 `Rectangle`；默认卡底不与黄/青/绿/红高亮色混淆；`play_scroll_unroll()` 为圆角拉幕 |

## B 组：构建后检查（对成品 `<标题>-成品.mp4`）

| # | 检查项 | 方法 | 判据 |
|---|---|---|---|
| B1 | 字幕位置 | 抽首/中/尾帧 | 品牌条上方 y∈[1610,1690] 有黄色像素（r>180,g>150,b<120） |
| B2 | 字幕不截断 | 抽字幕帧 | 黄字右缘 x<1036、左缘 x>44 |
| B3 | 字幕折行 | 抽长句帧 | ≤2 行；英文单词不拆断 |
| B4 | 音画同步 | `python3 scripts/check_sync.py <shipinhao目录>`；若存在 `tts/sentence-boundaries.json`，对比 `subs.srt` 每条与 clips 的 start/end（按实际段长累计） | 字幕时间戳无重叠/无过短；每条字幕都落在对应 clip 区间内，不跨句；「声音与画面同步但字幕不同步」= build 时间戳优先级错误，必须用 sentence-boundaries |
| B5 | 无长静音 | `ffmpeg -i 成品 -af silencedetect=noise=-35dB:d=1.5 -f null -` | 最长静音段 <1.5s（段间 0.1s 缓冲、句间 <1s 正常） |
| B6 | 时长 | ffprobe | ≈ Σ(VOICE_DUR) + N×0.1 |
| B7 | 封面 | 检查 `<标题>-封面.png` | yairouter 1080×1920；关键内容在 3:4 安全区 y∈[240,1680] |
| B8 | 用户报点 ASR 抽验（有反馈时必做） | 提取报点 ±1s 各 2s 音频 → MiMo ASR（`scripts/mimo_srt.py`）→ 与 subs.srt 同刻文本对比 | 语音内容 == 字幕文本；不一致 → 按 av-sync.md 精修 sentence-boundaries 后重 build |

## 常见 FAIL 模式（对应 pitfalls.md）

- A3 漏元素：FadeOut 缺本页元素 → 残影叠压（RLHF S7 lab、预训练 prefix、归一化箭头）
- A5 超界：宽组未 fit → 边字被裁（BPE「左」/「块」）
- A6 溢出：框内长文字未限宽 → 压出边框（Transformer/WordPiece）
- A10 接龙布局/留白不等：`next_to(head, DOWN)` 从标题往下铺 → 整页 box 未用 `layout_page` 居中、上下留白不等或 >30%（GRPO 第三轮）
- A8 穿圆：CurvedArrow → 弧线进圆（RLHF v7 3009 像素）；用 arc_curve()
- B4 不同步：字幕时间戳按字数比例 → 早 2-3s；pauses.json 停顿驱动
