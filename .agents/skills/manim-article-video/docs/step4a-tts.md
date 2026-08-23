# Step 4A 整段配音 + 时间戳切分（TTS 克隆流程，2026-08-12 定稿）

**⛔ 门禁 1 配音稿确认（硬性）**：跑 TTS 前必须把逐段配音稿（含过渡句、拟声标签）展示给用户确认，回「go/haole」后再批量生成；配音稿有改动时同样先确认。

**⛔ 门禁 2 时长预估（硬性）**：确认配音稿时同步数字符预估总时长，明显超限先精简配音稿再进 TTS，**禁止生成音频后才报「太长了」**。
- 公式：`wc -m tts.txt` 字符数（**含标点/数字/字母，不是纯汉字数**）× 0.22~0.23（speed 1.0 实测折算，曾 1.15 时 ×0.19~0.20）+ 标签开销（每个 `<#0.5#>` 0.5s、每个拟声标签 ~0.3-0.5s）
- 软上限：成片 **≤5 分钟**，默认目标 **3-4 分钟**（2026-08-25 用户拍板「节奏非常快」后收紧，替换 6 分钟软上限）；**预估 ≤4:00 直接做不返工**；用户对本篇另有拍板时以拍板为准（Transformer 全景 2026-08-13 曾拍板 5:30）
- 教训（2026-08-11）：按纯汉字数预估低估 20%+（位置编码按汉字 1198 字估 ~3:50，实际 wc -m 1548 字符 × 0.195 = 5:01）

**配音参数（定稿，勿擅自改）**：
- 模型 **speech-2.8-turbo**（2026-08-12 定稿：便宜且克隆+时间戳兼容，句间停顿略多；hd 仅用户明确要求时用）
- **speed 1.0 + pitch +2**（2026-08-25 用户拍板：降速控节奏，pitch 保留提亮；曾 1.15/+2 被嫌「节奏非常快」）。**仅当用户要求调参时才重出试听**（用 2-3 句台词合成 3 组 speed×pitch，ffplay 播放给用户选）
- **整段生成，不逐段 TTS**（逐段生成段间话题跳跃、收尾生硬）：段尾过渡句（见 step3 第 6 条）+ 一次生成 + 官方句子级时间戳切分

```bash
# ① 整段文本 full.txt = tts.txt 5-6 段合并（含过渡句、拟声标签），一次生成
python3 scripts/minimax_tts.py --text-file shipinhao/full.txt \
    --clone-audio branding/my-voice-denoised.wav \
    --speed 1.0 --pitch 2 --subtitle --out shipinhao/tts/full.wav
# → tts/full.wav + tts/full.subtitle.json（句子级时间戳，免费）

# ② 按台词时间戳切分 5-6 段（scripts/tts_split.py，2026-08-12 固化）
python3 scripts/tts_split.py shipinhao --full tts/full.wav --subtitle tts/full.subtitle.json
# → tts/s1..s6.wav 覆盖旧文件 + 打印 VOICE_DUR（复制进 scenes.py）
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
