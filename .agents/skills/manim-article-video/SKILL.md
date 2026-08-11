---
name: manim-article-video
description: 根据公众号文章（weixin.md）素材生成 Manim 动画风格的微信视频号成品——分镜脚本、MiniMax 整段配音（克隆音色）、Manim 竖屏动画场景、一键构建（mux 配音 + 无缝拼接 + 黄色字幕烧录 + 品牌尾卡）。Use when user mentions "视频号", "微信视频", "Manim 动画", "manim 风格视频", "给文章做视频", "shipinhao", 或要求把某篇文章做成动画视频。
version: 1.1.0
metadata:
  openclaw:
    homepage: internal
---

# 文章 → Manim 动画视频号成品

## When to Use

- 用户要求把某篇公众号文章做成视频号（shipinhao）视频，尤其提到「Manim / 动画风格 / 数学动画」
- 用户说「对 XX 这篇文章做一个微信视频」「给文章配视频」「做成 3Blue1Brown 风格」等

## 用户输入模式

1. **标题指代文章，不给路径**：按标题关键词 grep 定位 `content/<日期>-<主题>/`，确认后读 `weixin.md`
2. **风格词口语化**：「Many 动画风格」= Manim；「微信视频」= 视频号成品
3. **极简确认**：用户常只回「manim」「go」「haole」= 继续，不要停下来再问
4. **sudo 停下交用户**：系统依赖安装等 sudo 操作停下来给出指令，用户执行完回「haole」再继续
5. **规格先问、微调自主**：竖屏/时长/配音大方向 `ask_user_question`（仅首次，用户认可推荐项）；语速、缓冲、字幕等微调直接取定稿值（见生效决策表），不问
6. **段间停顿是红线**：成片必须验证静音段，段间缓冲 0.1s

## 前置条件

1. **文章**：`content/<日期>-<主题>/weixin.md`（内容唯一基准，同 AGENTS.md 多平台一致性规则）
2. **Manim**：`pip3 install manim`；系统依赖 `libpango1.0-dev libcairo2-dev`（sudo 装，交给用户执行）
3. **中文字体**：Noto Sans CJK SC（`/usr/share/fonts/opentype/noto/`），Manim `Text(..., font="Noto Sans CJK SC")`
4. **API Key**：`MINIMAX_API_KEY`（`scripts/minimax_tts.py`，默认 **speech-2.8-turbo**，hd 用 `--model speech-2.8-hd`）；MiMo 旧脚本 `scripts/xiaomi_mimo_tts.py` 弃用（无时间戳，切分需收费 ASR，不用于视频配音）
5. **克隆音色**：`branding/my-voice-denoised.wav`（作者声音，MiniMax 克隆参考；原始录音 `branding/my-voice-original.m4a`，旧版备份 `my-voice-old-20260810.wav`）。voice_id 缓存于 `branding/.minimax_voice_id`（7 天内用过即永久保留，删除后重新克隆即可）。**默认配音用克隆音色，不用内置音色**
6. **工具**：ffmpeg、`scripts/manim_video_build.py`、`scripts/tts_split.py`、`scripts/add_tts_tags.py`、品牌图 `avatar-sjai.png`（项目根目录）

## 全流程（8 步）

### Step 1 定位文章 + 读素材

按标题关键词在 `content/` 下定位目录，读 `weixin.md` 全文，提炼：核心概念、关键数字/表格、文章结构（钩子→定义→链路→数据→手段→行动）。

### Step 2 规格确认（仅首次）

`ask_user_question` 一次问清，推荐项：画面**竖屏 9:16**、时长 **2-3 分钟**（软上限 4 分钟，见 Step 4 时长门禁）、配音 **MiniMax 克隆音色 + 烧录字幕**。

### Step 3 分镜脚本

写 `shipinhao/storyboard.md`：段落表（场景 / 动画要点 / 配音稿），每段一个场景，8 段左右。配音稿是字幕基准，措辞须与文章术语、年份一致（2026 等，见 AGENTS.md 数据时效性）。

**台词爆点节奏规范（硬性，完播率抓手）**：

1. **开场钩子（S1 前 3 秒，硬性）**：第一句必须是价值承诺或悬念——「这条视频讲清楚 XXX 为什么 YYY」/「XXX 出了问题，问题出在 XXX」，禁止开场寒暄/背景铺垫（完播率低的主因是开头 3 秒流失）
2. **每段至少 1 个爆点**，8 段内 4 种爆点类型轮换、均匀分布——禁止爆点全挤开头、中段平铺直叙：
   - 问句钩子（段首设疑）：「这 2KB 通信，凭什么能救 1M 序列？」
   - 数字对比（重读强调数据差）：「9MB 对 72MB——省了 8 倍」
   - 短句断句（拆长句制造节奏）：「注意。边界块，补齐了。」
   - 转折爆点（但/结果反转）：「但 gather 出来的数据里，有洞」
3. **只改节奏与标点，不改内容**：术语、数字、年份、事实必须与 `weixin.md` 一致，禁止新增正文没有的内容（爆点是语气强化，不是信息增量）
4. **禁止全程陈述句**：一段内问句/感叹至少 1 处；长句 >35 字必须拆
5. **拟声标签**：MiniMax 2.8 原生支持 `(sighs)(breath)(gasps)(laughs)` 等，整段生成（full.txt）同样可用，插在段首/停顿处增强人味，勿堆砌（每段 ≤2 个）；`scripts/add_tts_tags.py` 可自动按台词特征插入。⚠️ **转折处用显式停顿 `<#0.5#>`（精确到秒），不用 `(inhale)`**（2026-08-11 用户反馈：拟声标签只管发声不管停留；转折前要「停留」用停顿标签）
6. **段间悬念钩（硬性，2026-08-11 完播率优化）**：段尾过渡句升级为悬念——不只设问承接，要「抛问题不解答，下一段开头才揭晓」（如 S3 尾「普通 CP 全靠两个假设撑着。那假设塌了会怎样？」→ S4 开头揭晓）。段段设悬念拉住观众，禁止平铺式收尾
7. **结尾预告 + 互动（硬性）**：S8 末尾预告下一篇内容（「下一篇拆 DualPipe」）+ 抛 1 个开放式问题引导评论区（「你觉得 1M 上下文真有必要吗？评论区聊聊」）
8. **⚠️ 公式符号禁止进配音稿（2026-08-14 踩坑）**：TTS 文本里出现符号串（`⟨Q,K⟩`、`‖Q‖‖K‖cosθ`、`QKᵀ` 等）会被 MiniMax 当生词卡顿 2s+（实测「‖Q‖‖K‖cosθ」停 2.18s，画面僵住，完播率杀手）。公式一律口语化：「Q 和 K 的内积，等于 Q 的模乘 K 的模，再乘夹角的余弦」「除以根号 d」「Q 乘 K 转置」。画面上的公式照常写，只有 TTS 文本要口语。
9. 参照：`content/2026-07-17-位置编码/shipinhao/storyboard.md`（分镜）、`.../full.txt`（配音稿含拟声标签与 `<#0.5#>` 用法）

### Step 4 整段配音 + 时间戳切分（默认流程，2026-08-12 定稿）

**⛔ 门禁 1 配音稿确认（硬性）**：跑 TTS 前必须把逐段配音稿（含过渡句、拟声标签）展示给用户确认，回「go/haole」后再批量生成；配音稿有改动时同样先确认。

**⛔ 门禁 2 时长预估（硬性）**：确认配音稿时同步数字符预估总时长，明显超限先精简配音稿再进 TTS，**禁止生成音频后才报「太长了」**。
- 公式：`wc -m tts.txt` 字符数（**含标点/数字/字母，不是纯汉字数**）× 0.19~0.20（turbo 实测）+ 标签开销（每个 `<#0.5#>` 0.5s、每个拟声标签 ~0.3-0.5s）
- 软上限：成片 **≤4 分钟**；**预估 ≤4:20 直接做不返工**（用户明确许可「超过一点点也可以」）；>4:20 仍须先精简再生成
- 教训（2026-08-11）：按纯汉字数预估低估 20%+（位置编码按汉字 1198 字估 ~3:50，实际 wc -m 1548 字符 × 0.195 = 5:01）

**配音参数（定稿，勿擅自改）**：
- 模型 **speech-2.8-turbo**（2026-08-12 定稿：便宜且克隆+时间戳兼容，句间停顿略多；hd 仅用户明确要求时用）
- **speed 1.15 + pitch +2**（2026-08-10 试听定稿：克隆音色低沉偏慢，1.0 嫌慢、1.2/+5 太亮太急，1.15/+2 最自然）。**仅当用户要求调参时才重出试听**（用 2-3 句台词合成 3 组 speed×pitch，ffplay 播放给用户选）
- **整段生成，不逐段 TTS**（逐段生成段间话题跳跃、收尾生硬）：段尾过渡句（Step 3.5）+ 一次生成 + 官方句子级时间戳切分

```bash
# ① 整段文本 full.txt = tts.txt 8 段合并（含过渡句、拟声标签），一次生成
python3 scripts/minimax_tts.py --text-file shipinhao/full.txt \
    --clone-audio branding/my-voice-denoised.wav \
    --speed 1.15 --pitch 2 --subtitle --out shipinhao/tts/full.wav
# → tts/full.wav + tts/full.subtitle.json（句子级时间戳，免费）

# ② 按台词时间戳切分 8 段（scripts/tts_split.py，2026-08-12 固化）
python3 scripts/tts_split.py shipinhao --full tts/full.wav --subtitle tts/full.subtitle.json
# → tts/s1..s8.wav 覆盖旧文件 + 打印 VOICE_DUR（复制进 scenes.py）
# 切分验证：每段开头 0.1-0.2s 应静音（0.2s 窗口 RMS < -30dB 属正常起音，勿用 0.3s+ 窗口误报）；**段内长静音检测（硬性，2026-08-14 踩坑）**：`silencedetect=noise=-35dB:d=1.5` 逐段扫，出现 ≥1.5s 静音 = 台词含公式符号被 TTS 卡顿，不是切分问题——改 full.txt/tts.txt 口语化后整段重跑（勿手动补音频）
# ⚠️ 段边界 = 前后句时间戳中点（落在静音区）；勿用 begin-0.2（会吞前句尾音）
```

⚠️ **时长变化时 scenes.py 的 `at()` 节点必须按比例缩放**：k = 新时长/旧时长，所有 `at(t)` → `at(t*k)`（写脚本批量替换，勿手改），否则动画节点与配音错位。
⚠️ **勿用 build --speed 加速**（atempo 只变音轨，动画时间轴不变 → 音画错位）；提速必须重跑 TTS（MiniMax 直接变速，语音自然）。

**克隆参考音频预处理（录音后必做）**：手机录音底噪会被 voiceclone 学进成品（成品 SNR 仅 ~44dB，高频偏亮、听感尖薄）。克隆前先降噪 + 高频衰减：

```bash
ffmpeg -y -v error -i branding/my-voice.wav -af "afftdn=nf=-30,highshelf=f=8500:g=-4:width=1.2" branding/my-voice-denoised.wav
# 效果实测：SNR 45→57dB（参考音频），成品 44→59dB；频谱重心 1917→946Hz
# 克隆时 --clone-audio branding/my-voice-denoised.wav
```

质量检查（录音后）：语音占比 >70%（说话声占比，笔记本内置麦常 <15% 不可用）+ 信噪比 >25dB——**检测作参考，最终以新旧参考各克隆同一句台词的试听对比为准**（逐词停顿风格会低估语音占比，实测 41-57% 克隆仍可用）。重录参考音频须含张力要素：重读词（数字/关键词）、问句上扬、短句干脆收尾；录完先剪头尾空白再转 44.1kHz 单声道 wav。

### Step 5 写 Manim 场景 scenes.py

完整模板参考 `content/2026-07-18-注意力机制/shipinhao/scenes.py`（最新一期，工具函数齐全，含 `boxed()`/`fit()` 只缩小不放大、`sqrt_group()` 手绘根号、`play_red_cross()` 动态大红叉），核心骨架：

```python
from manim import *
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 8.0
config.frame_height = 14.2222
config.background_color = "#16213E"
FONT = "Noto Sans CJK SC"
VOICE_DUR = {"S1": 24.28, ...}   # Step 4 ② 输出，ffprobe 实测
TAIL = 2.5                      # 渲染用缓冲（build 时会截掉，只留 0.1s）

def t(text, size=34, color=WHITE, weight="NORMAL"):   # 统一文字工厂
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)

def boxed(label, w, h, color, fs=28, fill=0.12, ...):  # 固定框 + 限宽文字（≤框宽 78%）
    ...

def fit(mob, frac=0.85):        # 宽内容守卫：set_width(frame_width * frac)
    ...

class _Base(Scene):
    def setup(self):
        self.scene_dur = VOICE_DUR[self.__class__.__name__] + TAIL
    def at(self, t: float):      # 推进到配音时间轴绝对时刻（动画动作挂到台词节点上）
        if t > self.time:
            self.wait(t - self.time)
    def pad_to_voice(self):      # 末尾兜底补齐（静止等待须 ≤ 配音时长 20%，见节奏规范）
        elapsed = self.time
        target = self.scene_dur
        if target > elapsed:
            self.wait(target - elapsed)
    def footer(self, text="数解AI · 大模型原理"):   # 品牌条 to_edge(DOWN, buff=1.15)
        ...

class S1(_Base):
    def construct(self):
        ...
        self.pad_to_voice()   # ← 必加，否则场景时长 < 配音时长
```

- **每段一个 Scene 类（S1..SN），`construct` 末尾必须 `self.pad_to_voice()`**
- **动画节奏 = 台词时间轴（硬性）**：写 scenes.py 前先把该段配音稿每句按字数比例切出起止时间（与 build 脚本字幕分配同一逻辑，如 20s 配音讲 5 句，每句约 4s）；每个 `self.play` 对应一句台词，用 `self.at(t)` 排到该句起始节点，动作密度铺满整段。**禁止**把动作全挤前 1/3 然后 `pad_to_voice` 长等——画面静止等语音是「动画和语音速度差距大」的直接根因（FP4 实测：25s 配音只用了 ~8s 动作，后 2/3 僵住）
- **末尾 pad 上限**：`pad_to_voice` 静止等待 ≤ 配音时长 20%（25s 配音最多 pad 5s）；动作应覆盖 ≥80% 配音时长；渲染前自查：最后一个 `self.play` 结束时刻 ≥ 配音时长 80%
- 配色：背景 `#16213E`，主强调黄 `#FFD54A`（与字幕黄一致），青/绿辅助
- **字幕约定（与 build 脚本一致，勿单改）**：黄色、**字号 75**（缩放后 ≈69px，一行约 13 字）、拆句阈值 26（防折 3 行）、**MarginV=210**（品牌条上方，safe_margin 缩放后文字底部距底 ≈236px）、**整行一次出现 + 150ms 快速淡入**（默认 `{\fad(150,80)}`，`--typewriter` 可切回逐字）
- **品牌尾卡（最后一个场景）**：建议列表淡出 → `ImageMobject("avatar-sjai-round.png")`（圆角透明版，`scale_to_fit_width(3.6)`）→ 图下黄色「关注「数解AI」」→ **当期文章标题**（《…》，白/黄加粗，= `weixin.md` frontmatter `title` 一字不差）→「查看公众号文章」引导（绿）→ 下一篇预告（MUTED，可选）

**封面场景（视频号竖屏封面，必须）**：`scenes.py` 末尾加 `Cover` 场景（独立 `Scene`，不继承 `_Base`——无配音，`VOICE_DUR` 查不到类名会 KeyError）。标题 = 文章标题（≤22 字，关键词前置），副标题 = 痛点句，关键视觉复用本片最有记忆点的元素（如序列切段/显存账/两阶段示意），无动画直接 `add`。渲染单帧：`python3 -m manim render -qm -s --disable_caching scenes.py Cover` → `media/images/scenes/Cover_ManimCE_v0.20.1.png`，拷贝归档为 `<标题>-封面.png`。

**封面 3:4 安全区（硬性，2026-08-11 用户确认）**：视频号主页封面按 **3:4 裁剪显示**（从 9:16 居中截取 1080×1440），封面关键内容（系列名/标题/副标题/关键视觉/品牌）**必须全部落在垂直中间 75%**（像素 y∈[240,1680]，即 frame 坐标 y∈[-5.33, +5.33]），上下 12.5% 只放纯装饰背景元素；标题先 `set_width(frame_width*0.8)` 限宽防左右裁切（2026-08-11 事故：manim 版封面「位」字左边缘被裁）。裁剪后内容必须完整，禁止关键文字/视觉贴边

**布局规范（硬性，违反必须返工）**：

0. **通用参考**：Manim API 详细用法（mobjects/grouping/positioning/动画/LaTeX/CLI 等）查 `.agents/skills/manimce-best-practices/rules/`。**冲突时以本规范为准**——外部示例默认横屏 16:9（frame 8×4.5），本项目画布是竖屏 `8×14.222`（config 已覆盖，勿照抄外部示例尺寸）
1. **VGroup 原子化**：相关元素先组装成 `VGroup`，组内 `arrange(RIGHT/DOWN, buff=...)`，组外只对整体做一次 `next_to`/`move_to`/`to_edge`。**禁止散落硬编码绝对坐标**（如 `move_to(UP * 2.2)` 魔法数字）
2. **锚点链**：内容从标题/footer/锚点元素出发，用 `next_to(prev, DOWN, buff=0.35, aligned_edge=LEFT)` 逐块堆叠，整块只定位一次；多列对齐用 `aligned_edge`，需要精确对齐用 `align_to(anchor, LEFT/UP/...)`
3. **网格**：≥2 行的重复元素（GPU 块、列表项）用 `arrange_in_grid(rows, cols, buff, cell_alignment=LEFT)`，禁止手算格子宽度
4. **安全区**：所有元素必须落在 `config.frame_height/2 - 1.5`（上，避标题）与 `-config.frame_height/2 + 2.5`（下，避 footer/字幕）之间，横向 `|x| ≤ config.frame_width/2 - 0.4`；**内容最低点距底 399~800px**（<399 撞两行 75 号字幕，>800 画面空）。渲染后抽帧验证（见 Step 6/8）
5. **内容占屏**：每页内容垂直跨度 ≥ 屏高 40%（内容最低点距底 ≤800px），多数页 45-65%。手段：每场景 2-3 页（合并单元素页）、大字号（head 50-56、正文 38-48、强调 48-64）、间距 buff 1.0-1.5、图表 1.3x、单/双元素页加贴合台词的装饰视觉（如 16 可选值网格、2 的幂阶梯、台阶图）
6. **溢出控制**：长文本/宽图表先 `set_width(config.frame_width * 0.8)` 或 `scale_to_fit_width(...)`，禁止超界截断。Manim Text 实际宽度常比估算宽 20-30%，不要凭字数估算宽度
7. **比例坐标**：确需绝对定位时用画布比例（如 `UP * config.frame_height * 0.3`），保证换分辨率不崩
8. **叠放顺序**：用 `z_index=` 控制，不依赖 add 顺序
9. **框内文字自适应（硬性，事故率最高）**：固定尺寸框内放文字，必须 `txt.set_width(框宽×0.72~0.85)` 限宽——长英文（Transformer/WordPiece/Python）与长中文（9 字以上描述）溢出是高频事故（2026-08-10 BPE 视频 6 处）；统一用 `boxed_text()`/`boxed()` 工具，token 块文字 ≤ 框宽 78%。**嵌套框（`VGroup(Rectangle, VGroup(标题, 副标))`）内文字同样逐一限宽**（2026-08-10 事故：只修了平铺框，嵌套结构漏网）；写完 grep 复查所有 `Rectangle(` 与相邻 `t(` 组合。⚠️ **`set_width` 只缩小不放大**（2026-08-11 事故：Q/K/V/追/猫/qᵢ 等短字符被无条件放大到框宽 78%，字形顶出边框 4 处）——`boxed()`/`fit()` 必须 `if mob.width > limit: mob.set_width(limit)`
10. **VGroup 内元素必须排布**：`VGroup(w, a, b)` 不 arrange 时所有子元素中心重叠（S2 id_card 事故）。箭头自适应：先 `VGroup(两端).arrange(RIGHT, buff)` 定好两端位置，再 `Arrow(左端.get_right(), 右端.get_left())`
11. **动画中间态也是画面**（用户暂停逐帧看）：FadeIn `shift` 位移 ≤0.1；验证抽帧必须覆盖「动画中帧」（每场景 30%/60% 时间点）+「页末帧」（90%），不只抽页末
12. **禁止假占位符**：数据展示不全用「…」块（MUTED 色）或只放真实元素，禁止 [—] 等凑数元素（用户原话「非常丑陋」）
13. **长链路分两行蛇形**：≥5 节点（如 7 步链路）排两行（4+3），行间用黄色折线箭头（`Arrow(行1底部, 行2顶部)`），禁止单行硬塞
14. **弧线方向与遮挡**：`CurvedArrow` 的 `angle` 正负决定弧凸向——start 在右、end 在左时 `angle=-PI/2` 弧向**下**凸，`+PI/2` 向上凸。循环弧放元素**下方**：`CurvedArrow(右端.get_bottom()+DOWN×0.3, 左端.get_bottom()+DOWN×0.3, angle=-PI/2)`，标签在弧下方，后续元素全部 `next_to` 到标签之下；弧线扫过的区域禁止任何元素（会「遮挡」）
15. **标签对齐（硬性，2026-08-11 事故）**：多个标签对应多个元素（如 token 标签↔权重条）时，**逐个 `next_to` 对准对应元素**（`t("token 2").next_to(bars[0], UP)`），禁止整组 arrange 后居中（组中心与条中心不重合）
16. **公式符号禁止 Text 直渲染**（2026-08-11 事故：`√d` 的 √ 与 d 分离不连贯 3 处）：系统无 LaTeX 时用 `sqrt_group()` 手绘（斜线+顶横线+d，scenes.py 模板内置）；**曲线必须配坐标轴**（`Axes` + `axes.plot`，禁止裸 `FunctionGraph` 悬空）
17. **弧线角度用 arctan2 精确计算**（2026-08-11 事故：拍脑袋 angle=0.5 画过头，弧线未连接 q 与 k₁）：`start_angle=arctan2(q_y, q_x)`、`angle=arctan2(k_y, k_x)-start_angle`
18. **next_to 到非居中父元素后必须 `set_x(0)`**（2026-08-11 事故：rowlab 对齐到 ell 偏移中心 + fit 不缩放 → 右端超界被裁「打分」二字）：fit 过的宽文字 next_to(ell/curve/箭头等 bbox 中心≠0 的元素) 后强制水平居中
19. **否定/纠错视觉（用户拍板 2026-08-11）**：用 `play_red_cross()`（两条粗红线 GrowFromCenter 交叉 + 弹跳，模板内置）盖住被否定的元素，**文字本身用 WHITE**——禁止红色文字 + 单条斜线（红叉已表达否定，文字红色与叉撞色）

### Step 6 渲染验证

```bash
# 先低质量冒烟（快），抽帧检查布局/中文渲染/越界
python3 -m manim render -ql --disable_caching scenes.py S1 S2 ...
# 封面单帧（-s 只渲染最后一帧）
python3 -m manim render -qm -s --disable_caching scenes.py Cover
# 再高质量渲染（1080×1920@30fps，输出在 media/videos/scenes/1920p30/）
python3 -m manim render -qm --disable_caching scenes.py S1 S2 S3 S4 S5 S6 S7 S8
```

`-ql` 帧上逐项过（每项都是事故换来的，勿跳）：
1. 元素完整：无出画布、无截断（对照安全区规范）
2. 无相互重叠：同屏元素间不压叠（允许刻意叠放的 z_index 场景）
3. 无压 footer/标题：底部 y>1800 只应有 footer，顶部 y<120 只应有标题
4. 代码审查：场景内每个 mobject 都能沿 next_to/arrange 链追溯到锚点，无裸 move_to 魔法数字
5. 像素级贴边扫描（必做，肉眼常漏）：每场景抽 70% 时间点帧，非背景像素到画布边缘距离 ≤2px 即为超界（2026-08-10 事故：S5 标签组总宽 8.3 单位 > 画布 8 单位，「左」/「块」字各被裁一半）
6. 框内文字溢出：每场景 30%/60%/90% 三档抽帧逐个框目测（badge 首字母被裁、token 块长英文溢出、9 字描述超框）；动画中帧（30%/60%）检查 FadeIn 中间态无错位
7. 箭头语义：弧线起终点在正确元素上（循环箭头贴元素顶=「帽子」）；链路折线箭头行间位置正确
8. 弧线遮挡：弧线扫过区域内不得有文字/框/标签——像素验证先排除底部字幕区（y>1450 黄色像素=字幕），再判断黄/绿元素相对位置

⚠️ `-qm` 输出目录名按像素高度叫 `1920p30`（不是 1080p30）；`-ql` 是 15fps 只用于布局验证。

### Step 7 一键构建（mux + 拼接 + 字幕 + 烧录）

```bash
python3 scripts/manim_video_build.py content/<日期>-<主题>/shipinhao \
    --speed 1.0 --tail 0.1 --out 成品.mp4
```

- `--speed` 是 **atempo 微调参数**（改语速不用重渲染 Manim，与 TTS 的 speed 1.15 无关，默认 1.0）；`--tail 0.1` = 段间缓冲 0.1s
- 脚本内置：逐段 atempo → 44.1kHz 立体声标准化（MiniMax 原生 24kHz mono 升采样，~192kbps AAC）→ mux → concat → SRT/ASS 字幕（拆长句 + 段内按字数比例分配时间）→ **整行字幕 + `{\fad(150,80)}` 快速淡入**（2026-08-12 起默认，`--typewriter` 切回逐字）→ 黄色字幕烧录（MarginV=210 品牌条上方，字号 75）→ 静音段验证输出
- **画质（2026-08-10 实测固化）**：Manim CLI 没有 `--crf` 参数（v0.20.1 默认 crf=23 写死），提画质需渲染后对 `media/videos/scenes/1920p30/S*.mp4` 逐个重编码（build 是 `-c:v copy`，会拷贝重编码后的流）：
  ```bash
  for f in media/videos/scenes/1920p30/S*.mp4; do
    ffmpeg -y -v error -i "$f" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p t.mp4 && mv t.mp4 "$f"
  done
  ```
  纯色背景+矢量动画压缩性极强：crf 23→14 码率仅 ~300→~370kbps，crf 10 也只有 ~530kbps——**crf 14 即视觉无损**，别指望拉高码率（二压按内容复杂度分配码率）。烧字幕会增加 ~20% 码率（字幕是画面最高频区域）

### Step 8 验证 + 归档

```bash
# 六查：
# 1) 字幕：抽首/中/尾帧，品牌条上方 y∈[1610,1690]（距底 230-310px）有黄色像素（r>180,g>150,b<120）
# 2) 内容不越界：对 build_S*.mp4（无字幕）抽每页最后一帧，距底 200-441px 区域（y∈[1479,1720]）
#    无非背景像素（品牌条带 y∈[1706,1734] 除外）
# 3) 内容占屏：每页内容最低点距底 ≤800px（跨度 ≥40% 屏高），且 ≥399px（两行字幕上方）
# 4) 音画：silencedetect 最长静音段应 ≈ tail（0.1s 级），句子间停顿 <1s 正常
# 5) 品牌尾卡：最后一场景抽帧，品牌图 + 黄色关注引导 + 当期文章标题可见
# 6) 时长 ≈ Σ(配音)+N×tail；封面 <标题>-封面.png 存在且为 1080×1920
```

- **SRT 必须改名**（不能与 mp4 同名，VLC 会叠加显示同名 .srt）
- 产物归档 `content/<日期>-<主题>/shipinhao/`：`<标题>-成品.mp4`、`<标题>-封面.png`、`<标题>-字幕备份.srt/.ass`、`storyboard.md`、`scenes.py`、`tts.txt`、`full.txt`、`tts/`、品牌圆角图

## 生效决策表（用户拍板，勿再返工）

| # | 决策（当前生效） | 沿革（被取代的旧值） |
|---|---|---|
| 1 | 段间缓冲 0.1s + 成片静音验证 | 曾段尾 2.5s 缓冲静音被否（「中间的停顿，非常不爽」） |
| 2 | 语速 **speed 1.15 + pitch +2**（2026-08-10 试听定稿） | 曾 1.0x 原速（嫌慢）、1.2x（嫌快）、1.2/+5（太亮太急） |
| 3 | 尾卡四要素：品牌图 + 黄色「关注「数解AI」」+ 当期文章标题 +「查看公众号文章」引导 | 曾只有文字尾卡；曾缺当期标题 |
| 4 | 字幕：**75 号**、MarginV=210（品牌条上方）、**整行 + `{\fad(150,80)}` 淡入**、拆句阈值 26 | 曾 44 号→100 号→75 号；曾打字机逐字（「不要逐字」） |
| 5 | 内容占屏 ≥40%，内容最低点距底 **399~800px** | 曾 501px 上限被否（字幕 1 行时内容可下探） |
| 6 | 布局原子化：VGroup + arrange + 锚点链 + 安全区，禁裸坐标 | 曾逐元素 move_to 魔法数字，换分辨率即越界重叠 |
| 7 | 框内文字限宽 0.72~0.85（含嵌套框），`boxed()` 工具 | 曾 6 处溢出事故（Transformer/WordPiece/9 字中文） |
| 8 | 弧线：侧边/下方起终点、扫过区禁元素 | 曾贴顶「帽子」弧、穿越下方内容被否 |
| 9 | ≥5 节点链路蛇形两行；禁止假占位符 | 曾单行硬塞每框 1.47 单位；曾 [—] 凑数被否（「非常丑陋」） |
| 10 | FadeIn shift ≤0.1；验证抽动画中帧 | 曾 0.2 位移暂停逐帧看到错位 |
| 11 | **整段配音 + 段尾过渡句 + 时间戳切分**；默认 speech-2.8-turbo | 曾逐段 TTS（段间话题跳跃生硬）；曾 hd（贵） |
| 12 | 时长门禁：生成前 `wc -m` 预估（×0.19~0.20）；软上限 4 分钟，**≤4:20 不返工** | 曾生成后报超长反复返工（6.5→5.1→4.7 分钟） |
| 13 | 动画节奏 = 台词时间轴；`pad_to_voice()` 兜底，静止 ≤20% | 曾动作挤前 1/3 后 2/3 画面僵住（FP4 复盘） |
| 14 | 转折前停顿用 `<#0.5#>`；拟声标签整段生成可用 | 曾 `(inhale)` 被否（只管发声不管停留） |
| 15 | 封面内容集中在**中间 3:4 安全区**（y∈[240,1680]），上下留装饰 | 曾全幅布局被视频号 3:4 裁剪切断标题（2026-08-11 手工重调封面） |
| 16 | 完播率三件套：**开场 3 秒钩子 + 段间悬念钩 + 结尾预告&互动** | 曾平铺直叙，完播率低（2026-08-11） |
| 17 | 否定/纠错视觉：**`play_red_cross()` 动态大红叉**（两笔 GrowFromCenter + 弹跳）+ **白色文字**（2026-08-11 注意力视频 3 处） | 曾红字 + 单条斜线被否（「文字就不要用红色了」「红叉叉最好加一个动态效果」） |
| 18 | **√d 用模板内置 `sqrt_group()` 手绘**（斜线+顶横线+d，Text 渲染 √ 与 d 分离不连贯）；系统无 LaTeX 时禁用 MathTex | 曾 Text 直写 √d 被否（3 处不连贯） |
| 19 | **boxed()/fit() 只缩小不放大**（`if width > limit` 才 set_width） | 曾无条件 set_width 放大短字符（Q/K/V/追/猫/qᵢ 顶出框，2026-08-11 四连发） |

## 常见坑（快速自查，细节见正文对应步骤）

1. 场景末尾忘调 `pad_to_voice()` → 画面提前定格（Step 5）
2. 中文乱码/方块 → `Text(..., font="Noto Sans CJK SC")`（Step 5）
3. `-ql`（15fps）低质量渲染直接当成品 → 成品必须 `-qm`（30fps）（Step 6）
4. VLC 同名 SRT 叠加显示 → 字幕备份改名 `xxx-字幕备份.srt`（Step 8）
5. 渲染输出目录猜错 → `-qm` 输出 `media/videos/scenes/1920p30/`（按像素高度命名）（Step 6）
6. logo/品牌图背景色与画布不一致 → 先裁圆角透明 PNG（PIL `rounded_rectangle` mask）（Step 5）
7. 配音稿写公式符号 → TTS 卡顿 2s+（实测 ‖Q‖‖K‖cosθ 停 2.18s）；生成后必须扫段内长静音（≥1.5s），有则口语化重跑（Step 3.8 / Step 4）
8. `boxed()`/`fit()` 忘加「只缩小不放大」→ 短字符被放大顶出框（Q/K/V/追/猫/qᵢ，2026-08-11 四连发）（Step 5.9）
9. Text 直渲染 `√d` → √ 与 d 分离不连贯 → 用模板内置 `sqrt_group()` 手绘（Step 5.16）
10. 标签组整组居中不对准对应条/卡 → 逐个 `next_to` 对准（Step 5.15）
11. 裸 `FunctionGraph` 无坐标轴 → 曲线悬空，必须 `Axes` + `plot`（Step 5.16）
12. 弧线角度拍脑袋 → 画过头/对不齐，用 `arctan2` 算起止角（Step 5.17）
13. 宽文字 `next_to` 到非居中元素后超界 → `set_x(0)` 强制居中（Step 5.18）
14. 删变量后 FadeOut 残留引用 → NameError，改完 `grep` 复查（2026-08-11 S8 slash→cross）
15. 红字+斜线表示否定 → 用户否：改 `play_red_cross()` 动态大红叉 + 白色文字（Step 5.19）

## 发布要点（同 gemini-video-to-shipinhao SKILL）

1. 画面内不能放可点击链接——品牌尾卡只引导「关注/搜索」
2. 官方可点击入口 = 发布时的**扩展链接**（挂公众号文章；需公众号绑定视频号 + 文章已群发）
3. 全屏模式链接默认隐藏：不选位置 + 文案只留一行；长视频文案 ≤100 字
4. 封面关键内容必须在**中间 3:4 安全区**（y∈[240,1680]）内，主页 3:4 裁剪后完整（见 Step 5 封面安全区）
