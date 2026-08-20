# 音画同步验证与精修（av-sync）

> 2026-08-19 事故复盘沉淀：ai-memory 视频 4:41/4:44 声音滞后 ~2s，历经四轮修复被证伪，
> 最终用 MiMo ASR 内容识别定位根因并精修到 0.01s。本文是「遇到音画同步问题先读这里」的标准方法。

## 1. 根因链（为什么会出现 2s 级错位）

```
pauses.json（silencedetect d=0.35）静音阈值太粗
  → 某句之间的停顿 < 0.35s 漏检 / 检测到的边界本身偏移
  → sentence-boundaries.json 直接拿 [0.0, *pauses, dur] 当字幕边界（边界错固化）
  → build 无校验直接进成品
  → 用户听到 A 句字幕却显示 B 句（听感 = 声音滞后 / 字幕超前）
```

典型错误：silencedetect 在 9.190-9.740 报 0.55s 静音，系统把 9.740 当「GLM-5.2」起点，
实际 9.74-11.25s 还在说「在长序列下同时爆炸」，真静音是 11.253-12.019 —— 错位 2s。

## 2. 第一原则：silencedetect 只能检测「有/无声音」，不能区分内容

- silencedetect / 能量包络 / RMS 曲线 **只能回答「这里有没有声音」**，不能回答「这里说的是哪一句」
- 用静音边界映射句子 = 猜内容，错位 0.4-2.6s 是常态（第四轮 42 个 clip 全量重写仍被证伪的根因）
- **能区分内容的唯一手段是 ASR**（本项目 = MiMo `mimo-v2.5-asr`，`scripts/mimo_srt.py` 的 `transcribe()`）

## 3. 诊断流程（用户报「XX:XX 不同步」时）

```bash
# 1) 提取报点 2s 音频（from 成品.mp4）
ffmpeg -y -v error -ss 252 -t 2 -i 成品.mp4 -ac 1 -ar 16000 /tmp/asr_252.wav
# 2) MiMo ASR 识别内容
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from mimo_srt import transcribe
import os
print(transcribe('/tmp/asr_252.wav', os.environ['XIAOMI_MIMO_API_KEY'], 'zh'))"
# 3) 与 subs.srt 同刻字幕对比 → 得出真实错位量
```

结论判读：
- 语音内容 = 字幕文本 → 同步（可能只是用户记忆偏差，先确认再动手）
- 语音内容 ≠ 字幕文本 → 记下「语音内容 + 时间段」，用第 4 节方法精修

## 3. 边界精修方法（0.1-0.01s 精度）

1. **粗定位**：2s 窗 ASR 扫全段（每 2s 一段），得到「哪 2 秒在说哪句」的完整地图
2. **细定位**：在目标边界附近用 0.8s 窗（步进 0.5s）或 0.5s 窗确认句子起点/终点
3. **交叉验证**：ASR 结果与 silencedetect 真静音（`-30dB d=0.1`）对照 ——
   句子起点应落在「上一句语音结束 ~ 本句语音开始」区间内；若 silencedetect 边界比 ASR 早 >0.4s，信 ASR
4. **写回** `tts/sentence-boundaries.json`（clips 的 start = 语音起点，不是静音边界）
5. **重渲染 + build + 复验**：重新提取报点 2s 音频 ASR，确认语音与字幕文本一致

> ⚠️ 同步更新口径：`sentence-boundaries.json` 是字幕时间轴**唯一权威**；
> build 后 `subs.srt` 每一条都必须落在对应 clip 区间内。

## 4. 防线（build 已内置，勿绕开）

| 防线 | 位置 | 作用 |
|---|---|---|
| `validate_sentence_ts()` | `manim_video_build.py` | build 前校验：SB 文本拼接必须等于配音文本（不一致 fail-fast）；边界单调递增、末边界 ≤ 段时长；SB 与 pauses 漂移 >0.4s 告警（提示人工复核） |
| `MANIM_STRICT_TIMELINE=1` | 渲染环境变量 | `at_clip()` 回退/顺序错立即报错，禁止静默降级 |
| 预发布抽验 | 发布前手动 | 用户报点 ±1s 各提取 2s 音频 ASR，与字幕文本一致才算同步 |

**scenes.py 坑（at_strict 报错）**：动画挂 `at_clip()` 后 `run_time` 不得越过下一个 clip 起点。
S8 c21「评」仅 0.36s，FadeIn 0.6s 从 42.540 推到 43.140 > c22 起点 42.900 → `at_strict(42.900) 回退`。
短句 clip 上的动画 run_time ≤ clip 时长 - 0.05s。

## 5. 完璧修复的流程顺序（本次实测）

1. MiMo 2s 窗 ASR 全段地图 → 确认每句真实位置
2. 细窗精修 sentence-boundaries.json（写回前文本拼接必须 == 段文本）
3. 同步 `recordings/studio-state.json`（S1-S6 可自动同步；数量不一致的段跳过，build 用 SB 优先）
4. `-qm` 重渲染改动的场景 + crf14 重编码（勿动未改场景）
5. `manim_video_build.py --speed 1.0 --tail 0.1` 全量 build
6. MiMo 复验全部用户报点（提取成品音频 ↔ 字幕文本）
7. 记录到 `polish-notes.md`（修复轮次 + 根因 + 验证证据）
