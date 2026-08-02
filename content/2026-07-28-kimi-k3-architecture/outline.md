# 大纲：Kimi K3 拆解：三轴撑住 2.8T 参数

## 元信息
- 标题：Kimi K3 拆解：三轴撑住 2.8T 参数
- 系列：大模型原理
- 类型：架构全貌篇
- 驱动问题：2.8T 参数不是暴力堆料，而是三条各自的效率优化拼出来的
- 预计字数：2200-2500（含公式）
- 数学定位：每轴都有公式直觉，不推导但让读者「看到」数学在做什么

## 结构

### 开头（~200 字）
场景驱动：Agent 在 50 万 token 代码仓库改了 3 小时，被问「还记得第 37 轮那条不能动支付接口的约束吗？」

引出矛盾：要答对这个问题，靠的不是更大的注意力窗口，而是三个各自解决不同问题的架构选择。

预告三轴：序列方向（KDA）、深度方向（AttnRes）、通道方向（Latent MoE）。

### 一、KDA 轴：序列方向的效率（~400 字）

#### 回顾核心直觉
KDA 让模型不必每次在百万 token 里翻找，而是读一份持续更新的「会议速记」。

#### 数学直觉
普通注意力的成本：

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

生成第 T+1 个 token 时，需要和前面 T 个 KV 配对 → 计算量 O(T)，KV Cache 存储 O(T)。当 T=10⁶ 时，每一步生成都要扫 10⁶ 个历史位置。

KDA 的替代方案——用固定大小状态 S 替代 KV Cache：

$$S_t = \alpha_t \cdot S_{t-1} + k_t \otimes v_t$$

$$\text{Output}_t = q_t \cdot S_t$$

其中 $\alpha_t$ 是学到的衰减门控（delta 机制的核心），$k_t \otimes v_t$ 是新信息的「变化量」。

关键：状态 S 的大小固定，不随序列长度 T 增长 → 处理整段序列的计算量从 O(T²) 降到 O(T)。

#### 关键数字
69 层 KDA + 24 层 Gated MLA = 93 层总配比。KDA 负责高效整理长历史，Gated MLA 负责关键时刻的全局精读。

跳转链接：想深入 KDA 原理的读者回看 [7/20 那篇](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA)

### 二、AttnRes 轴：深度方向的信号（~700 字）——重点

#### 直觉层（~200 字）
传统残差的问题：93 层之后，早期层的信号被层层稀释。AttnRes 的答案：每层可以回去看前面任意层的原始表示。

类比：传统残差像逐层传话（第 100 层听到的是前 99 层转述过的版本）；AttnRes 像允许任何一层直接回去翻前面某层的原始笔记。

#### 数学直觉

**传统残差：**

$$h_l = h_{l-1} + f_l(h_{l-1})$$

每一层只能看到前一层的输出。信息从第 1 层传到第 93 层，需要经过 92 次变换。早期层的特征被压缩、混合、稀释。

**Attention Residuals：**

$$h_l = \sum_{i=0}^{l-1} \alpha_{l,i} \cdot \text{AttnRes}(h_i) + f_l(h_{l-1})$$

其中 $\alpha_{l,i}$ 是第 l 层对第 i 层表示的注意力权重。每一层可以直接「检索」前面任意层的表示，而不是只能看前一层的累积结果。

直觉：传统残差是「链式传递」，AttnRes 是「全连接检索」。第 93 层可以直接回头看第 3 层的原始表示，只要注意力权重认为它有用。

#### 机制层（~300 字）

如果保留每层输出供后续检索 → 内存 O(Ld)，不可行。

**Block AttnRes 解法：**

层按 12 个分块，块内累加（传统残差），块间用注意力检索：

$$\text{Block}_j = \sum_{i \in \text{block}_j} h_i$$

$$h_l = \sum_{j} \beta_{l,j} \cdot \text{Block}_j + f_l(h_{l-1})$$

其中 $\beta_{l,j}$ 是块级注意力权重。

效果：活跃状态从 O(Ld) 压缩到 O(Nd)，N = L/12（块数 << 层数）。

类比升级：不是一个人先猜哪些录音重要，而是分小组管理录音，需要时跨组检索。

### 三、Latent MoE 轴：通道方向的容量（~600 字）

#### 稀疏概念（~200 字）
896 个 Routed Experts，每 token 只激活 16 个（≈1.8%）。2 个 Shared Experts 保持全宽路径。激活参数 104B。

#### 数学直觉

**路由选择：**

给定隐状态 $x$，路由器计算每个专家的分数：

$$g_i(x) = \text{softmax}(W_g \cdot x)_i$$

选择 top-16 专家 $\mathcal{E} = \text{topk}(g(x), 16)$。

**专家输出：**

$$y = \sum_{i \in \mathcal{E}} g_i(x) \cdot E_i(x)$$

其中 $E_i$ 是第 i 个专家的 FFN。

**Latent 投影降维：**

直接对 7168 维隐层做 16 个专家计算太贵。LatentMoE 先投影到低维空间：

$$x_{\text{latent}} = W_{\text{down}} \cdot x \quad (7168 \rightarrow 3584)$$

在低维空间做专家计算，再投影回：

$$y = W_{\text{up}} \cdot \sum_{i \in \mathcal{E}} g_i(x) \cdot E_i(x_{\text{latent}})$$

通信量减半。

#### Quantile Balancing（~200 字）

问题：896 个专家，路由不均衡 → 有的过载有的闲置。

传统方法：手工调平衡超参（敏感、启发式）。

Quantile Balancing 的数学：

对每个专家 i，维护一个可学习的偏置 $b_i$，但 $b_i$ 只影响路由选择（top-k 决策），不影响混合权重：

$$g_i^{\text{route}}(x) = \text{softmax}(W_g \cdot x + b)_i$$

$$y = \sum_{i \in \mathcal{E}} \underbrace{\text{softmax}(W_g \cdot x)_{\text{无 } b}}_{\text{混合权重}} \cdot E_i(x)$$

偏置 $b_i$ 的更新目标：让每个专家被选中的频率趋近均匀分布。通过分位数直接计算：

$$b_i \leftarrow Q_{\text{target}} - Q_i$$

其中 $Q_i$ 是专家 i 当前被选中的分数分位数，$Q_{\text{target}}$ 是目标分位数。

效果：消除手工超参，路由自动均衡。

### 四、Benchmark 速览（~200 字）

精简表格：

| Benchmark | K3 | Fable 5 | GPT-5.6 Sol |
|-----------|-----|---------|-------------|
| DeepSWE | 67.5 | 70.0 | 73.0 |
| SWE Marathon | **42.0** | 35.0 | 39.0 |
| BrowseComp | **91.2** | 88.0 | 90.4 |
| Program Bench | **77.8** | 76.8 | 77.6 |
| GPQA Diamond | 93.5 | 92.6 | 94.1 |
| GDPval-AA v2 | 1686 | 1747 | 1736 |

一句话总结：整体落后 Fable 5 / GPT-5.6 Sol，但在长程编程和 Agent 任务上反超。

### 结尾（~150 字）
回到开头场景：Agent 在第 37 轮找到那条支付约束——靠的是三轴合力。

点题：K3 的 2.8T 不是暴力堆参数，而是把三个方向的扩展效率都推到极限之后，让模型在 1M token 里连续工作成为可能。

定性：开源 AGI 的最新王者——不是最大，是在开源阵营里最先摸到 AGI 门槛。

### 资料来源
- [Kimi K3 官方技术博客](https://www.kimi.com/blog/kimi-k3)
- [moonshotai/Kimi-K3 HuggingFace 模型卡](https://huggingface.co/moonshotai/Kimi-K3)
- [Kimi K3 技术报告](https://github.com/MoonshotAI/Kimi-K3)

### 系列导航
前置阅读：[KDA 长上下文](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA) | [归一化残差](已发布) | [MoE 混合专家](https://mp.weixin.qq.com/s/QdkD0CR2fD-HfY77-gX3Ug)
下一篇预告：RLHF 微调
