---
title: "Muon 怎么省一半显存？优化器只记一份账"
author: "数解AI"
date: "2026-08-06"
type: "解密篇"
series: "DeepSeek 技术解密"
keywords: ["Muon", "优化器", "Newton-Schulz", "正交化", "AdamW", "显存", "DeepSeek-V4"]
illustration_type: "infographic / flowchart / comparison"
illustration_density: "per-section"
illustration_style: "notion editorial"
illustration_palette: "warm graphite with cyan accents"
illustration_backend: "zairouter / gpt-image-2"
illustration_count: 5
---

# Muon 怎么省一半显存？优化器只记一份账

## 文章定位

- 本篇是 DeepSeek 技术解密系列的新一篇，对应 DeepSeek-V4 Technical Report §2.4（Muon Optimizer）与 §3.5.1（Muon 的高效实现）。
- 兑现 07-10 优化器篇与 07-27 预训练篇埋下的 Muon 预告弧线（两处原文引用 + 粗分组校准）。
- 与 07-10《学习率怎么自动调？Adam 优化器拆给你看》构成「原理篇 → 解密篇」映射：Adam 是通用原理，Muon 是 V4 的工程答案。
- 主线冲突：**AdamW 的隐形开销（显存账）**——每个参数记两份账（m/v），V4-Pro 1.6T 参数 → 优化器状态 ~3TB；Muon 用矩阵级正交化（Newton-Schulz）替代 v_t，状态减半。
- 数学深度：**全量推导模式**。公式 8-10 组，正文 3800-4500 字。
- 实验：双实验（NS 收敛性 κ 扫描 + 窄谷轨迹对比），标注「机制演示，不是官方性能基准」。
- 知识补充：延伸 Kimi K2 的 MuonClip（兑现 07-10 第二个伏笔）。
- 下一篇预告：mHC（顺接 K=V 文末已有预告）。

## 核心结论

1. AdamW 为每个参数维护两份状态（m_t 和 v_t），总占用 ≈ 2× 参数量。参照系：V3（671B 参数）用 AdamW，BF16 下优化器状态约 2.7TB（笔记/计算一致）；V4-Pro（1.6T 参数）若全量 AdamW 会翻到 6TB 量级。Muon 只保留 m_t，v_t 那份（1.6T 参数对应约 3TB 量级）被直接省掉——优化器状态约减半。
2. v_t 的几何本质是 per-element 自适应缩放，等价于「对角近似的梯度正交化」；Muon 直接对梯度矩阵做完整正交化（投影到 Stiefel 流形 UᵀU=I），因此不需要 v_t——状态减半。
3. 正交化的精确解是 SVD（O(n³)、分支密集、GPU 不友好）；Newton-Schulz 迭代用 2× GEMM 逼近矩阵逆平方根 X=(GᵀG)^{-1/2}，二阶收敛，κ<10 时约 5 次迭代即可。
4. V4 官方分组：Muon 用于绝大多数参数，AdamW 留给 embedding、prediction head、RMSNorm 权重；Muon 超参 momentum=0.95、weight_decay=0.1、更新矩阵 RMS 缩放到 0.18。
5. Muon 与 MoE 天然协同：正交化后每个 expert 的更新范数恒等于 √min(m,n)，从优化器层面压制 expert collapse。
6. 顺带：Newton-Schulz 迭代在 BF16 下数值稳定（论文 §3.5.1），与 V4 的 FP8 低精度训练路径兼容。

## 标题与摘要

### 标题

**Muon 怎么省一半显存？优化器只记一份账**

（教程攻略型 ⭐⭐⭐⭐：关键词「优化器」前置 + 「怎么」高频句式 + 「只用一半显存」具体痛点；18 字 ≤ 22；单术语）

### 摘要

Muon 怎么省一半显存？训练 1.6 万亿参数的模型，光「记住怎么更新」就要占约 3TB 显存。AdamW 给每个参数记两份账（动量 m 和方差 v），Muon 优化器用 Newton-Schulz 迭代把梯度矩阵正交化，直接省掉 v——状态减半，收敛还更快。DeepSeek-V4 为什么敢把绝大多数参数交给它？（含 2 个搜索关键词：Muon、优化器状态）

## 正文结构

### 0. 开头：还没开始训练，3TB 显存已经没了（约 250 字）

开场画面：V4-Pro 是 1.6T 参数的模型，但「模型本身」不是训练时唯一的显存大头。在参数、激活之外，还有一个容易被忽略的隐形账户——优化器状态。AdamW 给每个参数记两份账，光这笔账就要 ~3TB。

悬念：07-10 篇结尾说过「Adam 的文章还没写完，但下一章已经开始」——这一章，来了。

### 1. 回应弧线：两篇前文的承诺，今天兑现（约 250 字）

- 引 07-10 篇原文：「2024 年，Keller Jordan 提出了 Muon 优化器——不再像 Adam 那样逐元素缩放，而是对整个参数矩阵做 Newton-Schulz 迭代，把梯度更新矩阵正交化……这篇我们后面单独讲。」
- 引 07-10 篇：「Kimi K2（2025）率先全量采用 Muon 的改进版 MuonClip……DeepSeek-V4（2026）紧随其后，把大部分参数换成 Muon 优化器。」
- 校准：07-10 篇粗分组说「只留 embedding 和输出层给 AdamW」；论文 §4.2.2 的精确分组是：Muon 用于绝大多数参数，AdamW 用于 **embedding、prediction head、所有 RMSNorm 权重**。本篇按论文口径给精确表。
- 本篇只回答一个问题：为什么换？省了什么？怎么做到？

### 2. AdamW 的隐形开销：每个参数两份账（约 450 字）

简短回顾 AdamW 更新式（回链 07-10 篇，不重复推导）：

$$
m_t = \beta_1 m_{t-1} + (1-\beta_1)g_t, \qquad v_t = \beta_2 v_{t-1} + (1-\beta_2)g_t^2
$$

$$
W_{t+1} = W_t - \eta \frac{\hat{m}_t}{\sqrt{\hat{v}_t}+\varepsilon}
$$

显存账：m 和 v 各一份，总占用 ≈ 2× 参数量。BF16 下 V4-Pro（1.6T 参数）：
$1.6\text{T} \times 2\text{B} \times 2 \approx 3.2\text{TB}$。

提问：m_t 是动量，v_t 是方差——**v_t 到底在做什么？能不能省掉？**

### 3. v_t 的几何本质：AdamW 在做的是一次「粗糙的正交化」（约 550 字）

#### 3.1 标量视角

$g_i / \sqrt{v_i} \approx \operatorname{sign}(g_i)\cdot O(1)$：v_t 让每个维度的更新幅度归一化到同一量级，相当于「每个维度一套自适应学习率」。

#### 3.2 矩阵视角

对 $W \in \mathbb{R}^{m\times n}$，不同奇异值方向的梯度尺度差异巨大；AdamW 的 per-element 缩放是一种**粗糙的近似正交化**——它把矩阵展平成 $mn$ 维向量做对角缩放，丢失了矩阵的行空间/列空间结构。

#### 3.3 预条件三层表（数学深度点）

| 方法 | 预条件矩阵 P | 精度 | 代价 |
|---|---|---|---|
| Newton 法 | $H$（Hessian） | 完美 | $O(n^3)$ 不可行 |
| Natural Gradient | $F$（Fisher 信息矩阵） | 很好 | $O(n^2)$ 仍太贵 |
| AdamW | $\operatorname{diag}(\sqrt{v})$ | 粗糙 | $O(n)$ 可行 |

$v_i = \mathbb{E}[g_i^2]$ 正是 Fisher 信息矩阵的对角元素：**AdamW ≈ 对角 Fisher 预条件**。

结论：AdamW 只调每个坐标轴的缩放，处理不了轴间耦合；Muon 想做的是完整的矩阵级正交化——所有方向更新幅度**完全相等**。

### 4. Muon：把梯度投影到正交流形（约 900 字，核心推导节）

#### 4.1 目标与精确解

设梯度矩阵 $G$（经动量平滑后），目标是找到最近的部分等距矩阵 $\hat{G}$，使 $\hat{G}^\top \hat{G} = I$（Stiefel 流形 $\mathcal{V}_n(\mathbb{R}^m)$）。

精确解：$G = U\Sigma V^\top \Rightarrow \hat{G} = UV^\top$。但 SVD 是 $O(\min(m,n)^3)$，GPU 上分支密集、不高效。

数学重述：求 $X = (G^\top G)^{-1/2}$（矩阵逆平方根），则 $\hat{G} = GX$。

#### 4.2 Newton-Schulz 迭代的推导（全量推导）

求解 $X^{-2} = A$（其中 $A = G^\top G$）等价于找 $f(X) = X^{-2} - A = 0$ 的根。对矩阵函数做 Newton 法：

$$
X_{k+1} = X_k - f'(X_k)^{-1} f(X_k)
$$

对 $f(X) = X^{-2} - A$，计算导数项后得到迭代式：

$$
X_{k+1} = \frac{1}{2} X_k (3I - X_k X_k^\top)
$$

（正文给出一步化简说明：这是 Newton 法求矩阵逆平方根的经典结果；用 $X_k^\top X_k$ 形式给出标准写法。）

**实现中的 5 阶版本**：经典 NS 是 3 阶多项式（系数 1.5 / −0.5），收敛较慢；Muon 官方实现用 5 阶多项式迭代（NS-5，系数 a=3.4445, b=−4.775, c=2.0315），收敛更快，5 次迭代即可把奇异值拉近 1。正文只陈述 Muon 官方实现（Keller Jordan 博客）与 Kimi K2 报告可确认的事实，不冒充 V4 论文 §2.4 的具体阶数（该页在提取文本中缺失）。

收敛后 $\hat{G} = G X_\infty$ 即正交化结果。

#### 4.3 二阶收敛与条件数（数学深度点）

收敛的充分条件：初始化 $X_0$ 使 $\|X_0^\top X_0 - I\| < 1$，实践中取 $X_0 = G^\top / \|G\|_F$。

二阶收敛：误差每一步平方衰减

$$
\|X_{k+1}^\top X_{k+1} - I\| \le c \cdot \|X_k^\top X_k - I\|^2
$$

条件数 $\kappa = \sigma_{\max}/\sigma_{\min}$ 决定迭代次数：κ<10 → 5 次；κ>100 → 10-15 次。

**条件数几何**（承接 07-10 篇的椭圆直觉）：矩阵把单位圆映射成椭圆，κ = 长轴/短轴 = 椭圆扁度。κ=1 是圆碗，梯度直指最低点；κ≫1 是窄谷，梯度与最优方向几乎垂直，走之字。

**动量为什么先做**：单步梯度受 mini-batch 噪声影响，奇异值方差大；动量 $M_t = \beta M_{t-1} + (1-\beta)G_t$ 是指数加权平均，拉低瞬时峰值，$\kappa(M_t) < \kappa(G_t)$。

#### 4.4 为什么 GPU 友好

| 操作 | 复杂度 | GPU 友好度 |
|---|---|---|
| SVD | $O(n^3)$，分支密集、sequential | ❌ |
| Newton-Schulz 每步 | 2× GEMM | ✅ Tensor Core 友好 |

### 5. 双实验：数字替我们验证（约 350 字 + 表格）

用 `experiment.py` 做两个机制演示（**不是官方性能基准**）：

- **实验 1：NS 收敛性**。构造 κ=3/8/50/200 的矩阵，画 $\|X_k^\top X_k - I\|$ 随迭代的衰减曲线，对照 SVD 精确解 $UV^\top$，验证二阶收敛与「κ 越大迭代越多」。
- **实验 2：优化轨迹**。窄谷二次型 $f(x)=\tfrac12 x^\top A x$（大 κ）上，对比 Adam（对角缩放）与 Muon（正交化）的迭代路径：Adam 之字震荡、Muon 直走；输出每步更新方向与最优方向夹角。

### 6. 完整更新规则与 V4 实践（约 700 字）

#### 6.1 Muon 更新规则（伪代码）

```
每步 t:
  1. G ← ∇L(W_t)
  2. M_t ← β·M_{t-1} + (1-β)·G     # 只留一阶动量
  3. Ĝ ← NewtonSchulz(M_t)          # 正交化，替代 v_t
  4. W_{t+1} ← W_t − η·RMS-rescale(Ĝ)
```

对比 AdamW：省掉 v_t（状态减半）、省掉 ε；增加 Newton-Schulz 计算量（但 GEMM 主导，很快）。

#### 6.2 V4 官方分组表（论文 §4.2.2）

| 参数类型 | 优化器 |
|---|---|
| 绝大多数参数（含 Expert FFN 线性层） | **Muon** |
| embedding module | AdamW |
| prediction head | AdamW |
| 所有 RMSNorm 权重 | AdamW |

Muon 超参：momentum=0.95、weight_decay=0.1、**更新矩阵 RMS 缩放到 0.18**（为复用 AdamW 学习率）。AdamW 超参：β₁=0.9、β₂=0.95、ε=1e-20、weight_decay=0.1。

#### 6.3 与 MoE 的协同：从优化器层面防 expert collapse（数学深度点）

AdamW 下热门 expert 梯度范数远大于冷门 expert → 正反馈 → collapse。Muon 正交化后：

$$
\|\hat{G}_{\text{hot}}\|_F = \|\hat{G}_{\text{cold}}\|_F = \sqrt{\min(m,n)}
$$

每个 expert 更新范数完全相同——与路由侧的 bias trick 形成双保险。

分块正交化：256 个 expert 的矩阵独立做 NS（如 $2048 \times 7168$），完美并行，条件数可控。

#### 6.4 与 ZeRO 的冲突（论文 §3.5.1，一句话带过）

Muon 需要完整梯度矩阵算更新，与按元素切分的 ZeRO 冲突；V4 用 hybrid ZeRO bucket 分配（knapsack 算法 + <10% padding 开销）解决；论文还指出 NS 迭代在 BF16 下数值稳定，MoE 梯度随机舍入到 BF16 同步、通信减半。

### 7. 延伸：Kimi K2 的 MuonClip——为什么 Muon 更快，也更危险（约 450 字，知识补充）

- 兑现 07-10 伏笔：Kimi K2（2025，arXiv:2507.20534）全量使用 Muon 改进版 MuonClip，15.5T token 训练零 loss spike。
- **MuonClip 的真实定义**：Muon + weight decay + RMS matching + **QK-Clip**。QK-Clip 不是裁剪更新方向，而是更新后按 per-head 缩放 W_q / W_k 投影权重，把注意力 logits 限制在阈值 τ=100 内（logit 爆炸是 Muon 大模型训练的主要不稳定源）。
- **为什么 Muon 更容易 logit 爆炸（论文 Appendix E）**：Muon 的正交化让更新矩阵所有奇异值相等 → 满有效秩 → 更新方向与权重奇异向量的对齐概率更高 → 谱范数累积增长；而 Adam 的更新矩阵谱偏斜（少数大奇异值主导、低有效秩），增长更慢。QK 内积是谱范数的平方，于是被急剧放大。
- 对照：V4 用「RMS rescale + 梯度裁剪 + 按 expert 分块」稳定化，Kimi K2 用 QK-Clip——两种路线，同一个目标：让正交化更新不失控。
- **交叉验证**：V4 把每个更新矩阵的 RMS 缩放到 0.18，Kimi K2 用 0.2·√max(n,m)（Moonlight 沿用 0.2）——数字接近并非巧合，都是把 Muon 更新的 RMS 对齐到 AdamW 更新量级（0.2 左右），以便复用 AdamW 学习率。
- 呼应 KV 篇延伸 Kimi K3 的惯例；不替 Kimi 脑补设计动机，只陈述公开报告事实。

### 8. 回扣与结尾（约 200 字）

回扣开头：省掉的 3TB 不是凭空消失——优化器状态减半意味着同样的 GPU 能装更大的 batch、更长的上下文，或者更便宜地训练同规模模型。这正是 V4 敢训 33T token、把序列长度拉到 1M 的条件之一（论文摘要：faster convergence and greater training stability）。

下一篇预告：这套激进结构能训稳，还有另一半功劳来自残差连接——**mHC（流形约束超连接）**：为什么普通残差在 61 层会「传话传没」。

开放式问题：如果显存不再是瓶颈，你会为了更快的收敛改用 Muon 吗？还是继续信任 Adam 的稳定性？评论区聊聊。

## 配图计划

1. `00-cover.png`：封面标题「Muon 怎么省一半显存？优化器只记一份账」；画面：两本账本压塌一边天平，另一边一本账本平衡——暗示 m/v 两份账 vs 一份账，不出现未经核验的数字。
2. `01-adam-two-ledgers.png`：AdamW 双账本结构（m_t / v_t 公式卡片 + 2× 参数量显存条）。
3. `02-preconditioning-ladder.png`：预条件三层阶梯（Newton → Natural Gradient → AdamW）+ 椭圆变圆的示意图。
4. `03-newton-schulz-iteration.png`：NS 迭代式 $X_{k+1}=\frac12X_k(3I-X_kX_k^\top)$ 与二阶收敛曲线（误差每步平方）。
5. `04-trajectory-compare.png`：窄谷地形上 Adam 之字路线 vs Muon 直线下降的轨迹对比图（对应实验 2）。
6. `05-muon-v4-strategy.png`：V4 分组表 + RMS rescale 0.18 + expert 范数拉平示意（对应 6.2/6.3）。

## 来源与核验口径

- [DeepSeek-V4 Technical Report, arXiv:2606.19348](https://arxiv.org/abs/2606.19348)：§2.4 Muon Optimizer、§3.5.1 Efficient Implementation of Muon、§4.2.2 Training Setups（分组与超参）。
- Muon 原始论文：Jordan, Keller et al., "Muon: An optimizer for hidden layers in neural networks"（arXiv:2405.02793，2024）与 Liu et al. 2025（V4 引用双出处）。
- 07-10 优化器篇（已发布，微信 URL）：弧线原文出处。
- [Kimi K2 技术报告（arXiv:2507.20534）](https://arxiv.org/abs/2507.20534)（Moonshot AI，2025）：MuonClip 定义（§2.1）、QK-Clip 机制、15.5T token 零 loss spike、为什么 Muon 更易 logit 爆炸（Appendix E）——已 web 核验。
- Obsidian 笔记《DeepSeek 第 6 课 · Muon 优化器》《第 12 课 · V4 Technical Report 全景导读》：数学推导框架参考。
- 实验：`experiment.py` 自包含 NumPy 实现，仅机制演示。

## 自检清单

- [ ] 标题 ≤22 字、关键词前置、单术语、过 6 条自检。
- [ ] 开头有回应弧线小节，引用 07-10 原文并校准粗分组。
- [ ] 主线始终围绕「AdamW 隐形开销/状态减半」展开，不散。
- [ ] Newton-Schulz 迭代式有完整推导过程（Newton 法求 X⁻²=A）。
- [ ] 公式 8-10 组，独立公式 `$$...$$`、内联 `$...$`。
- [ ] 论文数据（分组、超参、0.18、33T/32T、BF16 稳定）标注来源，不把推测写成官方原话。
- [ ] 实验标注「机制演示，不是官方性能基准」。
- [ ] 文末有 3-5 个话题标签、合集导航、mHC 预告、开放式问题、关注引导。
- [ ] 预告弧线两处（Muon 单独讲 + MuonClip）都兑现。
- [ ] mHC 只作预告与分组原因，不展开（独立主题）。
