---
title: "K=V：一份KV缓存怎么干两份活？"
series: "DeepSeek 技术解密"
author: "数解AI"
type: "原理篇"
keywords: ["K=V", "KV缓存", "Partial RoPE", "de-RoPE", "DeepSeek-V4", "CSA", "位置编码"]
digest: "KV 缓存为什么能让 K 和 V 共用一份？Partial RoPE 把位置收进最后 64 维，de-RoPE 再还原为相对距离。"
cover: "00-cover.png"
wechatUrl: null
---

前两篇我们先把长上下文的问题拆成两层。在[MLA 那篇](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg)里，MLA 解决 KV cache 存多少。
上一篇[DeepSeek-V4 为何不用 MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)里看的是 CSA/HCA：注意力究竟要看多少？现在再往下追，DeepSeek-V4 里还有一个更反直觉的设计：模型把每个块的 KV 压成一个 entry，再让这个 entry 同时当 key 和 value。

直觉上这说不通。key 是拿来「匹配」的，value 是拿来「取出」的，两份职责不同，数据怎么能是同一份？

更麻烦的是位置。RoPE 旋转是加在 key 上的，因为匹配需要知道「这句话离我多远」。可如果同一个向量又当 value，它带着旋转被加权求和，位置信息就会渗进输出。V4 是怎么让一份缓存干两份活而不串味的？

答案藏在两个机制里。Partial RoPE 把位置职责锁进最后 64 维，de-RoPE 再把绝对位置翻译成相对位置。这篇把两步拆开看。

## 一、K 和 V 为什么本该分开

先回到标准注意力：

$$
\operatorname{Attn}(Q,K,V)=\operatorname{Softmax}\left(\frac{QK^\top}{\sqrt{d_h}}\right)V
$$

- K 是「靶子」：query 和它做内积，分数决定这段内容值不值得注意。它必须知道位置，因为「第 30 句的话」和「第 300 句的话」匹配意义不同。
- V 是「内容」：被权重加权后取出来。内容本身不该因为出现在第 3 句还是第 300 句而改变。

所以正常 Transformer 里，K、V 由两个不同的投影矩阵生成，RoPE 只加在 Q、K 上，V 不旋转。

一句话类比：K 是图书索引上的「关键词」，V 是「正文」。索引必须标注页码，正文却不需要每一行都写着页码。

![K 找什么，V 取什么：两份职责为什么分开](01-k-v-division.png)

在 [注意力机制那篇](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw) 里我们说过，attention 本质是「按匹配度做加权平均」。K=V 相当于把「索引」和「正文」合成了一页纸。它必须同时回答两个问题：这段内容合适吗？它是什么？

## 二、双流重叠压缩：一份 entry 怎么诞生

CSA 怎么把一份 entry 压出来，[上一期](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)已经推过，这里只留关键两步。

先用两组投影生成两条 KV 流和两条权重流：

$$
C^a=HW^{aKV},\qquad C^b=HW^{bKV}
$$

每 $m$ 个 entry 按权重合并成一个压缩 entry。$a$ 流管当前块，$b$ 流管前一个块，相邻摘要共享一部分范围，所以有效压缩比仍是 $m$，不是 $2m$：

$$
C_i^{\mathrm{Comp}}=\sum_{j=mi}^{m(i+1)-1}S_j^a\odot C_j^a+\sum_{j=m(i-1)}^{mi-1}S_j^b\odot C_j^b
$$

然后就是关键一步：**压缩后的 entry 不再拆成 K 和 V，而是同一个向量直接同时充当二者**。论文把这条路径称为 shared key-value MQA：每个压缩 entry 既是 key，也是 value。V4-Pro 的 CSA/HCA 有 128 个 query 头。
这些头共享同一份压缩 KV，head_dim 是 512（见[论文](https://arxiv.org/abs/2606.19348)第 2.3.1 节和 [config.json](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/config.json)）。

![双流重叠压缩：两条流汇成一个 entry，同时当 key 和 value](02-dual-stream-entry.png)

这里出现了一个真正的冲突：同一个向量，既要被「匹配」，又要被「取出」。如果两种职责混在一起，模型会分不清「这段内容值得注意」和「这段内容恰好匹配」。

V4 的解法是**按维度分工**。
在这条注意力路径里，最后 64 维承担位置相关的旋转。其余 448 维保持未旋转的内容分量。这就是 Partial RoPE 的由来。

## 三、Partial RoPE：为什么只旋转最后 64 维

[位置编码那篇](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ) 讲过 RoPE 的核心：对向量做分块旋转，内积就会带上相对位置因子。旋转矩阵长这样：

$$
R_\theta=\begin{pmatrix}\cos\theta & -\sin\theta \\ \sin\theta & \cos\theta\end{pmatrix}
$$

普通做法是整个向量都旋转。V4 只旋转最后 64 维。[论文第 2.3.3 节](https://arxiv.org/abs/2606.19348)明确了这一点；config 里 `qk_rope_head_dim=64`，`head_dim=512`。

可以把它理解成：512 个维度里，64 维负责「我在哪个位置」，448 维保留「我是什么内容」。位置和内容在维度上物理分离。

这个设计还有直接收益（见[论文第 2.3.4 节](https://arxiv.org/abs/2606.19348)）。既然只有 64 维需要精确位置，KV 就可以混合存储：64 维用 BF16，448 维用 FP8。缓存体积比纯 BF16 近乎减半。

类比一下：图书索引卡上，只有「页码」字段参与排序，书名、作者这些内容字段不参与。参与排序的字段需要精确（BF16），内容字段可以粗糙一点（FP8）。

![512 维里只有最后 64 维旋转，位置与内容各占各的维度](03-partial-rope.png)

为什么不全转或全不转？
全转时，位置挤进所有维度，K=V 后内容容易被位置包裹。
在仍依赖 RoPE 的普通 softmax 注意力里，全不转又会让 key 失去这条路径的距离信号。Partial RoPE 取中间态：内容维保持纯净，位置维承担匹配。

## 四、de-RoPE：输出端为什么要把旋转解掉

![de-RoPE：输出端解旋，绝对位置变成相对距离](04-derope-restore.png)

现在到了最微妙的一步。

因为 entry 又当 V，注意力输出是**带旋转的 V 的加权和**。下面把最后 64 维的旋转记为 $R_j$，其余 448 维的恒等变换省略。查询在位置 $i$，entry 在位置 $j$：

$$
\mathbf{o}_{t,i}=\sum_j a_{t,j}\,R_j\,\mathbf{v}_j
$$

问题来了：每个 $R_j$ 都带着自己的绝对位置。输出里混进了「第 3 块的旋转」和「第 300 块的旋转」——同一段内容，出现在不同位置，输出的内容坐标就不同。[论文第 2.3.3 节](https://arxiv.org/abs/2606.19348)把它概括为：naive 输出会携带 absolute position embeddings。

V4 的解法很漂亮：**对输出再按查询位置 $-i$ 旋转一次**。旋转矩阵满足角度相加，$R_{-i}R_j=R_{j-i}$：

$$
R_{-i}\,\mathbf{o}_{t,i}=\sum_j a_{t,j}\,R_{j-i}\,\mathbf{v}_j
$$

看右边：在旋转的 64 维里，每一项只剩「entry 和查询的距离 $j-i$」，绝对位置被消掉了，相对位置被保留下来。

这就是 de-RoPE 的名字由来——它不是「去掉位置」，而是「**解旋**」：把绝对位置翻译成相对位置。de- 是 undo 的意思，不是 delete。

为什么要做这一步？直观地说，下游 FFN 需要稳定地解读「内容」。如果输出坐标随绝对位置漂移，同样的内容在第 5 句和第 500 句会给出不同的表示，模型就更难学到稳定的语义。做完 de-RoPE，内容坐标干净了，位置信息还在——只是从「第 500 句」变成了「在 30 句之前」。

代价有多大？很小：只需对 64 维再做一次旋转。这正是 Partial RoPE 的 64 维设计反哺 de-RoPE 的地方——要解的东西越小，解旋越便宜。

## 五、机制验证：de-RoPE 真的能还原吗

光看公式不够，我写了个自包含的 NumPy 脚本（`experiment.py`）验证三条路径。为了可读性，演示用 16 维向量、最后 2 维旋转，对应真实配置里「512 维中最后 64 维」的分工。**这是机制演示，不是官方性能基准。**

| 验证项 | 结果 |
|---|---|
| 同一 entry 同时当 K 和 V（K=V 路径） | 形状与数值路径成立 |
| QK 内积只依赖相对距离（d=3，绝对位置 (5,8) vs (105,108)） | 2.0361 = 2.0361 |
| 只扰动内容维，内积随位置的变化不变 | 2.6065 = 2.6065 |
| 无 de-RoPE：同一内容在不同绝对位置的输出 | 最大差 0.2843（位置泄漏） |
| 有 de-RoPE：同一内容在不同绝对位置的输出 | 最大差 1.11e-16（绝对位置不变性恢复） |
| 不同相对距离（d=3 vs d=4）的输出 | 最大差 0.6855（相对位置仍保留） |

第二行验证 Partial RoPE：同一个相对距离换绝对位置，内积结果不变。
第三行进一步说明：扰动未旋转的内容维，并不会改变这条位置关系。
后三行验证 de-RoPE：不解旋，同一内容换个绝对位置，输出会漂移 0.28。
解旋后，漂移降到机器精度，同时仍保留相对距离信息。

## 六、延伸：Kimi K3 干脆不用 RoPE

V4 在「旋转一部分」上做文章，另一家国产旗舰走了更远的一步。

我核验了 [Kimi K3 官方开源仓库](https://huggingface.co/moonshotai/Kimi-K3)。注意力实现里 `rotary_emb = None`，还直接 `assert use_nope`。config 里没有 qk_rope_head_dim，K3 的注意力完全不旋转。

两种路线形成了有趣的对照：V4 是「部分旋转 + 输出解旋」，K3 是「完全不旋转」。这说明在长上下文时代，「RoPE 是不是必须的」已经成了开放问题。位置信息可以有别的载体，比如线性注意力里的状态更新本身就带顺序。

这里只陈述官方代码能确认的事实，不替 K3 脑补设计动机。

## 七、效率收口：这份缓存到底省了多少

![1M 上下文官方效率：27%、10%、2%](05-efficiency.png)

K=V 不是炫技，账是算得过来的。论文给的官方口径（1M context）：

- 推理 FLOPs 约为 DeepSeek-V3.2 的 **27%**
- KV cache 约为 DeepSeek-V3.2 的 **10%**
- 以 BF16 GQA8（head_dim=128）为基线，KV cache 约为基线的 **2%**

省在哪？主要是四件事：压缩、K=V 单份缓存、混合存储、索引器 FP4。
CSA 每 4 个 token 合成 1 个 entry。
HCA 每 128 个合成 1 个；V4-Pro 前两层先用 HCA，后续 CSA/HCA 交替。

这些数字是论文报告的，不是本文实验测的。机制演示只验证了路径正确，不能推出官方性能。

## 八、回扣：位置与内容，各归其位

回到开头的问题：K=V 为什么没让「找」和「取」串味？

因为 V4 把职责拆到了不同维度上。Partial RoPE 把位置锁进最后 64 维，让内容维度保持纯净。de-RoPE 在输出端把绝对位置翻译成相对距离。内容坐标不再随绝对位置漂移。两份工作共用一份缓存，但各用各的维度——这不是偷工减料，是更精细的分工。

而这套注意力还要和 V4-Pro 的 61 层网络一起工作，这就引出下一篇 **mHC（流形约束超连接）**：拆它怎么让深层信号稳定传播——为什么普通残差连接在 60 层以上会「传话传没」。

📖 **[大模型原理合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect)**：[BPE](https://mp.weixin.qq.com/s/5nR_KI47v_U8KwpQA4Uv5Q) → [词嵌入](https://mp.weixin.qq.com/s/rDryn1z_hLt7mwi3X8fsxQ) → [位置编码](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ) → [注意力](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw) → [FFN](https://mp.weixin.qq.com/s/vBCzukDlQyB9O6ASgAmlvQ) → [归一化残差](https://mp.weixin.qq.com/s/v-SBuMTbMANSTxHj7gYDkg) → [Transformer 全景](https://mp.weixin.qq.com/s/22J8JPkdpVeUx23KahbBmA) → [预训练](https://mp.weixin.qq.com/s/XoGHVycQHR5Tp-BWPac9Hg) → [SFT](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ) → [RLHF](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ) → [PPO](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw) → [GRPO](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA) → [RLVR](https://mp.weixin.qq.com/s/NvemnDdtkinRKEbmtcckzA) → [推理加速](https://mp.weixin.qq.com/s/LvxasW-4t0YuXy8nWpyzVw)

🔥 **DeepSeek 技术解密**：[AI 上下文为什么越长越慢](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q) → [MoE 混合专家](https://mp.weixin.qq.com/s/QdkD0CR2fD-HfY77-gX3Ug) → [KDA 长上下文](https://mp.weixin.qq.com/s/_RR5LLWgjGNm-qXdSdnAGA) → [MLA](https://mp.weixin.qq.com/s/HHMNEdCYThOjCLRozQorhg) → [Kimi K3 架构](https://mp.weixin.qq.com/s/6GJ2781jJh-dqYswJ07dfA) → [V4 注意力](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ) → K=V（本篇） → mHC → FP8 训练

如果你是架构师，会把位置信息放在少数维度（像 V4），还是干脆不旋转（像 K3）？你最担心的是位置信息丢失，还是内容被位置污染？评论区聊聊你的取舍。

觉得有用就点个赞 👍、收藏 ⭐ 备用；关注「数解AI」，下一篇拆 mHC 怎么让 61 层网络稳如磐石。

#DeepSeek技术解密 #K=V #KV缓存 #位置编码 #数解AI
