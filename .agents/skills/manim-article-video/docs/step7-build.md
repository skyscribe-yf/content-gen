# Step 7 一键构建（mux + 拼接 + 字幕 + 烧录）

```bash
python3 scripts/manim_video_build.py content/<日期>-<主题>/shipinhao \
    --speed 1.0 --tail 0.1 --out 成品.mp4
```

- `--speed` 是 **atempo 微调参数**（改语速不用重渲染 Manim，与 TTS 的 speed 1.15 无关，默认 1.0）；`--tail 0.1` = 段间缓冲 0.1s
- 脚本内置：逐段 atempo → 44.1kHz 立体声标准化（MiniMax 原生 24kHz mono 升采样，~192kbps AAC）→ mux → concat → SRT/ASS 字幕（拆长句 + 段内分配时间；**时间戳优先级：`recordings/manual-boundaries.json` Web 人工确认 > `tts/sentence-boundaries.json` 逐句 start/end（最高自动优先级，与语音逐句严格对应）> 口播 `tts/pauses.json` 停顿驱动切分兜底 > TTS `full.subtitle.json` 句子时间戳 > 纯字数比例**）→ **整行字幕 + `{\fad(150,80)}` 快速淡入**（2026-08-12 起默认，`--typewriter` 切回逐字）→ 黄色字幕烧录（MarginV=210 品牌条上方，字号 75）→ 静音段验证输出
- **段长用 ffprobe 实测（2026-08-17 固化）**：build 的段时长 = `dur_of(build_SN.mp4)` 实际值（concat 后 AAC padding 会累积漂移 ~0.7s，用 ffprobe 实际段长累计字幕时间轴，否则后半段字幕早于画面）；段边界落在原子内部且距下一字符 >4 字才允许硬切，**英文/数字串（InstructGPT、1.3B、θ 等）保护不拆断**
- **画质（2026-08-10 实测固化）**：Manim CLI 没有 `--crf` 参数（v0.20.1 默认 crf=23 写死），提画质需渲染后对 `media/videos/scenes/1920p30/S*.mp4` 逐个重编码（build 是 `-c:v copy`，会拷贝重编码后的流）：
  ```bash
  for f in media/videos/scenes/1920p30/S*.mp4; do
    ffmpeg -y -v error -i "$f" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p t.mp4 && mv t.mp4 "$f"
  done
  ```
  纯色背景+矢量动画压缩性极强：crf 23→14 码率仅 ~300→~370kbps，crf 10 也只有 ~530kbps——**crf 14 即视觉无损**，别指望拉高码率（二压按内容复杂度分配码率）。烧字幕会增加 ~20% 码率（字幕是画面最高频区域）
