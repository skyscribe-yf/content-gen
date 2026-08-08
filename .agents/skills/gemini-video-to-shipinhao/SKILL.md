---
name: gemini-video-to-shipinhao
description: 把 Gemini Notebook（NotebookLM）生成的视频加工成视频号成品——MiMo ASR 生成字幕、对照公众号文章校对、自动检测并去除 Gemini logo、烧录黄色字幕、自动探测并替换片尾品牌页为关注卡。Use when user mentions "视频号", "gemini 视频", "notebooklm 视频", "去 logo", "给视频加字幕", "片尾", "shipinhao".
version: 2.0.0
metadata:
  openclaw:
    homepage: internal
---

# Gemini Notebook 视频 → 视频号成品

## When to Use

- 用户提供 Gemini Notebook 下载的 mp4，要加工成视频号（shipinhao）发布用成品
- 需要：识别/生成中文字幕、去掉 Gemini Notebook logo、替换片尾品牌页、优化画质

## 前置条件

1. **视频**：Gemini Notebook 下载的 mp4（本流程参考 1280x720/24fps，其他尺寸需调整关注卡布局）
2. **公众号文章**：`content/<日期>-<主题>/weixin.md` —— 字幕校对的唯一基准
3. **API Key**：`XIAOMI_MIMO_API_KEY` 环境变量（MiMo ASR，¥0.5/小时**按秒计费**，几分钟视频约 ¥0.03-0.08）
4. **工具**：ffmpeg、`scripts/mimo_srt.py`、`scripts/burn_shipinhao.py`、Noto Sans CJK SC 字体

## 全流程（7 步）

### Step 1 生成字幕（MiMo ASR）

```bash
python3 scripts/mimo_srt.py video.mp4 --out /tmp/sub.srt
```

- 原理：silencedetect 静音切分（按停顿断句，**不切断句子**）→ 逐段调 `mimo-v2.5-asr`（OpenAI 兼容，base_url `https://api.xiaomimimo.com/v1`，返回纯文本无时间戳，靠段起止拼 SRT）
- 全程背景音乐导致检测不到静音时：`--noise -35`（更灵敏），仍失败则回退固定切片

### Step 2 拆长句（防双行字幕）

超过 40 字的条目按标点（`。！？；，、`）拆分，时间按字数比例分配。原因：libass 自动折行后一条字幕显示成两行，用户会以为是"两条字幕重叠"。

### Step 3 校对字幕（对照公众号文章，必须）

逐条对照 `weixin.md` 核对术语、年份、大小写。MiMo 误听对照表：

| 误听 | 正确 | 误听 | 正确 |
|---|---|---|---|
| 埃德 / 阿当 / atom / item | Adam | 迷网 | Muon |
| RWW | AdamW | S基地 / SDG / S D G | SGD |
| 仓鼠...调索 | 参数...调速 | 水流集气 | 水流不急 |
| 脑囊 | 脑海 | 步长死满 | 步长死板 |
| beta two | β₂ | epsilon | ε |
| 二零二六/二零三六 | **2026**（年份一律阿拉伯数字） | Adam W / ADAM | AdamW / Adam |

### Step 4-6 烧录（全自动：logo 检测 + 片尾探测 + 滤镜链）

```bash
python3 scripts/burn_shipinhao.py video.mp4 /tmp/sub.srt \
    --auto-logo --auto-end-cut \
    --out "content/<日期>-<主题>/shipinhao/成品.mp4"
```

`--auto-logo` 抽 3 帧（20%/50%/80% 时长）多数投票定位右下角水印（固定位置、插图各帧不同被剔除，点阵网格用中位数阈值剥离），输出 delogo 区域。`--auto-end-cut` 从尾部向前找最后一个非品牌页帧（品牌页=白屏>95%），自动回退 0.3s 保险。检测失败才需要手动 `--logo-x/y/w/h`、`--end-cut`。

固化在脚本里的关键决策（不要改回去）：

1. **滤镜顺序 `delogo → unsharp → subtitles`**：delogo 在字幕前，否则长字幕侵入 logo 区时被插值模糊
2. **delogo 区域必须精确**：区域过大会把周围空白/插图卷进插值，产生难看涂抹（用户明确投诉过）
3. **字号补偿**：Noto Sans CJK 字体度量（ascender+descender≈1.45em）使 libass 字号放大 ~1.7x，`FontSize=13` ≈ 实际 21px；设 20 实际渲染 34px 会侵入 logo 区
4. **画质**：静态幻灯片内容 x264 拒绝高码率（`-b:v 2000k` 实测只给 ~600k，2-pass/minrate/qpmin 均无效），正解 = `CRF 11 + preset slow + tune grain + qpmin=0 + unsharp=5:5:0.4`（实测 768k > 原视频 570k）
5. **片尾替换**：concat 拼接 3s 关注卡（深蓝底 `0x16213E` + 三行 drawtext），帧率/音频参数与主视频一致（24fps/44100 mono）

### Step 7 验证 + 归档

```bash
# 三查（抽帧）：
# 1) 字幕：t=0 和 t=长字幕时段，y>680 区域有黄色像素（RGB r>180,g>180,b<120）
# 2) logo：检测区平均亮度 ≥225（干净）
# 3) 片尾：最后 1s 深色占比 >0.9（关注卡），且截断点前后无白屏品牌页
# 4) 时长 = end_cut + 关注卡秒数
```

- **SRT 必须改名**为 `xxx-字幕备份.srt`（不能与 mp4 同名！）
- 产物归档：`content/<日期>-<主题>/shipinhao/成品.mp4` + 字幕备份

## 用户纠正史（每次返工的根因，全部已固化）

| # | 用户纠正 | 根因 | 固化防线 |
|---|---|---|---|
| 1 | 固定 12s 切片切断句子 | 字幕时间轴按固定时长切分 | Step 1 静音切分 |
| 2 | 环境变量是 XIAOMI_MIMO_API_KEY | 用了错误的变量名 | 前置条件写明；`mimo_srt.py` 默认读取 |
| 3 | 几分钟视频会不会亏 | 误以为按整小时计费 | 前置条件注明按秒计费 |
| 4 | 成品放 shipinhao 目录 | 产物位置不明确 | Step 7 归档路径 |
| 5 | 视频里出现"2 个字幕" | 长字幕 libass 折行成两行 | Step 2 拆长句 |
| 6 | 原视频"自带大字幕" | **VLC 自动加载同目录同名 .srt** 叠加显示 | Step 7 SRT 改名 |
| 7 | 字幕要靠底、要黄色、delogo 效果难看 | 白色/MarginV=30/delogo 区域过大（274×84） | 黄色 &H0000FFFF、MarginV=8、区域精确化 |
| 8 | 长字幕被 delogo 搞模糊 | 滤镜顺序 subtitles→delogo | Step 5 顺序反转 |
| 9 | 清晰度不够、字幕上调 | CRF 18 码率低、静态内容 ABR 无效 | CRF 11+tune grain+unsharp；MarginV=8 |
| 10 | 片尾有 Gemini 广告画面 | 品牌页（白屏+logo）留在片尾 | Step 5 关注卡替换 |
| 11 | 视频画面内能否放可点击链接 | 平台规则疑问 | 见"视频号发布要点" |
| 12 | 重烧后字幕和去 logo 全没了 | **手动 trim 原视频拼接，丢了滤镜链** | 禁止手动拼命令，必须走 burn 脚本 |
| 13 | 片尾 Gemini 短暂闪现 | 截断点 488s 晚于品牌页淡入点 487.2s | `--auto-end-cut` 逐帧探测+回退 0.3s |
| 14 | Muon 写错、2026 写成 2036 | 未对照文章校对 | Step 3 必做 + 误听对照表 |
| 15 | logo 位置不要写死 | 每视频位置不同，硬编码坐标会错 | `--auto-logo` 动态检测 |

## 视频号发布要点（供用户参考）

1. **画面内不能放可点击链接**（mp4 非超链接）——关注卡只能引导"关注/搜索"
2. 官方可点击入口 = 发布时的**扩展链接**（挂公众号文章链接；需公众号绑定视频号 + 文章已群发 + 近 7 天 1 万阅读量门槛）
3. 全屏模式下链接默认隐藏：**不选位置 + 文案只留一行**链接才显示；长视频文案 ≤100 字

## 常见坑清单（按事故率排序）

1. **拼接片尾时丢滤镜链**：重烧必须走 `burn_shipinhao.py` 全链路（本项目真实事故 #12）
2. **VLC 同名 SRT 自动加载**：用户会误以为"原视频自带大字幕"（#6）
3. **delogo 区域过大**：插值涂抹难看（#7）
4. **截断点晚于品牌页淡入**：Gemini 画面闪现（#13，品牌页探测判据：白屏>0.95 + 中央暗像素从 0 增长）
5. **字号不补偿**：FontSize=20 实际 34px 侵入 logo 区（#8）
6. **单遍 ABR / 2-pass 提码率**：静态内容无效，用 CRF+tune grain+锐化组合（#9）
7. **抽帧验证避开字幕间隙**：相邻两条字幕之间的时间点抽帧看不到字幕
8. **logo 检测的干扰源**：右缘固定 UI 竖条（排除最右 20px）、底部边缘线（排除最下 3px）、部分页面水印形状不同 Gemini/HunYuan（多数投票 ≥2 帧）、开头标题页可能无水印（采样 20%/50%/80% 时长）
