# Step 4B 口播录音 + 修音 + 时长/停顿分析（作者本人录音流程）

在 Step 2 选口播模式时走此流程，替代 step4a-tts.md。产物与 TTS 模式同构（`tts/sN.wav` + VOICE_DUR），下游 Step 5/6/7/8 完全复用。

**⛔ 门禁 1 分段录音稿确认（硬性）**：进录音前必须把 `tts.txt` 逐段录音稿（含过渡句）展示给用户，回「go/haole」后再开始录。口播模式下**去掉拟声标签和 `<#0.5#>` 停顿标签**（那是对 TTS 的指令，真人不需要，还会干扰停顿分析）——只在台词里用自然标点引导语气。

**⛔ 门禁 2 时长预估（硬性）**：确认录音稿时用 TTS 公式（`wc -m` × 0.22~0.23）先估基准时长；真人念得通常比 TTS 1.0 稍慢，**给 10-15% 余量**做软上限（默认目标 3-4 分钟、软上限 5 分钟，2026-08-25 拍板），超限先精简录音稿再进录音，禁止录完才报「太长」。

**⛔ 门禁 3 录音环境（硬性）**：提醒用户安静房间、贴近麦克风、手机横持离嘴 20-30cm；每段一口气念完，**句与句之间自然停顿 0.3-0.5s**（这是后续字幕停顿对齐的关键），念错该段重录（文件名覆盖 `sN.wav`）。录音格式不限，`voice_process.py` 会统一转 wav。

**⛔ 门禁 3.5 削波检测（硬性，2026-08-17 新增）**：录音室在每段录制后自动测「0dBFS 满幅样本占比 + 峰值」——**输入增益过高会在录音时直接削波（波形平顶），后期任何修音都救不回来，还会被 loudnorm 放大成爆破音**（GRPO s1/s2 教训：s2 削波样本占 1.3%，成片明显爆破音 + 音色发闷）。
- 削波占比 ≥ 0.05% → 硬门禁：试听页显示红色问题清单、**「确认对应关系」按钮被禁用**，必须调低输入增益/离麦远一点重录
- 削波占比 > 0 但 < 0.05% → 黄色提醒（偏满，建议重录更干净）
- 峰值 < -6dB → 黄色提醒（离麦太远/增益不足，声音闷）
- 试听页 meta 行会显示 `峰值 xxdB · 削波样本 xx%`，待录制页也加了音量提示
- 阈值/文案在 `scripts/voice_studio.py` 顶部 `CLIP_SAMPLE_RATIO` / `CLIP_PEAK_DB` / `CLIP_BLOCK_MSG` / `CLIP_HINT_MSG`

**录音引导节奏（一段一段来，不要一次塞 5-6 段）**：
1. 先把 `tts.txt` 逐段展示，让用户按 S1→SN 顺序录，每段一个文件 `shipinhao/recordings/sN.wav`
2. **录完一段我核对一段**（时长、有无吞字/环境噪音），有问题提示补录，没问题进下一段
3. 全部录完后跑修音 + 分析（见下），再进 Step 5

**录音脚本（scripts/record_voice.py，2026-08-15 新增）**：用 ffmpeg 录音，自动探测麦克风 + 计算窗口。
```bash
python3 scripts/record_voice.py content/<日期>-<主题>/shipinhao --probe   # 探测可用麦克风
python3 scripts/record_voice.py content/<日期>-<主题>/shipinhao --seg S1 --dur 40  # 录 S1，40s 窗口
```
- **麦克风探测**：--probe 自动 arecord -l + volumedetect 选有信号的设备（CM40 USB 麦 48kHz 立体声 / 内置麦 44.1kHz 单声道）
- **窗口计算**：--dur = 预估时长 + 10-15s 余量，避免最后一句被截断（S2 教训）
- **录音后裁剪静音**：scripts/trim_silence.py 自动裁剪头尾静音（处理开头微弱声误判、尾部静音残留），输出 VOICE_DUR

**口播录音室（推荐，`scripts/voice_studio.py`，agent 后台编排）**：`tts.txt` 的每个非空行自动成为一段，段数不限，**禁止把 PPO 或 S1..S8 写死**。agent 负责后台启动、监控 handoff、用户录完回来说「继续」后杀进程：

1. **选可用端口**（bind 0 由 OS 分配，无冲突，勿写死 8787/8788）：
   ```bash
   PORT=$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")
   ```
2. **后台启动 + 健康检查**（PID 落盘，等待期长可能经历上下文压缩，靠文件找回）：
   ```bash
   nohup python3 scripts/voice_studio.py --port "$PORT" content/<日期>-<主题>/shipinhao \
     > /tmp/voice_studio-<slug>.log 2>&1 & echo $! > /tmp/voice_studio-<slug>.pid
   curl -sf "http://127.0.0.1:$PORT/api/state" > /dev/null && echo "OK $PORT"
   ```
3. **把 URL 发给用户**（`http://127.0.0.1:$PORT`），提醒 CM40、离嘴 20-30cm、句间自然停顿 0.3-0.5s、**全部段确认后点「生成制作文件」**；要求录完回来说「继续/haole」。等待期间**只监控 handoff 文件**（每 30-60s 查一次），不轮询 UI、不打断用户。
4. **handoff = `tts/sentence-boundaries.json`**（finalize 完成后写出；同批产出 `tts/sN.wav`、`tts/pauses.json`、`tts/consistency.json`，有人工校正时另有 `tts/manual-boundaries.json`，构建字幕/Manim 时优先级高于自动停顿）。参考 PPO 样例：`content/2026-07-31-ppo/shipinhao/tts/`（sentence-boundaries.json 每段含 duration + 句级 clips）。
5. **用户回「继续」后**：先验证 handoff 完整（JSON 可解析、segments 数 = `tts.txt` 非空行数、每段 duration > 0）——不完整（多半是忘点「生成制作文件」）就提示补点再回；完整则**杀后台进程**并确认退出：
   ```bash
   PID=$(cat /tmp/voice_studio-<slug>.pid)
   kill "$PID"; sleep 1
   ps -p "$PID" > /dev/null && kill -9 "$PID"   # 残留才强杀
   ```
   然后跑门禁 4/5（`recordings/studio-state.json` 的 analysis 含每段 speech_ratio / longest_pause；`tts/consistency.json` 看补偿是否触顶）。
6. **界面行为**（供用户参考，agent 不用盯）：顶部固定探测 **CM40**，找不到或输入电平不足时不偷偷切内置麦（设备显示名不同可显式传 `--mic <匹配词>`）；只放行当前段，倒计时录制，结束即裁首尾静音并按真实句间停顿生成可试听句级片段，不满意直接重录，满意才解锁下一段；自动匹配有误时展开片段编辑器，可删除当前 1 段音频，或把连续 **1–3 段音频** 对应到连续 **1–3 个标点文本块**（删除只改 `trim/sN.wav`，原始 `recordings/sN.wav` 保留）。handoff 生成后才满足「先声音，后动画」门禁。

**口播音频处理（一键，`scripts/voice_process.py`，2026-08-16 新增）**：
```bash
python3 scripts/voice_process.py content/<日期>-<主题>/shipinhao
```
脚本一次完成：
- **修音**：`recordings/sN.wav` → `tts/sN.wav`（highpass 去隆隆声 + `afftdn` 去噪 + `highshelf` 降高频毛刺 + `loudnorm` 响度统一到 -16 LUFS）。滤镜链在 `--filter` 可调（默认 `DEFAULT_FILTER`；底噪大把 `afftdn nf` 从 -25 调到 -30）
- **段间一致性补偿（2026-08-16 新增，解决「某段声音能量不集中/发虚/发闷」）**：用 ffmpeg 波形(`astats` 整体 RMS)+频谱(`bandpass` 分 4 个语音关键频段测 RMS：低160/中低500/中高2k/高5.6k) 分析每段 → 选频谱最均衡的一段为锚 → 每段各频段增益向锚对齐（差 >3dB 才补，单频段 ≤6dB 防失真）→ 再 `loudnorm` 统一响度。体检报告打印「频段能量表 + 补偿量」并存 `tts/consistency.json`；`--no-consistency` 关闭补偿，`--consistency-report` 只读分析现有 `tts/sN.wav` 出报告、不改任何产物
- **时长**：ffprobe 每段 → 打印 `VOICE_DUR`（复制进 scenes.py）
- **削波/电平体检（2026-08-17 新增，录音室内置）**：每段录制后自动测 0dBFS 满幅样本占比与峰值；≥0.05% 硬门禁必须重录（GRPO 教训：s2 录音削波 1.3%，后期救不回、loudnorm 反而放大成爆破音）；峰值 < -6dB 提醒离麦太远。阈值/文案在 voice_studio.py 顶部 `CLIP_SAMPLE_RATIO` 等常量
- **停顿分析**：`silencedetect=noise=-35dB:d=0.35` 每段找句间停顿 → 写 `tts/pauses.json`（句子级停顿边界，供 build 脚本字幕停顿对齐；**语义 = 静音结束点**，即下一句语音起点，非中点；开头 <0.3s 静音过滤）
- **质量参考**：每段打印语音占比 + 最长静音段（语音占比 <15% = 麦太远/环境太吵，提示重录）

**⛔ 门禁 4 录音质量检查（硬性）**：跑完 `voice_process.py` 先看输出——每段语音占比应 >50%（手机近距离收音通常 >70%）、无「某段最长静音 ≥1.5s」的异常长停顿（说明那段念崩了/忘词停顿过长，重录）。**停顿异常长的段必须先重录再进 Step 5**，避免字幕时间轴被异常停顿拖乱。

**⛔ 门禁 5 一致性体检复核（硬性）**：跑完看报告——正常应多数段「补偿无需」或小幅补偿；若**某段单频段补偿触顶（+/-6dB）仍对不齐锚段**，说明那段频响差异过大（如离麦太远、靠墙角闷），`loudnorm`+EQ 救不回，**先重录再进 Step 5**，不要把明显失真的补偿带进成片。

⚠️ **口播时长不稳定**：真人每遍时长都会变，**scenes.py 的 `at()` 必须按最终 VOICE_DUR 写**（不能用 TTS 预估），动画节点直接挂到实际录音时间轴；若录完时长与初稿差很多，Step 5 按实际时长重排动画密度，禁止硬套旧时间轴。
