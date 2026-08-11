# 《BPE分词：AI为什么把文字切成碎片？》视频号分镜脚本

基于 content/2026-07-13-BPE/weixin.md（大模型原理 · 第 1/10 篇）
规格：竖屏 1080×1920 · Manim 动画 · MiniMax 克隆音色配音 + 烧录字幕 · 目标 2-3 分钟

## 段落设计（8 段）

| # | 场景 | 动画要点 | 配音稿 |
|---|------|---------|--------|
| S1 | 开场钩子：strawberry 数 r 翻车 | 「strawberry 里有几个 r？」大字弹出 → 模型答「2 个」红色 × → 正确答案「3 个」绿色 ✓ → 能做微积分的模型，栽在小学生题目上 | (breath) 先考你一道题：strawberry 里有几个字母 r？最先进的大模型，2024 年给出的答案是 2 个。正确答案是 3。能做微积分、能写代码的模型，连数字母都会翻车。它到底是怎么"看"文字的？ |
| S2 | 模型按 token 读字 | 文字「猫」→ 整数编号演示；「文字→token→token ID」三步链；词表 129280 数字强调 | 答案藏在"切字"这一步。神经网络不认识"猫"，也不认识 Transformer。它只认整数编号。分词器先把文字切成 token 片段，再给每个片段一个 ID。DeepSeek-V4-Pro 的词表有 12 万 9280 个条目——但注意，这不是 12 万个完整词，而是能拼出一切的碎片。 |
| S3 | BPE 合并原理 | low/low/lower/lowest 四词 → 拆字符 → pair 统计表（l,o)4 次最高 → 合并 lo → 再合并 low → lowest=low+e+s+t | 那 token 是怎么长出来的？看 BPE 的核心操作。训练语料里有 low、low、lower、lowest。先拆成字符：l-o-w。数相邻字符对：(l,o) 出现 4 次，(o,w) 也是 4 次，最高频。先把 l、o 粘起来，再粘 w。low 就成了一个 token。(gasps) 注意：lowest 拆开是 low、e、s、t——见过的片段变大块，没见过的先保持小块。 |
| S4 | 一句话代码 | 四步循环卡牌：数 pair → 找最高频 → 合并 → 重复；循环箭头转起来 | 把过程写成代码，核心就四步：数 pair、找最高频的一对、合并，然后循环。频率统计，选 pair，合并，更新词表。真实 tokenizer 还要处理空格、Unicode、字节，但骨架就是这个循环。 |
| S5 | 真实 tokenizer：14 tokens | 句子「请用 Python 写一个 Transformer，参数量 7B。」→ 14 个碎片块一字排开；乱码片段 vs ID 两种视角切换 | (sighs) 别被乱码吓到。拿 DeepSeek-V4-Pro 的 tokenizer 切这句话：14 个 token。中文片段打印出来像乱码？那是 byte-level 的"工作现场"——中文先变 UTF-8 字节再合并。看 ID 就清楚了：Transformer 整体一个 token，7B 拆成 7 和 B。乱码只是显示不友好，输入没坏。 |
| S6 | 纯中文 + strawberry | 「今天天气真好，适合出去玩」→ 6 个 token 拆分动画（今天/天气/真好/，/适合/出去玩）；strawberry → st/raw/berry 三块 | 换句纯中文：今天天气真好，适合出去玩，只有 6 个 token：今天、天气、真好、逗号、适合、出去玩。token 的边界不按人类的词划线。再看开头的 strawberry——它被切成 st、raw、berry。(gasps) 模型看到的不是逐字母清单，而是三个碎片。 |
| S7 | 切法影响：token 越多越贵 | 三个字符串对比卡（中文说明/Python 函数/7B + UTF-8）→ 长度差不多 token 数不同；token 多 → 上下文窗口更小 + API 更贵 | 切法为什么影响使用？一句话：token 越多，上下文窗口里能放的原文越少，API 费用越高。三个字符串长得差不多——中文说明、Python 函数、7B 加 UTF-8——token 数却完全不同。所以数"字"不够，数"词"也不够，真正进模型的是 token。 |
| S8 | 方法对比 + 链路总结 + 尾卡 | BPE/WordPiece/Unigram 三卡片；文字→预分词→字节→BPE→token→ID→向量 链路；品牌尾卡（avatar + 关注引导 + 当期标题 + 下一篇预告） | BPE 只是其中一种：WordPiece 选提升模型概率的片段，Unigram 从大词表往删。路线不同，目标一样：常见的短一点，罕见的也能表示。整条链路：文字、预分词、字节、BPE 合并、token、查表拿 ID、嵌入变向量。下一篇，讲 token 的 ID 怎么变成坐标。关注数解AI，一起把大模型原理讲透。 |

## 爆点分布自查

| 段 | 类型 | 位置 |
|----|------|------|
| S1 | 问句钩子 | 段首「strawberry 里有几个 r？」+ 结尾「它到底怎么"看"文字？」 |
| S2 | 数字对比 | 「12万9280」+ 转折「但注意，这不是 12 万个完整词」 |
| S3 | 数字对比 + 短句 | 「(l,o) 出现 4 次」+「先把 l、o 粘起来，再粘 w」 |
| S4 | 短句断句 | 四步循环卡牌节奏 |
| S5 | 转折爆点 | 「别被乱码吓到」+「乱码只是显示不友好，输入没坏」 |
| S6 | 转折爆点 | 「模型看到的不是逐字母清单，而是三个碎片」 |
| S7 | 数字对比 | 「token 越多…费用越高」+ 三字符串对比 |
| S8 | 问句收尾 + 预告 | 「ID 怎么变成坐标」+ 关注引导 |

## 制作流程

1. 配音：`scripts/minimax_tts.py` 逐段生成 S1-S8（`--clone-audio branding/my-voice-denoised.wav`，voice_id 已缓存 author-video-voice-01），ffprobe 记录各段真实时长
2. 动画：每段一个 Manim Scene（S1..S8 + Cover），`construct` 末尾 `pad_to_voice()` 补齐，动画覆盖 ≥80% 配音时长
3. 构建：`scripts/manim_video_build.py` mux 配音 + 无缝拼接 + 黄色字幕烧录（MarginV=210 字号 75）+ 打字机效果 + 品牌尾卡
4. 归档：`content/2026-07-13-BPE/shipinhao/`
