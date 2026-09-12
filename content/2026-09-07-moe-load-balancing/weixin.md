---
title: "DeepSeek 有 384 个专家，为什么不敢强迫它们平均干活？"
author: "数解AI"
date: "2026-09-07"
type: "原理篇"
series: "数学直觉"
digest: "DeepSeek 的模型里有 384 个专家，为什么不敢强迫它们平均干活？因为约束不是铁律，是带价格的偏好——拉格朗日乘子法把「不均衡」标上价格加进训练目标。DeepSeek 更狠：连这个价格都不付了，直接调路由偏置。"
cover: "00-cover.png"
keywords: ["拉格朗日乘子法", "MoE", "混合专家", "DeepSeek", "负载均衡", "辅助损失", "路由坍缩"]
scheduledPublish: "2026-09-07T20:00:00+08:00"
wechatUrl: ""
---

如果公司规定 384 个员工必须干一模一样的活，你会觉得公平还是荒谬？DeepSeek 的模型里就有 384 个"专家"，训练时它面临同样的选择——而它选了"不公平"。

看过很多论文里面，专家调配不均衡，训练失败奔溃的例子比比皆是。可问题是：既然不均衡这么危险，为什么不干脆规定每个专家平均干活？这听起来是最稳妥的方案，DeepSeek 却偏偏不敢。

## 一、平均干活，直觉上最公平，为什么不敢？

如果你从直觉和计算效率上看，专家是否要充分调动起来，每次都平均承担一部分运算才是效率最高的方式？我后来才发现，这个直觉并不成立，也没有那么简单。

先看 MoE 是怎么工作的。DeepSeek-V4-Pro 有 1.6 万亿参数，但每个 token 只激活 49B。靠的就是稀疏路由：384 个路由专家 + 1 个共享专家，每个 token 只挑 6 个专家干活。共享专家每个 token 都参与，路由专家则看情况上岗。

很多人说，根据你的输入任务的不同，模型会路由给不同分工的专家，如写代码，数学，法律方面的专家，这个说法其实更加错的离谱。专家的分配还是依据每一次的输入来的，给定一串输入序列，可能每次生成下一个token的时候，激活的专家都是不同的。

也就是说，不存在"写代码的专家"这种固定岗位。同一个 token 序列，生成第 3 个字和第 4 个字时，被激活的专家可能完全不同。专家不是按任务分工的部门，而是按当前语境临时组队的自由职业者。

那问题来了：既然每次都是临时组队，凭什么保证 384 个专家都被用上？如果路由完全自由，会发生什么？

## 二、放任自由的后果：路由坍缩

不干预的话，训练早期会出现一个经典灾难：路由坍缩（routing collapse）。所有 token 都挤到少数几个"热门"专家上，其余专家收不到 token，梯度为零，彻底废掉。

这个现象在论文里被反复记录。Switch Transformer（Fedus et al., 2021）的原文写得很直白：不干预的话，路由会坍缩。少数几个专家吃掉几乎所有 token。作者的原话是 "Without intervention, routers collapse: a few experts receive almost all tokens"。

坍缩的后果是双重的。一方面，热门专家过载，计算资源全堆在几个专家上，稀疏化的意义荡然无存。另一方面，冷门专家白训练——参数一直在更新，但从来没被用过，等于花钱养闲人。

![路由坍缩：token 全挤到少数几个专家](01-routing-collapse.png)

所以放任自由不行。那怎么办？最直接的想法是：规定每个专家必须处理一样多的 token。这就是硬约束。

## 三、硬约束为什么也不行

硬约束的思路很朴素：给每个专家设一个容量上限，token 超过上限就溢出丢弃。听起来公平，但问题在于——专家不是同质的。

有的专家擅长处理常见模式，有的专家擅长处理罕见模式。如果强迫每个专家处理完全相同的 token 量，等于让擅长数学的专家去写代码，让擅长代码的专家去写诗。每个专家都被迫干自己不擅长的活，整体性能必然受损。

而且硬约束还有一个工程问题：容量上限设多少？设小了，热门专家装不下，token 被丢弃，信息丢失；设大了，约束形同虚设。这个上限本身就是一个需要调的超参数，调起来比不调还麻烦。

硬约束太死，放任自由太乱。中间有没有第三条路？

## 四、拉格朗日出场：约束不是铁律，是价格

有。这就是拉格朗日乘子法（Lagrange multiplier）的核心思想：**约束不是铁律，是带价格的偏好**。

数学上，拉格朗日乘子法解决的是"带约束的优化问题"：在满足 $g(x)=0$ 的前提下最小化 $f(x)$。教科书教的方法是构造拉格朗日函数：

$$L(x, \lambda) = f(x) + \lambda \cdot g(x)$$

把约束 $g(x)=0$ 乘上一个系数 $\lambda$，加进目标函数 $f(x)$。然后对 $x$ 和 $\lambda$ 一起求导，令导数为零，解出来的 $x^*$ 就是约束下的最优解。

![拉格朗日：约束不是铁律，是价格](04-lagrange-geometry.png)

这个 $\lambda$ 就是拉格朗日乘子，它的含义非常深刻：**它度量了约束的"价格"**。约束每放松一单位，目标函数能改善多少。约束不是不可违背的铁律，而是有标价的偏好：你可以违反它，但要付出代价，代价的大小由 $\lambda$ 决定。

从数学课堂上老师填鸭式灌输的拉格朗日乘子法求解优化问题，到实际AI算法里面引入的各种正则项然后再求最优的参数组合，完全理解这些花了我很长的时间。

MoE 的负载均衡正是这么干的。不硬性规定每个专家处理多少 token，而是给"不均衡"标个价。在训练损失里加一项辅助损失（auxiliary loss），专门惩罚路由的不均衡程度：

$$L = L_{main} + \alpha \cdot L_{aux}$$

$L_{main}$ 是模型的主损失（预测下一个 token 的交叉熵）。$L_{aux}$ 是负载均衡损失，度量 token 在专家间的分布有多不均衡。$\alpha$ 就是那个价格系数——拉格朗日乘子。模型在训练中自己权衡：为了省这点罚金，值不值得绕路去用冷门专家。

## 五、价格有副作用：调 α 是走钢丝

从优化的角度看，这个参数过大或者过小，都不行，有点像中国人的中庸之道，得有一个恰到好处的设定才更好，不是吗？

$\alpha$ 太小，罚金不痛不痒，路由照样坍缩——模型发现绕路去用冷门专家的代价比罚金还高，干脆交罚款。$\alpha$ 太大，模型被罚金绑架。为了躲罚金，它强迫自己平均分配 token，结果每个专家都在干不擅长的活，主任务性能下降。

这个权衡在论文里有实证。Switch Transformer 的作者扫了 $\alpha$ 的取值，推荐 $\alpha = 0.01$。一个恰到好处的价格。而 Wang et al. (2024) 的论文说得更直白：$\alpha$ 太小负载均衡差。$\alpha$ 太大损害模型性能。这篇论文就是 Auxiliary-Loss-Free Load Balancing。他们测了 $\alpha$ 从 0 到 0.01 的变化：负载均衡确实改善了，但困惑度（perplexity）变差了。语言建模性能在下降。

也就是说，拉格朗日式的辅助损失本身就有副作用：**你为了平衡付出的罚金，会污染主任务**。平衡是手段，不是目的，但罚金分不清手段和目的。

![α 太小坍缩，α 太大伤性能](02-alpha-tradeoff.png)

## 六、DeepSeek 的答案：不付这个价格

DeepSeek 的选择是：连这个价格都不付了。

DeepSeek-V3 论文（arXiv:2412.19437）明确说，他们采用了一种无辅助损失的负载均衡策略。论文里叫 auxiliary-loss-free。目的就是"最小化为了鼓励负载均衡而对模型性能造成的负面影响"。原文是 "minimizing the adverse impact on model performance that arises from the effort to encourage load balancing"。

具体怎么做？不罚钱，直接调路由的偏置（bias）。每个专家维护一个偏置项，token 路由时，如果某个专家收到的 token 太少，就把它的偏置调高，让路由更容易选中它。反之调低。这个偏置只影响路由选择，不进入梯度反传，所以不会污染主任务。

到了 DeepSeek-V4-Pro，这个策略继续沿用，还加了一个轻微的序列级平衡损失，防止单条序列内部出现极端不均衡。384 个路由专家 + 1 个共享专家，每个 token 激活 6 个，1.6 万亿参数只激活 49B。这套机制撑起了整个模型的效率。

![384 个路由专家，每个 token 只激活 6 个](03-384-experts.png)

## 七、拉格朗日在 AI 里无处不在

拉格朗日乘子法远不止管 MoE。事实上，AI 里到处都是"给约束标价"的套路，只是名字不叫拉格朗日。

**β-VAE**。变分自编码器的损失函数里，KL 散度项前面乘了一个系数 $\beta$。$\beta > 1$ 时，模型被强迫让隐变量更"解耦"——每个隐变量只管一个独立属性。这个 $\beta$ 就是拉格朗日乘子：约束"隐变量别跑太远"的价格。Higgins et al. (2017) 发现 $\beta$ 调大一点，模型学到的表示就更干净。

**WGAN-GP**。生成对抗网络训练不稳定，WGAN 用 Wasserstein 距离替代 JS 散度。但要求判别器满足 Lipschitz 约束。怎么保证这个约束？Gulrajani et al. (2017) 的做法是加梯度惩罚项，系数 $\lambda = 10$。又是一个拉格朗日乘子。判别器当"警察"，梯度惩罚就是警察的执法成本。

**L1/L2 正则化**。权重衰减（weight decay）本质上是给"权重别太大"这个约束标价。L2 正则化对应拉格朗日形式，L1 正则化（LASSO）则对应另一个变体。你训练模型时随手写的 weight_decay=0.01，就是一个拉格朗日乘子。

![拉格朗日在 AI 里无处不在](05-lagrange-everywhere.png)

课本上抽象的理论，只有放到实际问题中，才能看到基础的理论是多么优美而又实用。拉格朗日乘子法在数学课上是个求解技巧，在 AI 里却是一整套"如何优雅地管住模型"的哲学。

## 八、所以，DeepSeek 不是不敢平均

回到开头的问题：DeepSeek 有 384 个专家，为什么不敢强迫它们平均干活？

因为平均从来不是目的。专家的价值在于各司其职，路由的价值在于按需分配。强迫平均，等于让每个专家都变成平庸的全能选手。DeepSeek 的做法是：先给"不均衡"标个价（辅助损失），后来发现价格本身有副作用，干脆连价格都不标了，直接调偏置。

拉格朗日乘子法的精髓就在这里：**约束不是铁律，是带价格的偏好**。价格可以调，可以取消，甚至可以换成别的机制。真正的高手不是遵守约束，而是理解约束的价格，然后决定付不付。

你训练模型时调过损失函数里的小系数吗？报一下模型名和数值，评论区聊聊。

下一篇我们聊 SVD：矩阵为什么能「压缩」？——KV 缓存压到 1bit 的数学底牌。

---

看完别急着划走：觉得有用就点个赞 👍、收藏 ⭐ 备用；关注「数解AI」，下一篇第一时间推给你。

📖 本文收进「AI中的数学」合集。前几篇见：[MLE为何让大模型一会儿像博士一会儿像小学生？](https://mp.weixin.qq.com/s/lyB9eA4qKIMWW_3i1PypDw) · [每步都靠猜，上百万Token的长任务怎么不跑偏](https://mp.weixin.qq.com/s/pbIQrUsChnNuFotkayFtiw) · [KL散度：为什么整个AI共用一把尺子？](https://mp.weixin.qq.com/s/G1PUOuwxURoo1Dp1pDfQMg) · [信息熵：压缩1000倍，为什么信息反而少？](https://mp.weixin.qq.com/s/BkGWzKxiJE2mlPMlZgb7ag)

🔥 **热门文章**：

[曾困扰人类358年的费马大定理终被AI证明](https://mp.weixin.qq.com/s/SJWle4e-JtCw5qO_A6eQ-g)  
[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[MLE为何让大模型一会儿像博士一会儿像小学生？](https://mp.weixin.qq.com/s/lyB9eA4qKIMWW_3i1PypDw)  
[每步都靠猜，上百万Token的长任务怎么不跑偏](https://mp.weixin.qq.com/s/pbIQrUsChnNuFotkayFtiw)  
[KL散度：为什么整个AI共用一把尺子？](https://mp.weixin.qq.com/s/G1PUOuwxURoo1Dp1pDfQMg)  
[信息熵：压缩1000倍，为什么信息反而少？](https://mp.weixin.qq.com/s/BkGWzKxiJE2mlPMlZgb7ag)  
[SFT微调：1万条数据就能让模型听话？](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ)  
[梯度下降：蒙着眼下山](https://mp.weixin.qq.com/s/V6mGvCVFpTvmC51pNtxiTw)  
[Softmax为什么不直接取最大值？](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw)  

**参考资料**

1. Fedus, W., Zoph, B., & Shazeer, N. (2021). [Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961). arXiv:2101.03961.
2. DeepSeek-AI (2024). [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437). arXiv:2412.19437.
3. Wang, L., et al. (2024). [Auxiliary-Loss-Free Load Balancing Strategy for Mixture-of-Experts](https://arxiv.org/abs/2408.15664). arXiv:2408.15664.
4. DeepSeek-AI (2026). [DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence](https://arxiv.org/abs/2606.19348). arXiv:2606.19348.
5. Higgins, I., et al. (2017). [β-VAE: Learning Basic Visual Concepts with a Constrained Variational Framework](https://openreview.net/forum?id=Sy2fzU9gl). ICLR 2017.
6. Gulrajani, I., et al. (2017). [Improved Training of Wasserstein GANs](https://arxiv.org/abs/1704.00028). arXiv:1704.00028.

#拉格朗日乘子法 #MoE #DeepSeek #负载均衡 #数学直觉 #数解AI
