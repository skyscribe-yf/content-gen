---
title: "DeepSeek便宜30倍的秘密：MoE混合专家入门"
author: "数解AI"
digest: "DeepSeek V4 Pro API 价格比 GPT-5.5 便宜 30 倍——不是模型小，是 90% 的参数根本没参与计算。MoE 架构用 Top-k 稀疏路由实现选择性激活，256 个专家每次只请 8 个最懂的干活。便宜的秘密在数学里。"
type: "融合篇"
series: "热点背后的数学"
keywords: ["MoE", "混合专家", "DeepSeek", "稀疏路由", "Top-k"]
cover: 00-cover.png
scheduledPublish: "2026-07-13T08:00:00+08:00"
---

## 🎯 驱动问题

2026年4月，DeepSeek V4 Pro 发布。API 价格：输入每百万 token $0.435，输出 $0.87。

GPT-5.5：输入 $5，输出 $30。Claude Opus 4.7：输入 $5，输出 $25。

**同样的答案，同样的质量——价格差了 10 到 30 倍。**

2026年5月，DeepSeek 宣布这个已经低到离谱的价格**永久化**。不是促销，不是烧钱补贴——是成本结构上真能做到这么便宜。凭什么？

有人说中国劳动力便宜。有人说华为 Ascend 芯片成本低。这些都对，但不触及本质。答案在架构里：**V4 Pro 的 1.6T 参数，每次推理只有 ~160B 在工作。剩下的 90% 在睡觉。**

这不是工程优化。这是数学——一种叫 MoE（Mixture of Experts，混合专家）的架构设计。早在 2024 年底的 DeepSeek-V3 上，这个架构就已经亮了相——671B 总参数，每次只激活 37B，API 价格压到 ¥0.27/百万 token，是当时 GPT-4o 的 1/10。V4 Pro 把它推到了极致：1.6T 参数，激活比从 5.5% 拉到 10%，价格再砍一大截。

在之前的深度学习基础系列里，我们讲了[梯度下降](https://mp.weixin.qq.com/s/V6mGvCVFpTvmC51pNtxiTw)、[损失函数](https://mp.weixin.qq.com/s/zIWqYqYVzEaF1e8P6fcTfw)、[反向传播](https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g)和[Softmax](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw)——合起来就是"模型怎么学"。热点背后的数学系列开篇讲了[为什么上下文越长模型越慢](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q)——那是注意力机制的 O(n²) 硬墙。

这一篇换个视角：**学了之后，模型的结构本身可以被重新设计。** 不是更努力地算，而是更聪明地选——只算必要的部分。

---

## 💡 直觉解释：医院分诊台

你去一家大医院看病。

前台挂着8个科室：心内科、骨科、皮肤科、眼科、消化科、神经科、内分泌科、呼吸科。

你头疼。分诊台的护士看了一眼：“挂神经科和眼科，其他的不用去。”

你只挂了2个号，付了2个挂号费——而不是8个。

**Dense模型（GPT-4o这一类）= 每个病人看所有科室。** 不管你是头疼还是崴脚，心内科、骨科、皮肤科全给你看一遍。知识是全面了，但成本全部包进去。

**MoE模型（DeepSeek-V3）= 分诊制。** 先判断你需要什么，再找对应专家。头疼只挂神经科和眼科，剩下的6个科室完全不启动。

![](01-hospital-triage.png)

DeepSeek-V3有256个专家（科室），每次只激活8个。头疼挂神经科，写代码挂逻辑推理和语法解析，做翻译挂双语对齐和语义理解——不同任务，不同专家组合。

这就是便宜的秘密：**不是跑得更快，而是只跑必要的路。**

---

## 💡 直觉解释：知识存在哪？

你可能会问：为什么专家替换的是 FFN 层，不是注意力层？

这背后有一个关键发现：**大语言模型的大部分知识，存在 MLP（也就是 FFN）层里，不在注意力层里。**

注意力层的工作是"看上下文"——当前这个词跟前面的哪些词有关。FFN 层的工作是"回忆知识"——看到"巴黎"激活"法国首都"、"埃菲尔铁塔"、"浪漫之都"这些关联。2017年那篇著名论文叫"Attention Is All You Need"，但后来的研究发现，**Attention Is Not All You Need**——知识的长期储存，FFN 才是主力。

（注意力具体怎么"看"、Q/K/V 三剑客怎么协作，我们在大模型原理系列里专门拆——这里先记住分工：注意力管"看"，FFN 管"想"。）

这就是为什么 MoE 要替换 FFN 而不是注意力层：**扩展知识容量，最好的办法是让 FFN 层变大、变多、变专。** 注意力层的任务是"看"，FFN 层的任务是"想"——把"想"的部分交给不同专家，让每个专家专精一个领域，模型的整体知识容量就翻了256倍。

![](01b-knowledge-in-ffn.png)

---

## 💡 直觉解释：为什么必须8个，不能1个？

你可能会问：每个token只激活8个专家，为什么不是1个？

因为这8个专家各管不同的事。一个token可能同时需要"语法知识"和"事实知识"——只激活1个专家，另一方面的能力就丢了。

反过来，如果激活全部256个——那MoE就退化成Dense了，成本优势消失。

8个是DeepSeek团队实验出来的甜点：**够多，能覆盖一个token的复合需求；够少，能保持显著的成本优势。**

V4-Pro把这个"甜点"推进了一步：8个激活专家不变，但总专家数翻到256（实际也没增加，只是参数总量从671B涨到1.6T，激活参数从37B涨到~160B）。**专家更大、更精专，但路由策略不变。**

---

## 📐 数学原理：路由器是怎么做决策的

MoE的核心是一个**门控网络**（router）——决定每个token该找哪些专家。

对输入 token x：

> **门控评分：g(x) = softmax(x · W_g)**
> 
>（[Softmax 为什么能把分数变成概率，之前详细拆过](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw)）
> 
> 这给出每个专家的"选中意愿"：g(x) = [0.02, 0.15, 0.41, 0.03, 0.22, 0.01, 0.08, 0.04, ...]
>
> **Top-k 选择：取前k个最大的**
>
> 按上述分数，k=2时选第3和第5个专家。
>
> **输出：y = Σ_{i∈topk} g_i(x) · Expert_i(x)**
>
> 用选中的专家的输出按门控分数加权求和。

三步：打分 → 选人 → 加权。复杂度 O(N_experts × d² × k)，而 Dense FFN 是 O(N_experts × d²)。省掉 (N_experts − k) / N_experts 的计算量——256个里挑8个，省掉 96.9%。

![](02-gating-router.png)

但这里藏着一个坑。

---

## 📐 数学原理：256个专家，谁来管？

有个现实问题：如果所有token都去找同一个专家，那个专家累死，其他人闲着。这叫**负载不均衡**。

传统的解法叫 Auxiliary Loss——在训练目标里加一个惩罚项：

> **L_aux = α · Σ_i f_i · p_i**

其中 f_i 是专家 i 被选中的频率，p_i 是选中概率。这个惩罚项强制模型均匀分配token。

但这里有个 trade-off：α 大 → 均衡好，但惩罚项干扰了主任务的学习（你会为了降低惩罚而牺牲回答质量）。α 小 → 均衡不够。

DeepSeek的答案是**不要惩罚项**。用偏置（bias）代替：

> **选择阶段：g'_i(x) = softmax(x · W_g)_i + b_i → 用来做 top-k 决定谁被选中**
>
> **加权阶段：用原始 g_i(x) = softmax(x · W_g)_i → 用来算每个专家贡献多大**

**关键分离：b_i 只管"谁被选中"，不管"选中后的权重"。**

b_i 不是通过梯度学习更新的——它是纯统计量。训练时每步都监控：

```
if expert_i 被选中次数 > 平均值:
    b_i -= δ    （降权，让它少被选）
if expert_i 被选中次数 < 平均值:
    b_i += δ    （提权，让它多被选）
```

![](03-bias-trick.png)

用生活类比来记：

- **Auxiliary Loss = 高速公路收费站**。每辆车经过都要交"不均衡税"，直接改变司机的驾驶决策。
- **Bias Trick = 智能信号灯**。只在入口处调整车流，不碰车内人的行为。

这就是 DeepSeek MoE 最精妙的设计——负载均衡靠信号灯，不靠收费站。

---

## 🔧 算法实现

用 PyTorch 写出来，核心就这几行：

```python
class MoELayer(nn.Module):
    def __init__(self, dim, n_experts=256, k=8):
        self.gate = nn.Linear(dim, n_experts)  # 路由器
        self.experts = nn.ModuleList([
            Expert(dim) for _ in range(n_experts)
        ])
        self.bias = nn.Parameter(torch.zeros(n_experts))  # 信号灯偏置
        self.k = k

    def forward(self, x):          # x: [N, D]
        raw = self.gate(x)
        gated = raw + self.bias         # 打分 + 偏置 → 选人
        _, topk_idx = gated.topk(self.k)

        # 用原始分数加权（不加偏置！）
        weights = raw.gather(-1, topk_idx)
        weights = F.softmax(weights, dim=-1)

        out = torch.zeros_like(x)
        for eid in range(len(self.experts)):
            mask = (topk_idx == eid)     # 哪些token选了这个专家
            tok, pos = mask.nonzero(as_tuple=True)
            if tok.numel() == 0: continue
            out[tok] += weights[tok, pos].unsqueeze(-1) * self.experts[eid](x[tok])
        return out
```

对比计算量：

| 架构 | 每token FLOPs | 以 d=7168 为例 |
|------|-------------|--------------|
| Dense FFN | O(d² · N_experts) | ~3.3B FLOPs |
| MoE (k=8) | O(d² · k + d · N_experts) | ~0.12B FLOPs |
| **节省** | — | **~27×** |

d · N_experts 那部分是门控打分的开销，远小于专家计算，可以忽略。实际节省 ≈ N_experts / k = 32×。

![](04-moe-dataflow.png)

---

## 🌍 实战：DeepSeek 的 MoE 全景

| 指标 | V3 (2024.12) | V4-Pro (2026) |
|------|-------------|--------------|
| 总参数 | 671B | 1.6T |
| 激活参数 | 37B | ~160B |
| 总专家数 | 256 | 256 |
| 激活专家数 | 8 | 8 |
| 共享专家 | 1 | 1 |
| 激活比 | 5.5% | 10% |

**共享专家**是什么？1个专家所有token都经过——不参与路由选择。它负责捕获通用知识（比如"主语后面通常跟谓语"这种全球通用的语言规律），而256个路由专家负责专项能力。

![](05-v3-v4-comparison.png)

DeepSeek 的 MoE 还有三个工程细节值得一提：

1. **FP8 训练**：Expert FFN 的前向和反向都用 FP8 精度——这部分占 80% 的 FLOPs。精度砍半，计算翻倍，质量不降。（这个我们后面专门写一篇。）

2. **DeepEP 通信库**：256个专家分布在多个GPU上，每次token要跳到不同的GPU找专家。DeepSeek开源了专门的通信库，让跨GPU调度几乎零损耗。

3. **MTP（Multi-Token Prediction）**：除了预测下一个token，还额外预测下下个token——一份计算，两份梯度信号，训练更高效。推理时还能用这个能力做推测解码加速。

---

## 🔄 回路：便宜的秘密藏在"选择性"里

回到开头的问题：**为什么 DeepSeek 比 GPT 便宜 10 到 30 倍？**

不是因为模型小——671B 参数比很多 Dense 模型都大。

不是因为精度低——FP8 训练（后面专门讲）的损失和 BF16 几乎重合。

**是因为 MoE 用数学上等价的方式，实现了选择性计算。** 大语言模型的知识主要存在 FFN 层——注意力负责"看"，FFN 负责"想"。MoE 把 FFN 拆成 256 个专家，每次推理只激活 8 个——计算量是 Dense 的 1/32，但输出是等价的（因为没被激活的专家贡献为 0）。

再加上 Aux-loss-free 的 bias trick——负载均衡靠信号灯而不是收费站——这 8 个专家不是随便选的，而是经过精确路由、各自负责不同能力的。

终极秘密 = **选择性激活 × 数学等价 × 智能调度**。

---

## 📌 一句话总结

DeepSeek API 价格只有 GPT-4o 的 1/10，因为 MoE 架构每次只激活 8/256 个专家——90% 的参数不参与计算，FLOPs 减少 32× 但数学上等价。核心创新 Aux-loss-free bias trick 用非参数偏置做路由选择而不污染梯度，负载均衡靠信号灯而不是收费站。

---

MoE 解决了"谁干活"的问题，但还有一个更深的坑：**每个专家干活要用到的"记忆"（KV Cache），推理时占的显存比专家本身还大。** DeepSeek 用的 MLA 方案把这份记忆压缩了 32 倍——下一篇讲这个。

你对"选择性激活"这种思路怎么看？代码生成和数学推理，哪个更依赖专家分工？评论区聊聊 👇

---

👍 如果觉得有收获，**点赞、在看、收藏**，支持一下～

📖 **深度学习基础系列**：① [梯度下降](https://mp.weixin.qq.com/s/V6mGvCVFpTvmC51pNtxiTw) → ② [损失函数](https://mp.weixin.qq.com/s/zIWqYqYVzEaF1e8P6fcTfw) → ③ [反向传播](https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g) → ④ [Softmax](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw) → ⑤ 残差连接（待发布） → ⑥ 优化器（待发布）

🔬 **热点背后的数学 · DeepSeek 技术解密**：① [AI上下文为什么越长越慢](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q) → ② MoE（本篇）→ ③ MLA（待发布）→ ④ GRPO → ⑤ 注意力进化 → ⑥ FP8 训练

🧠 **大模型原理系列**：从词嵌入→注意力→Transformer→预训练→推理优化，9 篇拆解大模型内部机制。即将启动。

持续更新中。关注「数解AI」，下一篇第一时间推给你。
