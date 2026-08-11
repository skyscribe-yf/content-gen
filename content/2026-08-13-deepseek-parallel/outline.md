---
title: "1.6T参数怎么塞进GPU？V4五维并行策略"
author: "数解AI"
date: "2026-08-13"
type: "解密篇"
series: "DeepSeek 技术解密"
keywords: ["并行策略", "数据并行", "张量并行", "流水线并行", "专家并行", "上下文并行", "DeepSeek-V4", "ZeRO"]
illustration_type: "infographic / framework / comparison"
illustration_density: "per-section"
illustration_style: "notion editorial"
illustration_palette: "warm graphite with cyan accents"
illustration_backend: "yairouter / gpt-image-2"
illustration_count: 6
---

# 1.6T参数怎么塞进GPU？V4五维并行策略

## 文章定位

- 本篇是 DeepSeek 技术解密系列「训练系统线」的入口，兑现 MTP 篇（08-12）文末预告：「单卡再快也有极限，下一站 1000 块 GPU 怎么分活」——主线是 **V4 训练/推理的五维并行策略（DP/TP/PP/CP/EP），每个维度切一个正交的轴，组合起来让 1.6T 参数在显存、计算、通信三个维度都落进可处理的范围**。
- 主线冲突（谜题式）：**一块 H800 只有 80G 显存，V4-Pro 有 1.6T 参数——差 20 倍，怎么装？** 装下（PP/TP）→ 算快（DP+ZeRO-1）→ MoE 特有（EP+通信账）→ 1M 序列（CP）→ 一块 GPU 的多重身份。悬念链：装得下 ≠ 跑得快 ≠ 通信不爆炸。
- 啊哈时刻（反常识点，文章高潮）：**V4 把 TP 关了（TP=1）**——直觉是「参数越大越要切矩阵」，但 V4 的 MLA/CSA 已把 KV/注意力维度压到极小（KV 每 entry 512 维、压缩 4×/128×），TP 每层都要 all-gather/all-reduce 的通信代价超过收益；DeepSeek 的答案是把「切」让位给 EP（专家天然是散的，切片成本为零）和 PP（层间通信量小）。
- **同题不同解对照（系列惯例第 8 节，需查证后定）**：候选——①Kimi K2 系列训练也用 EP+PP+DP 组合（5D 并行含 TP？需查 K2 报告）；②GLM-5.2 采用 DeepEP（开源库被多家采用），说明「EP 通信优化」是行业共性问题。若查证不到可靠数字，则对照改为「V3 的 4 节点限制 vs V4 取消限制」（V4 报告 §2.1「remove the constraint on the number of routing target nodes」+ 九老师解读：V3 限 M=4 节点降低 IB 通信，V4 取消后靠 Waved-EP 融合 kernel 兜底）——这个对照有据可查、且正好落在 EP 主角线上。
- **归属校准（系列惯例）**：并行策略不是 V4 发明——DP/TP/PP 是 Megatron/ZeRO（2019-2020）时代经典；EP 随 MoE（GShard 2019、Switch 2021）出现；CP 是长上下文时代（Ring Attention 2023）产物。V3 的贡献是「低配硬件上的组合艺术」：2048 张 H800 + 8 卡 NVLink 节点 + 50GB/s IB 跨节点，用 16PP×64EP×ZeRO-1 DP 的组合避开 TP（不用 NVLink 内的高频通信）和 ZeRO-2/3（不抢 IB 带宽），把宝贵的 IB 带宽全留给 EP。V4 增量：①取消路由节点数限制（§2.1）；②Waved-EP/MegaMoE 融合 kernel（§3.1，1.50~1.73×/1.96×）；③CP 两阶段设计适配 CSA/HCA（§3.4.3）；④Muon 下 ZeRO 按矩阵拆分（§3.4.1）。
- **防炒冷饭边界**：08-04 CSA 篇、08-05 KV 篇、08-06 Muon 篇、08-11 Indexer 篇、08-12 MTP 篇均未展开并行策略（已核查各篇标题与正文范围）；推理加速篇（08-03）讲的是 API 延迟构成，未涉及分布式并行。CP 两阶段细节 → 08-14 专篇；DualPipe/DeepEP 细节 → 08-15 专篇；本篇只给概念与预告。
- 数学深度：B 级。不推公式，只讲三个账：显存账（参数×精度×卡数）、EP vs CP 通信量对比（差 1000 倍）、ZeRO-1 为什么"近乎免费"（通信量不变的账）。每个账配具体数字。
- **实验方案（作者确认，2026-08-13 grill 结论）**：并行账本计算器（experiment.py，纯 Python 无依赖）。输入 V4-Pro config（61 层/hidden 7168/1 shared+384 routed/inter_dim 3072/topk 6/FP8 主权重+FP4 专家）+ 硬件参数（H800 80G、NVLink 900GB/s、IB 50GB/s、8 卡节点），输出：①显存账（推理 FP8 要 20 卡、训练加梯度/优化器状态要多少卡）；②五维通信量对比表（PP/EP/CP/DP 每 micro-batch 的 GB 数与耗时，@IB 50GB/s）；③结论数字（EP 是 CP 的 ~1000 倍 → 解释 V4 为什么 EP 走 IB、TP 关闭）。数字可复核，延续 KV-disk 篇算术账风格。
- 下一篇预告：08-14 CP（上下文并行）——过渡线：五维里 CP 最年轻，1M 序列怎么拆给多张 GPU、两阶段通信怎么适配压缩注意力。
- **开源可核验声明**：V3 2024-12 开源（MIT），V4 2026-04 开源（MIT）；正文数字来自 V4 技术报告（§2.1 路由限制、§3.1 MegaMoE、§3.4.3 CP、§4.2.1 模型配置）、V3 技术报告（§3.5 训练配置、2048 H800）、HF config.json，可自查。

## 核心结论

1. **装不下**：V4-Pro 1.6T 参数，FP8 存储 1600GB；一块 H800 80G，推理最少 20 块；训练还要梯度 + 优化器状态（Muon/AdamW 各档），账再翻 2-3 倍。单卡极限先撞上的是显存，不是算力。
2. **切的两个基本动作**：按层切（PP，通信量小、适合跨节点）+ 按矩阵切（TP，层内高频通信、必须 NVLink）。V4 反直觉决策：**TP=1 关闭**——MLA/CSA 把注意力压扁后 TP 的通信税不值，把切片任务让给 EP。
3. **DP 与 ZeRO-1 的免费午餐**：DP 每卡完整模型各算各的 batch，反向结束同步一次梯度；AdamW 优化器状态占参数 ~12 倍显存，ZeRO-1 只切优化器状态、通信量和普通 DP 一模一样（近乎免费）。不选 ZeRO-2/3：梯度/参数通信会跟 EP 抢 IB 带宽。
4. **EP 是 MoE 的主角，也是通信的大头**：专家天然独立，摊到 64 路跨节点，token 通过 all-to-all dispatch 上门、算完 combine 回家；EP 通信量 ~14GB/layer，是 CP（~14MB/layer）的 1000 倍，IB 带宽就是训练系统的命脉。V4 用 MegaMoE 融合 kernel 把通信藏进计算（1.50~1.73×，RL 场景 1.96×）。
5. **CP 让 1M 序列可训练**：序列切段、每卡一段，两阶段 all-gather 压缩 KV（细节 08-14）。
6. **一块 GPU 的多重身份**：一张 H800 同时是 DP replica（同步梯度）/ PP stage（管某几层）/ CP rank（持有一段序列）/ EP group（持有若干专家）；同一层内 Attention 归 CP（NVLink）、MoE 归 EP（IB）——「KV 来找 token vs token 去找专家」，两条通信总线互不阻塞。
7. **低配硬件的组合艺术（归属）**：2048 张 H800 + 8 卡 NVLink 节点 + IB 50GB/s，DeepSeek 用 16PP×64EP×ZeRO-1 DP 把 TP 排除在外、把 IB 带宽留给 EP——不是堆硬件，是把每个通信字节花在刀刃上。

## 文章结构（预计 3000-3200 字）

### 开头（150 字）
承接 MTP 结尾预告「1000 块 GPU 怎么分活」。悬念开场：一块 H800 只有 80G 显存，V4-Pro 有 1.6T 参数——差 20 倍，怎么装？答案不是「更多更大的卡」，是「切」。

### 一、先算账：1.6T 到底要多少块卡（350 字）
- 显存账：FP8 1 字节/参数 → 1.6T×1B = 1600GB → 推理最少 20 块 H800。
- 训练更狠：参数 + 梯度 + 优化器状态（Muon 按矩阵拆、AdamW 两矩），账再翻倍以上——所以训练用的卡数远不止 20。
- 悬念升级：装下只是第一步——装下了怎么不打架？引出三个问题：装下、算快、通信不爆炸。

### 二、装下：按层切（PP）与按矩阵切（TP）（500 字）
- PP：61 层切成 16 个 stage，micro-batch 像流水线流过；通信量小（每 stage 只传激活），适合跨节点；代价是气泡（等待空窗），DualPipe 用前向/反向交叠填满（预告 08-15）。
- TP：一个矩阵切成 N 片、每卡算一片再 all-reduce 合并；层内通信密集，必须节点内 NVLink（900GB/s）。
- 反常识点：V4 的答案是 TP=1（关闭）——MLA/CSA 已把注意力压扁，TP 的通信税不值；「切矩阵」让位给「切专家」（EP 切片成本为零）。

### 三、算快：DP 数据并行与 ZeRO-1（450 字）
- DP：每卡一份完整模型、各算各的 batch，反向结束后 all-reduce 同步梯度——计算与通信天然错峰（算下一层时同步上一层梯度）。
- 显存大头是优化器状态（AdamW 两矩 + master weight ≈ 12× 参数）：10B 模型 FP16 就要 160GB，其中优化器 80GB。
- ZeRO-1：只切优化器状态，通信量和普通 DP 一模一样（reduce-scatter + all-gather 恰好是 all-reduce 的拆解）——「近乎免费」。
- 为什么不切梯度/参数（ZeRO-2/3）：每次 micro-batch 都产生参数量级的通信，跟 EP 抢 IB 带宽。DeepSeek 把 IB 留给 EP。

### 四、MoE 主角：EP 专家并行与通信账（650 字，本篇高潮）
- EP 思路：384 个路由专家摊到 64 路（跨节点），token 通过 all-to-all dispatch 去专家所在的卡、算完 combine 回来。「token 去找专家」，专家是天然切好的，零切片成本。
- 通信账（实验核心输出）：EP all-to-all ~14GB/layer vs CP ~14MB/layer vs PP 点对点几十 MB——EP 是 CP 的 1000 倍，IB（50GB/s）就是命脉。
- V3 的保守：路由限 4 节点内选专家，把 IB 通信归并成 NVLink 转发；V4 取消限制（§2.1），靠 MegaMoE 融合 kernel 兜底——把 dispatch/计算/combine 融进一个 kernel、专家分 wave 流水，通信藏进计算，1.50~1.73×（RL/agent 场景 1.96×）（预告 08-15 DeepEP）。
- 对照：V3 的 4 节点限制 vs V4 的取消限制——同一个问题（IB 带宽）的两种解法。

### 五、1M 序列：CP 上下文并行（300 字，带过 + 预告）
- 1M token 序列单卡放不下 → 按序列切段、每卡管一段（CP rank）。
- 一句话讲两阶段通信（边界传 m 个未压缩 KV → all-gather 压缩 KV），细节、Ring-Attention 对比全部留给 08-14。

### 六、收尾：一块 GPU 的多重身份（400 字）
- 一张 H800 同时是：DP replica（同步梯度）/ PP stage 3（管 Layer 9-12）/ CP rank 5（持有序列 [625K, 750K)）/ EP group（持有若干专家）——四个身份四个正交轴。
- 层内顺序：Attention block ← CP（NVLink 两阶段 all-gather）；MoE FFN ← EP（IB all-to-all）——「KV 来找 token vs token 去找专家」互不阻塞。
- 通信量汇总表（实验输出）：五维各占多少带宽、各自时间量级。

### 结尾（200 字）+ 下一篇预告
- 收束：装下靠切、算快靠各干各的、不打架靠把每个通信字节花在刀刃上——低配硬件上的组合艺术。
- 下一篇预告：五维里最年轻的 CP——1M 序列怎么拆给多张 GPU（08-14）。
- 一个问题留读者 + 近期热门 + 点赞/关注引导 + 话题标签（#DeepSeek技术解密 #并行策略 #大模型训练 #数解AI 等 3-5 个）。

## 实验设计（experiment.py 并行账本计算器）

- 输入常量（全部来自 config.json / 技术报告，脚本内注释标注来源）：
  - V4-Pro：n_layer 61、hidden 7168、n_routed_experts 384、shared 1、inter_dim 3072、topk 6、FP8 主权重、FP4 专家权重、激活 49B/总 1.6T
  - 硬件：H800 80GB、节点 8 卡 NVLink 900GB/s、跨节点 IB 50GB/s（V3 报告披露口径）
  - 并行配置：PP 16、EP 64、CP 8（长上下文）、TP 1（关闭）、DP_replica 2（V3 口径）
- 输出三张表：
  1. 显存账：推理（FP8 权重 1600GB → 20 卡）vs 训练（+梯度 +Muon/AdamW 优化器状态 → N 卡），并算 ZeRO-1 切优化器后每卡省多少
  2. 五维通信量对比（每 micro-batch、每层或每 step 口径，@IB 50GB/s / NVLink 900GB/s）：
     - PP：B×L×hidden×2（几十 MB 级）
     - EP：B×L×topk×hidden×4（~14GB/layer 级，需与笔记口径对账）
     - CP：两阶段 ~14MB/layer（854MB 全模型）
     - DP：ZeRO-1 每 step 一次 all-reduce（模型量级，可 overlap）
  3. 结论行：EP 通信量 / CP 通信量 ≈ 1000 → 解释 V4 的并行决策
- 输出可直接作为正文表格；脚本保留 `--json` 输出便于核查。

## 数字核对清单（写正文时逐项验证）

- [ ] V4-Pro config.json：61 层 / hidden 7168 / 1 shared + 384 routed / inter_dim 3072 / topk 6 / FP4 专家
- [ ] V4 报告 §4.2.1：1.6T 总参 / 49B 激活；FP8 权重口径（FP4 专家 + FP8 其余）
- [ ] V3 报告：2048 张 H800、8 卡节点、16PP × 64EP × ZeRO-1 DP、DP_replica=2（若 V4 未披露则标注 V3 口径）
- [ ] V4 报告 §2.1：「remove the constraint on the number of routing target nodes」原文
- [ ] V4 报告 §3.1：MegaMoE 1.50~1.73× / 1.96×、6144 FLOPs/Byte
- [ ] V4 报告 §3.4.3：CP 两阶段（m 个未压缩 KV + all-gather 压缩 KV、cp_size·m 对齐）
- [ ] 第 16 课笔记通信量表：CP 阶段1 ~63KB/layer、阶段2 ~14MB/layer（854MB 全模型）、EP ~14.3GB/layer——实验脚本须自洽复现
- [ ] NVLink 900GB/s（8 卡 H800 节点）与 IB 50GB/s 数字（V3 报告/九老师解读双重核对）
- [ ] ZeRO-1「通信量不变」论证（all-reduce = reduce-scatter + all-gather 的拆解）
- [ ] 10B 模型 160GB 账（参数 20G + 梯度 20G + AdamW 状态 80G + master 40G）——九老师文章口径，可作正文例子
