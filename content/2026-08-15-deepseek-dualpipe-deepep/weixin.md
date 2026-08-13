---
title: "DeepEP：训练时GPU的空等怎么藏起来"
author: "数解AI"
date: "2026-08-15"
type: "解密篇"
series: "DeepSeek 技术解密"
digest: "训练 MoE 大模型时，GPU 有两处空等：等上游数据（流水线气泡）和等网络通信（all-to-all）。V3 用 DualPipe 把气泡减半、用 DeepEP 把通信藏进计算；V4 进化到 MegaMoE 的 wave 粒度，还给出了「通信什么时候藏得满」的数学判据——C/B ≤ 6144 FLOPs/Byte。"
cover: "00-cover.png"
wechatUrl: null
keywords: ["DeepEP", "DualPipe", "MegaMoE", "MoE通信", "流水线并行", "大模型训练", "DeepSeek-V4"]
---

# DeepEP：训练时GPU的空等怎么藏起来

你花 20 万买一块 H800，训练大模型的时候，它真正在算的时间有多少？

第一次盯训练日志，我发现 GPU 利用率只有六成多，第一反应是模型写错了。排了半天，模型没错——它是在**等**。等两样东西：等上游 stage 的数据传下来，等网络上 token 的 all-to-all 传完。两处空等，就是训练系统里最贵的浪费。

今天把这两处空等拆开，看 DeepSeek 怎么把它们藏起来。

## 一、等谁：两处空等的账

先回到 2048 张 H800 的现场（V3 披露的口径）。1.6T 参数的 MoE 模型按层切成 16 个 stage，micro-batch 一个接一个灌进去。这时候第一处空等出现了。

**等待 1：等上游。** 流水线并行里，每个 stage 必须等上游 stage 算完才能接活。micro-batch 像流水线上的工件，第 1 个 stage 灌入后，后面的 stage 只能干等它一路传下来——工件还没到，工位先空着。调度再怎么排，总有 stage 空转的缝隙，这叫**气泡（bubble）**。1F1B 调度下，每个流水线周期的气泡大约是：

$$\text{气泡}_{1F1B} = (PP-1)(F+B)$$

$PP$ 是 stage 数，$F$ 是前向耗时，$B$ 是反向耗时。PP=16 时，气泡相当于 15 个「前向+反向」块的时间——一大块纯浪费。

**等待 2：等网络。** MoE 层里，每个 token 要被 dispatch 到持有对应专家的 GPU 上算，算完 combine 回来。上一篇文章算过这笔账（五维并行篇，待发布），EP 每层要传约 **16GB**——FP8 dispatch 加 BF16 combine。跨节点的 InfiniBand 带宽只有 NVLink 的约 1/18（900 GB/s 对 50 GB/s），这 16GB 是实打实的等待。

比喻一下：第一种等待像流水线工人等上游工位空出来，第二种像食堂打饭——窗口就一个，谁都得排队。

两处等待性质不同：一个靠**调度**藏，一个靠**通信库**藏。但哲学是同一句：**把空等藏进别的活**。

![GPU 的两处空等：气泡与 all-to-all](01-gpu-waiting.png)

## 二、前菜：DualPipe 把气泡填掉一半

气泡怎么填？V3 技术报告（§3.2.1）的方案叫 DualPipe，两个动作。

**动作 1：双向调度。** 1F1B 只从管道一头灌 micro-batch，尾部 stage 要等很久才有活干。DualPipe 从**两端同时灌**——前向和反向对称地往中间汇合，气泡被两边的活挤掉。

**动作 2：把 chunk 拆碎。** 每个 micro-batch 的 chunk 拆成四段：attention、dispatch、MLP、combine；反向再拆成「对输入的」和「对权重的」。拆得越碎，越容易把缝隙填上——attention 是纯计算，dispatch/combine 是通信，两者交错执行，**计算和通信就重叠了**。

报告里的气泡账（Table 2）：

$$\text{气泡}_{DualPipe} = \left(\frac{PP}{2}-1\right)(F\&B + B - 3W)$$

$F\&B$ 是「前向/反向重叠块」的耗时，$W$ 是反向中算权重的那部分。PP=16 时，块数从 15 降到 7，气泡直接减半以上。实验脚本跑了一下（演示值，见文末）：PP=16 时气泡从 45 降到 12.6，**只剩 1/4**。

代价不是没有：DualPipe 要**两份参数拷贝**。我第一反应是显存账要翻倍——报告里一句话打消了：EP 规模大时，每张卡只持有一小份参数，两份拷贝不贵（激活显存也只多 1/PP）。气泡对比跑出来长这样：

![气泡账：1F1B 与 DualPipe 对比（演示值）](04-bubble-chart.png)

而且这不是 V3 的化石。V4 报告 §3.5.2 明确写了「调整 DualPipe 1F1B 重叠方案」来适配 mHC（[mHC 篇](https://mp.weixin.qq.com/s/VKD1Epopeuj_od-ITbg_dQ)的 6.7% 开销，就是在这个方案上测的）。**V4 还在用 DualPipe。**

![DualPipe 双向调度：两端同时灌入 micro-batch](02-dualpipe-schedule.png)

但气泡只是调度层的等待。层内还有更狠的：all-to-all 那 16GB。

## 三、主菜：DeepEP 怎么把 all-to-all 藏进计算

DeepEP 是 DeepSeek 开源的专家并行通信库（deepseek-ai/DeepEP）。先补一句历史：V3 报告 §3.2.2 里，跨节点 all-to-all 已经有定制内核——token 最多发往 4 个节点，20 个 SM 就能打满 IB 和 NVLink 的带宽。DeepEP 把这条路做成通用库，又补齐了「藏」的三件真货。

**真货 1：专用内核。** 通用 NCCL 的 all-to-all 要为任意数据形状兜底，dispatch 的形状却是固定的（token 数 × top-k × hidden 维）——专用内核把通用性省下的开销全换成带宽。dispatch 和 combine 各自还有高吞吐、低延迟两条路径：大批量要吞吐，per-token 级同步要低延迟，两个场景两套内核。FP8 dispatch 直接把带宽砍半（低精度省带宽的原理，[FP8 篇](https://mp.weixin.qq.com/s/yxrkmxPSZ8CnsFhWZ1bCPA)讲过）。内核是 JIT 编译的——第一次用要先现场编译，慢得想退货，编完就快了。SM100 上 NVLink 实测能到 726/740 GB/s。

**真货 2：异步重叠。** 通信放到独立流上跑，算完的 token 先算，不用等整批就绪。核心就三行伪代码：

```python
handle = deepep.dispatch_async(tokens)   # 发起通信，立刻返回
handle.wait_ready("local_tokens")        # 本地 token 到了就开工
expert_forward(ready_tokens)             # 先到先算，不等整批
```

像食堂窗口：菜齐一碟端一碟，不等整桌的菜全炒好。

**真货 3：极低 SM 占用。** 这是「藏」的物理前提——通信不能抢算力的 SM。通信内核的活主要是等网络，不是算，等数据用不了几个 SM。DeepEP 在 V3 训练场景把 SM 占用从 24 个降到 4-6 个，V2 相对 V1 峰值再提 1.3 倍、SM 再省 4 倍。4-6 个 SM 传 16GB，剩下 100 多个 SM 专心算。通信几乎不占计算资源，计算才填得住通信的坑。

三件真货合起来：all-to-all 从「排队等待」变成「藏在计算阴影里」。

![DeepEP 异步重叠：通信流与计算流并行，token 先到先算](03-deepep-overlap.png)

## 四、藏得满吗？一个数学判据

到这里你可能会问：通信藏在计算后面，**什么时候藏得满**？

先给直觉：$C/B$ 是「每 1 字节带宽要喂多少个 FLOPs」。喂得动（$C/B$ 小），通信就能藏在计算里；喂不动（$C/B$ 大），通信就得排队。

V4 报告 §2.1 给了量化的答案——这是我通读报告时觉得最漂亮的一行公式。记 $C$ 为峰值算力，$B$ 为互连带宽，通信能完全藏住当且仅当：

$$\frac{C}{B} \le \frac{V_{comp}}{V_{comm}}$$

$V_{comp}$ 和 $V_{comm}$ 是每个 token-expert 对的算账。V4-Pro 里，每对要算 6hd FLOPs（SwiGLU 的 gate/up/down 三个投影），通信只要 3h 字节（FP8 dispatch 1 字节 + BF16 combine 2 字节）：

$$\frac{V_{comp}}{V_{comm}} = \frac{6hd}{3h} = 2d = 6144 \ \text{FLOPs/Byte}$$

（h=7168 是隐藏维度，d=3072 是 FFN 中间维度。）

代入 H800 的硬件数字（估算口径）：FP8 峰值约 1.98 PFLOPS。

- 节点内 NVLink（900 GB/s）：C/B ≈ 2200 < 6144 → **藏得满 ✓**
- 跨节点 IB（50 GB/s/卡）：C/B ≈ 39600 > 6144 → **藏不满 ✗**

你可以自己算一遍：1.98×10¹⁵ 除以 9×10¹¹ 是 2200，除以 5×10¹⁰ 是 39600。差一个数量级。

所以单对通信在节点内能藏满，跨节点藏不满。V3/V4 的所有机制——DualPipe 跨 micro-batch 重叠、MegaMoE 跨 wave 重叠——本质都是同一件事：**把一次通信摊到一大批计算上**，把有效 Vcomp/Vcomm 抬过 6144 的门槛。下一节就是这套思路的极限形态。

![C/B 判据：算力与带宽的天平](06-cb-chart.png)

## 五、甜点：MegaMoE 把藏做到 wave 粒度

五维并行篇（待发布）预告过 MegaMoE 的数字（1.50~1.73×、RL 场景 1.96×），今天看机制。

V4 把 dispatch、专家计算、combine 融进一个 mega-kernel，专家切成**wave**：第一波专家在算的时候，第二波专家的数据已经在路上，第三波待发。通信和计算在 wave 边界上无缝重叠——「藏」从 stage 之间、层内，一路藏到 **kernel 内部**。

用上一节的判据说：单个 token-expert 对的通信跨节点藏不满，但把一整批 wave 的计算量摊给一次通信，有效 Vcomp/Vcomm 就被抬过 6144 的门槛。wave 越深，摊得越平，这也是为什么长尾小 batch 的 RL 场景反而最吃这套——batch 小、通信占比大，wave 摊平的收益最明显。

理论加速 1.92×（V4 报告 Figure 5），实测 1.50~1.73×，RL/agent 这种长尾小 batch 场景反而最吃这套（1.96×）。实现开源在 DeepGEMM 里，名字叫 **MegaMoE2**。

顺带一个核验发现：V4 报告全文一次都没提 DeepEP。不是不用了——是进化了：DeepEP 解决「层内怎么藏」，MegaMoE 解决「怎么藏得更满」，同一套哲学的两代答案。

![MegaMoE wave 流水：第一波在算，第二波在路上](05-megamoe-wave.png)

## 结尾

回到开头的问题：20 万的 GPU 为什么空等？两处等待：等上游（气泡）、等网络（all-to-all）。三个粒度的藏：DualPipe 在 stage 之间藏，DeepEP 在层内藏，MegaMoE 在 wave 内藏。藏到最后，判据是一行不等式——6144 FLOPs/Byte。

至此训练系统线收官：五维并行篇（待发布）讲怎么切（层、矩阵、批次、专家、序列），上下文并行篇（待发布）讲怎么切序列，本篇讲怎么藏等待。切得开、装得下、等得起——大模型训练系统这三个坎，DeepSeek 用 V3 的工程积累和 V4 的进化解完了。

一个问题留给你：NVLink 藏得满、IB 藏不满——如果让你设计训练系统，你会把通信往节点内搬（让 EP 尽量留在 NVLink 内），还是升级更宽的互连？留言聊聊你的取舍。

🔥 **近期热门**：
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)

[Softmax为什么不直接取最大值？](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw)

[SFT微调：1万条数据就能让模型听话？](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ)

[残差连接：为什么56层比20层还差](https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg)

[Attention都够了，为什么还要前馈网络？](https://mp.weixin.qq.com/s/vBCzukDlQyB9O6ASgAmlvQ)

[反向传播是什么？AI怎么知道自己错在哪](https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g)

如果这篇帮你算清了「等」这笔账，点个赞 👍、收藏 ⭐ 备用。关注后回复「并行」，我把训练系统系列（五维并行、上下文并行、本篇）的合集链接发你。

#DeepSeek技术解密 #DeepEP #DualPipe #大模型训练 #数解AI

## 资料来源

- [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437)（2024）：§3.2.1 DualPipe（双向调度、chunk 四段拆分、Table 2 气泡公式 1F1B/ZB1P/DualPipe、2 份参数拷贝、near-zero all-to-all overhead）、§3.2.2 HAI-LLM 跨节点 all-to-all（token 限 4 节点、20 SM 打满）——逐项核对原文。
- [DeepEP 开源仓库](https://github.com/deepseek-ai/DeepEP)（deepseek-ai，MIT）：dispatch/combine 高吞吐/低延迟内核、FP8 dispatch、EventOverlap 异步重叠、SM 占用 V3 训练 24→4-6、SM100 NVLink 726/740 GB/s、V2 vs V1 峰值 1.3×。
- [DeepSeek-V4 Technical Report](https://arxiv.org/abs/2606.19348)（2026）：§2.1 MegaMoE（wave 调度、1.50~1.73×、RL 1.96×、理论 1.92×、C/B ≤ 2d=6144 FLOPs/Byte、6hd/3h、MegaMoE2/DeepGEMM）、§3.5.2（DualPipe 1F1B 方案沿用、mHC 6.7%）。
- HuggingFace `deepseek-ai/DeepSeek-V4-Pro/config.json`：hidden 7168、inter_dim 3072、n_routed_experts 384 + 1 shared、num_experts_per_tok 6。
- 实验：`experiment.py` 自包含纯 Python 账本（气泡公式对比 + C/B 判据代入 + 重叠时间线演示），演示值仅说明机制，不代表官方性能。
