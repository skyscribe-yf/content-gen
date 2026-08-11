---
title: "上下文并行：1M序列为什么切了会坏？"
author: "数解AI"
date: "2026-08-14"
type: "解密篇"
series: "DeepSeek 技术解密"
keywords: ["上下文并行", "CP", "长上下文", "压缩注意力", "CSA", "HCA", "DeepSeek-V4", "大模型训练"]
illustration_type: "infographic / mechanism / comparison"
illustration_density: "per-section"
illustration_style: "notion editorial"
illustration_palette: "warm graphite with cyan accents"
illustration_backend: "yairouter / gpt-image-2"
illustration_count: 6
---

# 上下文并行：1M序列为什么切了会坏？

## 文章定位

- 本篇是 DeepSeek 技术解密系列「训练系统线」的第二篇，兑现 parallel 篇（08-13）文末预告：「五维里最年轻的 CP——1M 序列怎么拆给多张 GPU、两阶段的通信为什么是压缩注意力的专属设计」。主线：**V4 的上下文并行不是「把序列切几段」这么简单——切完再压缩，才是真正的难点；两阶段通信（边界原料交换 + all-gather 压缩 KV）是压缩注意力的专属设计**。
- 主线冲突（谜题式）：**1M 序列太长，必须切给多张 GPU——但 V4 的一切就坏。** 悬念链：为什么必须切（显存 3.5TB vs 80GB）→ 普通 CP 怎么切（隐含两个假设）→ V4 为什么两个假设全破（压缩后长度不齐 + 压缩窗口跨边界）→ 阶段 1 边界原料交换（补上跨边界压缩块）→ 阶段 2 all-gather + select-and-pad（对齐形状、修好语义）→ 通信量账（9MB vs 72MB，压缩比直接兑换成通信节省）。
- 啊哈时刻（反常识点，文章高潮）：**「压缩」这个为推理省 KV 显存的设计，反过来逼着训练系统重新发明 CP。** 读者以为 CP 难点在「切」（切得均匀、通信少），实际难点在「压缩边界」——切完再压缩，每个 rank 的压缩 KV 长度不齐、压缩窗口还跨边界。普通 CP 的「各切各算、整齐 all-gather」在这里全部失效。
- **同题不同解对照（系列惯例第 7 节，已查证）**：Ring-Attention（Liu et al., 2023）用「击鼓传花」式流水线 overlap 通信；V4 用「先全量 gather 再算」——原因①Ring 假设 KV 块「来一块算一块」，压缩边界跨 rank 时左 rank 必须等右邻居数据就绪，overlap 基础消失；原因②CSA 的 top-k 稀疏选择需要 indexer 先看到全部压缩 KV，Ring 的逐步流水做不到。一句话带过，不展开（正文第 2 节）。
- **归属校准（系列惯例）**：CP 不是 V4 发明——Ring Attention（2023）、LongNet/Striped Attention 等都是长上下文并行先驱；CP 是长上下文时代的新维度。V4 的增量：两阶段通信设计专门适配 CSA/HCA 压缩注意力（V4 报告 §3.5.3），select-and-pad 算子把「形状对齐」与「语义正确」解耦。
- **防炒冷饭边界**：08-04 CSA 篇讲过压缩机制（m/m′、indexer、top-k），本篇不重复，只引用「压缩」概念本身 + 前篇链接；08-10 KV 磁盘篇讲过 KV 分层，本篇不展开；parallel 篇讲过五维并行总览和 CP 定位，本篇不重复五维表，只深入 CP。DualPipe/DeepEP → 08-15 专篇。
- 数学深度：B 级。只算三笔账：显存账（3.5TB 激活 vs 80GB 卡）、阶段 1 通信量（与 T 无关，~KB 级）、阶段 2 通信量（压缩比直接等于节省倍数，9MB vs 72MB）。
- **实验方案（作者确认，2026-08-09 grill 结论）**：「切了会坏」模拟器（experiment.py，纯 Python 无依赖）。随机生成 packed sequences（多序列打包，长度不均）→ 切成 8 个 CP rank → 三种做法对比：①朴素 CP（不交换边界，各 rank 只压本地完整块）；②两阶段 CP（阶段 1 边界原料交换 + 阶段 2 all-gather + select-and-pad）；③单卡基准（整条流在单卡上压缩）。断言：两阶段结果与单卡基准完全一致（entry 序列逐一比对），朴素 CP 有缺块/错块。输出：每 rank 压缩 entry 数分布表 + 正确性对比 + select-and-pad 可视化例子。
- 下一篇预告：08-15 DualPipe/DeepEP——训练时 GPU 在等什么？PP 气泡怎么被前向/反向交叠填满、EP 的 all-to-all 通信怎么藏进计算。
- **开源可核验声明**：V4 2026-04 开源（MIT）；正文数字来自 V4 技术报告 §3.5.3（CP 两阶段原文）、§4.2.1（模型配置）、HF config.json（compress_ratios 交替 4/128、61 层、sliding_window 128），可自查。

## 核心结论

1. **为什么必须切（显存账）**：1M 序列单层注意力 Q+K+V+输出 ≈ 57GB（Q 就 14.3GB），61 层激活 ≈ 3.5TB，一块 H800 只有 80GB——差约 44 倍。Flash Attention 解决了 T×T 的分数矩阵（在线 softmax 分块），但 Q/K/V 这些 O(T) 张量还在。CP 是唯一能把 O(T) 激活压进单卡的手段：切 8 份，每卡 125K token，Q 降到 1.8GB。**CP 不是优化，是必须。**
2. **普通 CP 隐含两个假设**：①本地 token 数 ≈ 本地 KV 数（一一对应、形状整齐）；②边界处理简单（块要么在 rank 内、要么边界好处理）。对普通注意力成立。
3. **V4 一切就坏（两个坏因）**：①训练样本是 packed 的，各序列独立压缩、尾部不足 m 的 token 丢弃 → 每 rank 压缩 KV 长度 < s/m 且彼此不同，all-gather 的形状对齐失效；②压缩窗口要 m 个连续 KV entry，可能横跨两个相邻 rank 的分界线 → 左 rank 只有前半块、右 rank 只有后半块，谁都压不出来。
4. **阶段 1 边界原料交换**：每个 rank 把自己末尾最后 m 个未压缩 KV 发给右邻居，右邻居与本地开头拼成完整块再压缩——传的是「原料」不是「结果」，因为压缩函数定义在完整 m 个 entry 上，半块没有合法输出。通信量与 T 无关：无论序列多长，都是 ~KB 级。
5. **阶段 2 all-gather + select-and-pad**：all-gather 把「形状」对齐（各 rank pad 到统一上界再 gather），select-and-pad 把「语义」修好（去 padding、尾对齐、按 top-k 重排）。两者分工：all-gather 解决通信接口问题，select-and-pad 解决语义正确性问题，不能合并、不能互换。
6. **通信量账（压缩比 = 节省倍数）**：假想直接 all-gather 未压缩 KV 每 rank 72MB/层；压缩后 CSA 层 18MB、HCA 层 0.56MB、平均约 9MB/层（与 parallel 篇口径一致）——压缩 4× 的层省 4 倍，压缩 128× 的层省 128 倍。9MB 在 NVLink 上 ~0.02ms，可被计算 overlap 掉；72MB 则无法隐藏。
7. **主线落点**：V4 的 CP 难点不是 sequence splitting，而是 compression boundary。压缩注意力不是一个孤立算子创新，它向下游训练系统继续施加结构约束。

## 文章结构（预计 3500-4000 字）

### 开头（150 字）
承接 parallel 篇结尾预告「下一站：五维里最年轻的 CP」。悬念开场：把 1M token 切成 8 段、每张卡管一段——听起来像切蛋糕一样简单。但 V4 的答案是：一切就坏。

### 一、为什么必须切：3.5TB 激活的显存账（350 字）
- 1M 序列，Q 就是 1M×7168×2B ≈ 14.3GB；单层 Q+K+V+输出 ≈ 57GB；61 层 ≈ 3.5TB。
- 有人会问：Flash Attention 不是解决了 T×T 分数矩阵吗？对——它把峰值显存压到 O(T)，但 Q/K/V 这些线性于 T 的张量还在，3.5TB 一分没少。
- H800 只有 80GB，差约 44 倍。CP 切 8 份：每卡 125K token，Q 降到 1.8GB。
- 结论：CP 不是优化，是必须。1M 上下文训练，没有 CP 跑不起来。

### 二、普通 CP 怎么切：两个隐含假设（350 字）
- 普通 CP：序列沿 sequence 维切段、每卡持有一段连续 token、各算各的注意力、需要全局信息时通信。
- 它成立依赖两个假设：①本地 token 数和本地 KV 数一一对应、形状整齐；②局部操作只依赖段内数据，边界好处理。
- Ring-Attention 一句话：把 KV 像击鼓传花一样轮流传，来一块算一块，用流水线 overlap 通信（但它的假设是「KV 块可以随时参与计算」——V4 用不了，后面会看到为什么）。
- 铺垫：V4 的压缩注意力把这两个假设同时打破了。

### 三、为什么 V4 一切就坏：两个坏因（600 字，本篇高潮）
- 坏因 1：压缩后 KV 长度不齐。训练样本是多个序列打包的（packed sequences），每个序列按自己的边界独立压缩、尾部不足 m 的 token 直接丢弃 → 每个 rank 实际压缩出的 KV 数 < s/m，而且彼此不一样。普通 CP 喜欢「每个 rank 产出同样形状的张量再整齐 all-gather」——现在形状不齐了。
- 坏因 2：压缩窗口跨 rank 边界。CSA/HCA 要求连续 m 个 KV entry 才能压缩。一个压缩块恰好横跨两个相邻 rank 的分界线时：左 rank 只有前半块、右 rank 只有后半块，任何一边单独都无法正确压缩——「半块没有合法输出」。
- 类比：把一摞 4 张一组的照片切给两个人，边界正好切在两张照片中间——谁都没拿到完整的一组。而压缩函数只认完整的一组。
- 落点：所以 V4 的 CP 不能照搬普通 CP，必须重新设计。

### 四、阶段 1：边界原料交换（500 字）
- 设计：每个 rank 把自己末尾最后 m 个未压缩 KV 发给右邻居（rank r → r+1）；右邻居把它们和自己本地开头的 KV 拼起来，在本地完成跨边界的压缩。
- 为什么传「原料」不传「结果」：跨边界块在左 rank 手里根本不是一个完整块，压缩函数定义在完整 m 个 entry 上——半块没有合法输出。硬传半成品会引入「半压缩态」这种中间表示，还得拼接校正再压一次。最干净的办法：send raw → complete on right → compress once。
- ownership 约定：横跨 rank r/r+1 的压缩块，由右侧 rank 成为最终产出者。
- 关键性质：通信量与 T 无关！无论序列多长，每个 rank 只发最后 m 个 KV——m 是压缩比（CSA 4、HCA 128），不是序列长度。~KB 级。
- 反向传播一句话：前向 r→r+1 传原料，反向梯度 r+1→r 传回去，对称。（不展开，一句带过）

### 五、阶段 2：all-gather + select-and-pad（600 字）
- 经过阶段 1，每个 rank 产出一段压缩 KV，但各 rank 长度仍然不同（packed 序列边界不同 + 承接跨边界块的 rank 多一两个 entry）。
- all-gather 要求形状整齐 → 先 pad 到统一上界，再 gather。gathered blob 形状整齐，但里面是「有洞」的——padding 不对应任何真实压缩块，直接喂给 attention 会污染分数。
- select-and-pad：去 padding、把 padding 集中到尾端、按每条路径的需求重排（HCA/indexer 要全量 valid entry，CSA sparse 要 top-k 选中的紧凑视图）。
- 数字例子（cp_size=2, m=4）：Rank 0 产出 [C0, PAD, PAD, PAD]（valid=1）、Rank 1 产出 [C1, C2, C3, PAD]（valid=3）→ select-and-pad 后 [C0, C1, C2, C3]。
- 一句话分工：all-gather 把通信接口的形状对齐；select-and-pad 把语义正确性还给各条路径。不能合并（通信中重排会变不规则、用不了标准 NCCL）、不能互换。
- 三条路径的可见范围：HCA/indexer 静态可预计算；CSA sparse 必须 indexer 跑完才知道 top-k——这也是为什么必须 gather 完之后才能算。

### 六、通信量账：9MB vs 72MB（400 字）
- 阶段 1：~KB 级（CSA 层 m=4：4×576B≈2.3KB；HCA 层 m'=128：128×576B≈74KB），与 T 无关。
- 阶段 2：每 rank 压缩 KV 分片 = 125K/m × 576B → CSA 层 ~18MB、HCA 层 ~0.56MB，平均 ~9MB/层（与 parallel 篇口径一致）。
- 假想直接 all-gather 未压缩 KV：125K×576B ≈ 72MB/层——压缩后省 ~8 倍（平均口径）；单看 HCA 层省 128 倍。压缩比直接兑换成通信节省倍数。
- 呼应 parallel 篇：EP 单层 16GB vs CP 9MB——差近千倍，所以 CP 走 NVLink、EP 走 IB。
- 9MB @ NVLink ~0.02ms，可被计算 overlap 掉；72MB 藏不住。

### 七、实验：切了会坏模拟器（450 字）
- 设计：随机生成 packed sequences（多个序列、长度不均）→ 切成 8 个 CP rank → 三种做法对比：朴素 CP / 两阶段 CP / 单卡基准。
- 结果：朴素 CP 的压缩 KV 序列与单卡基准不一致（跨边界块消失）；两阶段 CP 与基准逐一比对完全一致。select-and-pad 可视化例子。
- 表格：每 rank 的 entry 数（基准 vs 朴素 vs 两阶段）+ 正确性断言。

### 结尾（200 字）+ 下一篇预告
- 收束：CP 的难点不是「切」，是「切完还要压缩」。两阶段通信 = 阶段 1 补边界原料 + 阶段 2 对齐形状、修好语义——这是压缩注意力的专属设计，也是「注意力公式变了，训练并行不能原封不动」的实例。
- 下一篇预告：08-15 DualPipe/DeepEP——训练时 GPU 在等什么？PP 气泡怎么被填满、EP 通信怎么藏进计算。
- 一个问题留读者 + 近期热门 + 点赞/关注引导 + 话题标签（#DeepSeek技术解密 #上下文并行 #长上下文 #大模型训练 #数解AI）。

## 实验设计（experiment.py「切了会坏」模拟器）

- 目标：把「压缩窗口跨边界」「压缩后长度不齐」变成可运行、可验证的代码。
- 核心逻辑：
  - 压缩函数：m 个连续 KV entry → 1 个 compressed entry（指纹求和，便于断言比对）；压缩必须落在同一序列内，序列尾部不足 m 的丢弃。
  - packed sequences：随机生成若干序列（长度不均），拼接成一条 token 流。
  - 切成 k=8 个 rank，每 rank 连续 s 个 token。
  - 三种做法：
    1. 单卡基准：整条流按序列边界压缩 → entry 序列 E_ref。
    2. 朴素 CP：每 rank 只压本地完整块（忽略跨 rank 边界块）→ E_naive。
    3. 两阶段 CP：阶段 1 每 rank 把末尾 m 个未压缩 KV 发右邻居，右邻居拼出跨边界块；阶段 2 各 rank 产出 + all-gather + select-and-pad → E_two。
  - 断言：E_two == E_ref（逐一比对）；E_naive != E_ref（且能数出缺了几个 entry）。
- 输出：
  1. 正确性对比表：每 rank 的 entry 数（基准/朴素/两阶段）+ 缺失数。
  2. select-and-pad 小例子（cp_size=2、m=4）可视化。
  3. 通信量账表（与正文第 6 节数字一致）：阶段 1 / 阶段 2 / 假想 raw 对比。
- 参数可调：m（4 或 128）、k（8）、序列长度分布。默认 CSA 场景 m=4 跑主断言，HCA 场景 m=128 跑冒烟。
- 数字可复核，延续 parallel 篇「并行账本计算器」的透明风格。

## 数字核对清单（写正文时逐项验证）

- [ ] V4 报告 §3.5.3 原文（注意是 3.5.3，不是 3.4.3）：两阶段通信原文、s/m+1、cp_size·s/m、select-and-pad
- [ ] V4-Pro config.json：compress_ratios 交替 [4, 128]、61 层、sliding_window 128
- [ ] 显存账：Q=1M×7168×2B≈14.3GB；单层 Q+K+V+输出 ≈57GB；61 层 ≈3.5TB；H800 80GB → 约 44 倍
- [ ] KV entry 尺寸 576B（64 维 RoPE BF16 + 448 维 FP8，parallel 篇口径）
- [ ] 阶段 1：CSA 层 4×576≈2.3KB；HCA 层 128×576≈74KB（与 T 无关）
- [ ] 阶段 2：每 rank 125K token；CSA 层 125K/4×576≈18MB；HCA 层 125K/128×576≈0.56MB；平均 ≈9MB/层（与 parallel 篇 9MB 口径一致）
- [ ] 假想 raw all-gather：125K×576≈72MB/层 → 平均省 ~8 倍、HCA 层省 128 倍
- [ ] CP=8 → 每 rank 125K token（长上下文训练配置口径，报告未披露具体数值，标注与 parallel 篇一致）
- [ ] Ring-Attention（Liu et al., 2023）一句话带过，不展开
- [ ] 下一篇预告 08-15 DualPipe/DeepEP
- [ ] 标题 ≤22 字自检：上下文并行：1M序列为什么切了会坏？（19 字）
