---
title: "K=V：一份KV缓存怎么干两份活？"
author: "数解AI"
date: "2026-08-05"
type: "原理篇"
series: "DeepSeek 技术解密"
keywords: ["K=V", "KV缓存", "Partial RoPE", "de-RoPE", "DeepSeek-V4", "CSA", "位置编码"]
illustration_type: "infographic / flowchart / comparison"
illustration_density: "per-section"
illustration_style: "notion editorial"
illustration_palette: "warm graphite with cyan accents"
illustration_backend: "zairouter / gpt-image-2"
illustration_count: 5
---

# K=V：一份KV缓存怎么干两份活？

## 文章定位

- 本篇是 DeepSeek 技术解密 D4 的续篇，承接当晚已发布的《DeepSeek-V4为何不用MLA？》（URL 发布后回填），回答 CSA 篇文末预告的三连问：为什么一个压缩 entry 可以同时当 key 和 value？Partial RoPE 为什么只旋转最后 64 维？输出为什么还要做 de-RoPE？
- 全篇主线是 K=V 的反直觉：K 负责「找什么」、V 负责「取什么」，V4 却把两者压成一份缓存。
- 上一篇 CSA 只做小回顾（双流重叠压缩公式直接复用，不重新推导），RoPE 只做一句话回顾并链接位置编码篇。
- 推荐篇幅：正文约 3,900-4,200 字，公式 6-8 组，配图 5 张（封面 + 4 张正文图）。
- 实验：自包含 CPU 机制验证脚本（numpy），重点演示 de-RoPE 还原；正文只放设定/结果表/必要代码。

## 核心结论

1. 标准注意力里 K 和 V 必须分开：K 负责「和 query 匹配」，V 负责「被加权取出」，两者语义不同，投影也不同。
2. V4 的 CSA 用双流重叠压缩把每个块的 KV 汇成一个 entry，并在 MQA 方式下让这个 entry 同时当 K 和 V（V4-Pro：128 个 query 头共享 1 份 KV，head_dim=512）。
3. Partial RoPE 只旋转向量最后 64 维（config 的 qk_rope_head_dim=64），把「位置职责」集中到 64 维，其余 448 维保持纯内容——这也是 KV 能混合存储（64 维 BF16 + 448 维 FP8）的前提。
4. 同一 entry 又当 V 时，输出是带各自绝对位置旋转的 V 的加权和；de-RoPE 在输出端再按查询位置 -i 旋转，利用旋转群性质 R_{-i}R_j=R_{j-i}，把绝对位置变成相对位置，内容坐标不被污染。
5. Kimi K3 走出另一条路：官方开源实现里 rotary_emb=None 且 assert use_nope，即完全不用 RoPE；与 V4 的「部分旋转 + 输出解旋转」形成对照。

## 标题与摘要

### 标题

**K=V：一份KV缓存怎么干两份活？**（17 字）

标题自检（6 条）：有关键词「KV缓存」且在前半段 ✓；小白能懂 ✓（「一份缓存干两份活」无门槛）；点击冲动 ✓（反常识信息缺口）；无术语堆砌 ✓（K=V 是钩子不是堆词）；≤22 字 ✓；与正文一致 ✓（正文主线就是 K=V）。

### 摘要

注意力里，K 负责「找什么」，V 负责「取什么」，它们本该是两份不同的数据。DeepSeek-V4 却把 KV 压成一份 entry，同时当 key 又当 value。这份缓存怎么干两份活而不乱？Partial RoPE 把位置职责锁进最后 64 维，de-RoPE 在输出端把绝对位置还原成相对位置——位置与内容各归其位。

## 正文结构

### 0. 开头：一份缓存，两份工作（约 300 字）

开场画面：上一期 CSA 篇里出现了一个反直觉的设计——模型把每个块的 KV 压成一个 entry，这个 entry 同时当 key 和 value。读者会立刻想到：K 是用来「找」的，V 是用来「取」的，把两者合并不是会串味吗？

给出悬念：V4 没有让两份工作互相污染，靠的是两把钥匙：Partial RoPE 把位置锁进最后 64 维，de-RoPE 在输出端把位置再解出来。这篇拆开看这两步怎么配合。

承接链接：CSA 双流重叠压缩公式只做 1 段回顾，链接已发布文章（发布后补 URL，未发布标注）。

### 1. K 和 V 为什么本该分开（约 400 字）

标准注意力：

$$
\operatorname{Attn}(Q,K,V)=\operatorname{Softmax}\left(\frac{QK^\top}{\sqrt{d_h}}\right)V
$$

- K：给 query 提供「匹配的靶子」，语义是位置敏感的（哪里说的、离我多远）。
- V：给 query 提供「要取的内容」，语义上应该尽量不受位置干扰（内容本身不因为出现在第 3 句还是第 300 句而改变）。
- 所以正常 Transformer 里 K、V 由两个不同投影矩阵生成，RoPE 也只加在 Q、K 上，V 不旋转。

一句话类比：K 是书页上的「关键词索引」，V 是「正文内容」；索引要告诉你在第几页，正文却不必每行都标注页码。

### 2. 双流重叠压缩：一份 entry 怎么同时当 K 和 V（约 800 字）

#### 2.1 回顾 CSA 的合并动作

CSA 先用两组投影生成两条 KV 流和两条权重流：

$$
C^a=HW^{aKV},\qquad C^b=HW^{bKV}
$$

每 $m$ 个 entry 按权重合并成一个压缩 entry（$a$ 流管当前块，$b$ 流管前一个块，相邻摘要重叠，有效压缩比仍是 $m$）：

$$
C_i^{\mathrm{Comp}}=\sum_{j=mi}^{m(i+1)-1}S_j^a\odot C_j^a+\sum_{j=m(i-1)}^{mi-1}S_j^b\odot C_j^b
$$

#### 2.2 K=V 是 MQA 的极端形式

- 回顾 MQA：多个 query 头共享同一份 K/V。V4 更进一步：压缩后的 entry 直接当 K 又当 V，连 K 和 V 的投影都合并了。
- 事实锚点（V4-Pro config.json）：num_attention_heads=128，num_key_value_heads=1，head_dim=512，compress_ratios 按层交替（CSA m=4，HCA m'=128，论文 2.3.3），index_topk=1024，sliding_window=128。
- 冲突点：同一个向量既要「被匹配」又要「被取出」。如果它在两件事上的表现混在一起，模型就分不清「这段内容重要」和「这段内容合适」。
- 引出解法预告：把职责拆到不同维度上——位置职责交给最后 64 维，内容职责留给其余 448 维。

### 3. Partial RoPE：为什么只旋转最后 64 维（约 700 字）

#### 3.1 RoPE 一句话回顾

位置编码篇已证明：对向量做分块旋转，内积会带上相对位置因子。链接已发布的位置编码文章，不重复推导。

$$
R_\theta=\begin{pmatrix}\cos\theta & -\sin\theta \\ \sin\theta & \cos\theta\end{pmatrix}
$$

#### 3.2 只转最后 64 维

- V4 对 query、KV entry 的**最后 64 维**施加 RoPE（论文 2.3.3；config 中 qk_rope_head_dim=64，head_dim=512）。
- 含义：512 维里 64 维负责「我在哪个位置」，448 维保持「我是什么内容」，位置与内容在维度上物理分离。
- 存储收益（论文 2.3.4）：混合存储——RoPE 的 64 维用 BF16，其余 448 维用 FP8，KV 体积比纯 BF16 近乎减半。
- 类比：图书索引卡片，只有「页码」字段参与排序，书名、作者字段不参与。

#### 3.3 为什么是「部分」

- 全部旋转的问题：位置信息挤进所有维度，V 的内容表示被位置完全包裹，合并 K=V 后内容与位置彻底纠缠。
- 完全不旋转的问题：K 失去相对距离信息，长程匹配退化成纯内容相似度。
- Partial RoPE 取中间态：内容维度保持纯净（可放心压到 FP8），位置维度承担匹配职责（值得用 BF16 保精度）。

### 4. de-RoPE：输出端为什么要把旋转解掉（约 850 字，本篇重点）

#### 4.1 问题：V 带着旋转进入输出

- 因为 entry 又当 V，注意力输出是带旋转的 V 的加权和。设查询在位置 $i$、entry 在位置 $j$，entry 的旋转为 $R_j$：

$$
\mathbf{o}_{t,i}=\sum_j a_{t,j}\,R_j\,\mathbf{v}_j
$$

- 每个 $R_j$ 都带着自己的绝对位置。输出里混进了「第 3 块的旋转」和「第 300 块的旋转」，内容坐标被位置污染（论文原话：naive 输出携带 absolute position embeddings）。

#### 4.2 解法：输出端按 -i 再转一次

- 对输出最后 64 维施加位置 $-i$ 的旋转。旋转矩阵满足 $R_{-i}R_j=R_{j-i}$（角度相加）：

$$
R_{-i}\,\mathbf{o}_{t,i}=\sum_j a_{t,j}\,R_{j-i}\,\mathbf{v}_j
$$

- 结果：每项只剩「entry 位置与查询位置的距离 $j-i$」，绝对位置被消掉，相对位置被保留。
- 这就是「de-RoPE」：不是删掉位置，而是把绝对位置翻译成相对位置。名字里的 de- 是「解旋」而不是「去掉」。

#### 4.3 为什么必须做

- 不做：同一段内容出现在不同位置，输出的语义坐标不同，下游 FFN 无法稳定解读「内容」。
- 做了：内容坐标干净，位置信息仍以相对距离形式存在（模型知道「这句在 30 句之前」），两头都保住。
- 代价：只多一次 64 维的旋转（乘一个稀疏分块旋转矩阵），几乎免费；这也是 Partial RoPE 的 64 维设计让 de-RoPE 变便宜的原因。
- 实验预告：机制演示中会验证「相同内容、不同绝对位置」在 de-RoPE 前后输出的差异。

### 5. 延伸：Kimi K3 干脆不用 RoPE（约 200 字）

- 事实（官方开源实现 moonshotai/Kimi-K3）：modeling_kimi_linear.py 中 rotary_emb=None，且 assert use_nope；config 中 qk_rope_head_dim 为空。
- 对照：V4 是「部分旋转 + 输出解旋转」，K3 是「完全不旋转」。两种路线都在为长上下文重新设计位置信息，说明「RoPE 是不是必须的」已经成为新一代架构的开放问题。
- 边界：K3 的设计动机以官方代码与模型卡为准，不脑补技术报告未披露的理由。

### 6. 效率收口：这份缓存到底省了多少（约 400 字）

官方口径（论文摘要与 2.3.4，标注比较基准）：

- 1M context 下，V4-Pro 推理 FLOPs 约为 V3.2 的 **27%**，KV cache 约为 V3.2 的 **10%**。
- 以 BF16 GQA8（head_dim=128）为基线，V4 在 1M context 的 KV cache 约为基线的 **2%**。
- 拆解来源：压缩（CSA 4:1 / HCA 128:1）+ 单份 KV（K=V）+ 混合存储（64 维 BF16 + 448 维 FP8）+ indexer FP4。
- 明确口径：这些是官方论文数字，不是本文实验测得；机制演示只验证路径正确性。

### 7. 回扣：位置与内容，各归其位（约 300 字）

回到开头：K=V 没有让两份工作串味，因为 V4 把「位置职责」和「内容职责」拆到了不同维度。Partial RoPE 负责锁住位置，de-RoPE 负责在输出端把绝对位置翻译成相对位置。

结尾预告：这套激进设计要在 61 层网络里稳定传播，还差最后一块拼图——mHC（流形约束超连接）。下一篇拆它如何让深层信号不衰减。

## 实验设计（机制验证）

脚本：`experiment.py`（numpy，CPU，自包含），三部分：

1. **K=V 共享路径**：构造压缩 entry 集合，同一数组同时用于 QK 打分与加权求和，验证 MQA 路径形状与数值一致性。
2. **Partial RoPE 维度分工**：随机向量只旋转最后 64 维；验证 (a) 非旋转维扰动不改变内积的相对位置因子，(b) 旋转维内积随相对距离变化。
3. **de-RoPE 还原（重点）**：同一内容向量放在不同绝对位置，比较无 de-RoPE 输出（随绝对位置漂移）与 de-RoPE 输出（只依赖相对距离，绝对位置不变性成立）。

结果表：三组数值对照，正文只呈现结论表；标注「机制演示，非官方性能基准」。

## 配图方案（5 张，zairouter / gpt-image-2）

1. `00-cover.png`（21:9）：一份卡片同时当 K 和 V 的主视觉。
2. `01-k-v-division.png`：K「找什么」/ V「取什么」分工图。
3. `02-dual-stream-entry.png`：双流重叠压缩 → 一份 entry 的数据流。
4. `03-partial-rope.png`：512 维中最后 64 维旋转示意。
5. `04-derope-restore.png`：输出端解旋转，绝对位置 → 相对距离。

prompt 内文字/数字必须与正文一致（64、512、K=V、de-RoPE）。

## 资料来源

- [DeepSeek-V4 论文](https://arxiv.org/abs/2606.19348)（arXiv:2606.19348）：2.3.3 Other Details（Partial RoPE、de-RoPE、滑动窗口、超参数）、2.3.4 Efficiency Discussion（27%/10%/2% 与混合存储）、摘要。
- [DeepSeek-V4-Pro config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/config.json)：head_dim=512、num_key_value_heads=1、qk_rope_head_dim=64、compress_ratios、index_topk=1024、sliding_window=128、max_position_embeddings=1048576。
- [Kimi K3 官方仓库](https://huggingface.co/moonshotai/Kimi-K3)：modeling_kimi_linear.py（rotary_emb=None、assert use_nope）、config.json（无 qk_rope_head_dim）。
- 系列衔接：CSA 篇负责承接上一篇的内容；本文不放未发布的单篇链接，发布后只更新上一期文章自己的 frontmatter 与系列导航。
- 已发布：[位置编码篇](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ)、[注意力机制篇](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw)。

## 质量核查要点

- 标题 6 条自检（见上）。
- 公式全部 LaTeX，独立 `$$...$$`、内联 `$...$`，每组配直觉解释。
- 硬性数字核查：64 维、512 维、27%/10%/2%、CSA m=4、HCA m'=128 均来自论文/config；K3 无 RoPE 来自官方代码。
- 文末 3-5 个话题标签：`#DeepSeek技术解密 #K=V #KV缓存 #位置编码 #数解AI`。
- 尾部导航：DeepSeek 技术解密箭头链（AI上下文慢 → MoE → MLA → V4 注意力 → **K=V（本篇）** → mHC 预告），合集链接。
- 正文不依赖未发布链接；上一篇公开后更新其自己的 URL。
- 实验脚本可复现，结果表与代码一致。
