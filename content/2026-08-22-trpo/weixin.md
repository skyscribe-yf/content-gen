---
title: "梯度一步踩爆50倍预算，TRPO为什么敢走？"
author: "数解AI"
date: "2026-08-22"
type: "原理篇"
series: "强化学习原理"
digest: "梯度只说往哪走，不说走多大。TRPO 把「走多大」交给 KL 预算：surrogate 用旧轨迹给新策略预打分，拉格朗日把约束折成罚金，二阶泰勒交出曲率，最后一步闭式解自动按云的形状分步——窄方向小步、宽方向大步。"
cover: "00-cover.png"
wechatUrl: "https://mp.weixin.qq.com/s/Y3dk7CHMNgWBitxnoDNljA"
keywords: ["TRPO", "信任域", "KL散度", "自然梯度", "策略梯度", "强化学习"]
---

深夜，两个 coding agent 在同一份代码上训练。

A 用普通梯度上升，学习率 0.1，一步一个脚印。B 每步都先量一量新旧策略差多远。

一晚上过去。A 连昨天会的都忘了，B 稳稳变强。

差别不在学了多少，在一步走多大。

## 一、篇5 的遗产：预算

上篇《[多维高斯：为什么同一步长差1万倍？](https://mp.weixin.qq.com/s/GjNkcQ70B3WBzaVPwqVTgg)》说过：策略是一团云，云与云的距离用 KL 量。今天拿着这把尺子，看 TRPO 怎么限步。

先复习那颗椭圆云。

$\Sigma=\mathrm{diag}(0.01,\,100)$。窄方向是改行数：agent 很确定，几乎总改 3 行。宽方向是测试时长：很没底，1 分钟到 20 分钟都干过。

上一篇算了两个数：

- 均值 $\mu$ 往窄方向挪 $0.1$：$\mathrm{KL}=0.5$，翻天覆地。
- 往宽方向挪 $0.1$：$\mathrm{KL}=0.00005$，几乎无感。

同一把直尺量 $0.1$，两个方向差 $1$ 万倍。所以「步长」不能拿参数坐标定，要拿 KL 定。

由此有了预算：每次更新，新旧策略的 KL 不许超过 $\delta=0.01$。窄方向最多挪 $0.014$，宽方向最多挪 $1.41$，允许的步子差 $100$ 倍。

故事到这儿，问题悬着：**上限知道了，每一步实际走多大，谁说了算？**

梯度只说方向。梯度上升写成：

$$\theta \leftarrow \theta + \eta\, g$$

$\eta$ 是学习率，$g$ 是梯度。一个数管所有方向，既不认识云，也不看预算。

## 二、普通梯度：固定步长怎么崩的

回到椭圆云。假设两个方向的梯度都是 $1$：改行数方向该动，测试时长方向也该动。梯度说：各走 $0.1$。

普通更新器照做。学习率 $\eta=0.1$，一步把均值挪到 $(0.1,\,0.1)$。

量一量这一步的 KL。窄方向贡献 $\frac{1}{2}\cdot\frac{0.1^2}{0.01}=0.5$，宽方向贡献 $\frac{1}{2}\cdot\frac{0.1^2}{100}=0.00005$。加起来 KL $\approx 0.5$。

预算 $\delta=0.01$。这一脚踩了预算的 **50 倍**。

行为上发生了什么？窄方向的云 $\sigma=\sqrt{0.01}=0.1$，均值挪了 $0.1$，正好一个标准差。「几乎总改 3 行」这条习惯，概率从 $0.954$ 掉到 $0.840$——昨天九成半会做的事，今天只剩八成四。

不是学太快。是**云窄的地方经不起大步**。普通梯度不认识云，每个方向都按同一学习率踩，窄方向第一脚就踩爆。

![同一个梯度，普通更新器一步把窄方向踩出预算 50 倍](01-ordinary-gradient.png)

## 三、揭盖：surrogate——旧数据怎么给新策略预打分

![旧轨迹留在仓库，新策略用概率比重加权预打分](02-surrogate-score.png)

要换一种更新：走多大，让 KL 预算说了算。但算「新策略到底有多好」，需要按新策略重新采样跑环境——贵。

有个 trick，叫**重要性采样**。

新策略 $\pi_{\theta}$ 的概率比上旧策略 $\pi_{\text{old}}$：

$$r(\theta)=\frac{\pi_{\theta}(a\mid s)}{\pi_{\text{old}}(a\mid s)}$$

用旧轨迹给新策略打分，数学上等价：

$$\mathcal{L}(\theta)=\mathbb{E}_{\tau\sim\pi_{\text{old}}}\left[r(\theta)\,G\right]$$

读人话：**昨天的轨迹还在。把每条轨迹的回报 $G$，乘上「新策略对这条轨迹的重视程度」$r$，加起来，就是新策略的期望回报。**

直观上：旧策略走某条路的概率是 $0.30$，新策略想把它提到 $0.80$，这条路的分数权重就从 $1$ 涨到 $\frac{0.80}{0.30}\approx 2.67$。

新策略不必重新采样，就能估自己的表现。这就是 surrogate——代理目标。它回答「往哪走」。

## 四、泰勒展开：坡不只有方向，还有弯度

刚才梯度 $g=\nabla_\theta \mathcal{L}(\theta_{\text{old}})$ 是一阶信息：站在这里，坡往哪翘。

但云是椭圆的，坡是弯的。一步之内的曲率，一阶看不到。

二阶泰勒展开把曲率请进来：

$$\mathcal{L}(\theta)\approx \mathcal{L}(\theta_{\text{old}})+g^T\Delta\theta$$

KL 那边，二阶项是：

$$\mathrm{KL}(\pi_{\text{old}}\|\pi_{\theta})\approx \frac{1}{2}\,\Delta\theta^{T}F\,\Delta\theta$$

$F$ 是 Fisher 信息矩阵。在高斯策略下，$F=\Sigma^{-1}$——上一篇那把尺子的刻度。窄方向 $F=100$，宽方向 $F=0.01$。展开到二阶，预算变成椭圆不等式：

$$\frac{1}{2}\Delta\theta^{T}\Sigma^{-1}\Delta\theta\le\delta$$

椭圆还是那颗椭圆：窄方向 $0.014$，宽方向 $1.41$。

## 五、拉格朗日：预算超标，交罚金

![预算是一条安全线，越线交罚金，λ 是单价](03-lagrange.png)

现在约束优化：在 $\frac{1}{2}\Delta\theta^{T}F\,\Delta\theta\le\delta$ 之内，最大化 $\mathcal{L}$ 的一阶近似 $g\cdot\Delta\theta$。

这种「既要最大化目标，又不许越过一条线」的问题，大学最优化课里见得多了。处理它的标准工具叫**拉格朗日乘子法**——高数下册的老朋友，最优化理论的看家技巧。它解决一件事：怎么把「不许越线」翻译成数学能算的话。

翻译结果一句话：**把约束折成罚金。** 每超预算一个单位，罚 $\lambda$ 个罚金。$\lambda$ 是拉格朗日乘子，待定。

新的目标函数：

$$\max_{\Delta\theta}\; g^{T}\Delta\theta-\lambda\left(\frac{1}{2}\Delta\theta^{T}F\,\Delta\theta-\delta\right)$$

前一半是「往收益大的方向走」，后一半是「别超预算」。$\lambda$ 就是预算的贵——预算越紧，$\lambda$ 越大，步子越保守。

对 $\Delta\theta$ 求导，令其为零：

$$g-\lambda F\,\Delta\theta=0$$

解得：

$$\Delta\theta=\frac{1}{\lambda}F^{-1}g$$

**这就是自然梯度**：方向是 $F^{-1}g$，不是 $g$。

它把梯度掰弯了。$g=[1,1]$ 说两个方向各走一半，$F^{-1}g=[0.01,\,100]$ 说窄方向几乎不动、宽方向走满——比例差 $1$ 万倍。不是梯度说谎，是它在椭圆坐标系里重新诠释「方向」。

## 六、闭式解：步长自动算

还差一步：$\lambda$ 定下来，步长就定了。最优解应该恰好把预算用完（用不满就还能多走，$\lambda$ 就应调小）。把 $\Delta\theta$ 代回约束取等号：

$$\frac{1}{2}\left(\frac{1}{\lambda}F^{-1}g\right)^{T}F\left(\frac{1}{\lambda}F^{-1}g\right)=\delta$$

$$\frac{1}{2\lambda^{2}}\,g^{T}F^{-1}g=\delta$$

$$\lambda=\sqrt{\frac{g^{T}F^{-1}g}{2\delta}}$$

代回：

$$\boxed{\theta_{\text{new}}=\theta_{\text{old}}+\sqrt{\frac{2\delta}{g^{T}F^{-1}g}}\;F^{-1}g}$$

这就是 TRPO 的更新式。**方向看梯度，大小看曲率**。

验证一下数字。$g=[1,1]$，$\delta=0.01$，$F^{-1}=\mathrm{diag}(0.01,\,100)$：

$$g^{T}F^{-1}g=0.01+100=100.01$$

$$\sqrt{\frac{2\times0.01}{100.01}}\approx0.01414$$

一步：

$$\Delta\theta=0.01414\times[0.01,\,100]=[0.00014,\,1.414]$$

窄方向挪 $0.00014$，宽方向挪 $1.414$。回到篇5 的上限：窄 $0.014$，宽 $1.41$——TRPO 宽方向一步正好踩到上限，窄方向只用掉上限的 $1\%$。

KL 恰好等于 $0.01$，预算用满。

**同一个梯度，普通更新器踩爆预算 50 倍；TRPO 踩着预算走，一步不差。** 区别全在：普通更新器一个学习率走所有方向，TRPO 每一步都由云的形状反算。

![TRPO 一步自动分配：窄方向 0.00014，宽方向 1.414，恰好踩满预算](04-closed-form-step.png)

## 七、TRPO 是谁

TRPO 全称 Trust Region Policy Optimization，中文叫信任域策略优化。Schulman 等 2015 年提出。名字里的「信任域」就是那颗椭圆：每次更新，只信任旧策略周围的一小圈（KL 预算 $\delta$ 圈出来的区域）。

> 📌 小注：本文一直拿二维椭圆打比方。真实模型参数以百万计，信任域不是椭圆，是百万维空间里的椭球。高维空间的直觉（质量全挤在壳上、点和点互相远离），[《高维空间为什么全是壳？内积才是那把尺子》](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q) 拆过。椭球的长短轴对应曲率、曲率决定步子大小，[《学习率怎么自动调？Adam 优化器拆给你看》](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA) 里也提过这一层。

它给了一个保障：**优化 surrogate，真目标不降**。这个结论有个数学证明（Kakade-Langford 下界，Schulman 论文里引了），本文不展开，结论直接用了。这保证让「拿着旧数据优化」不是耍流氓。

工程上 F⁻¹ 不是真求逆的，用共轭梯度迭代去逼近这个乘积。理论上求个逆没问题，实际工程里承受不起这么大的计算量——参数百万级，真求逆训练根本跑不动。任何理论上很优美、但工程上落不了地的东西，都只能是镜花水月。这个细节，有机会我们再深入解释。

不便宜，但值：RLHF 里策略更新动辄百万参数，一步更新错了，整个模型回到解放前。TRPO 的预算刹车，保证每步都踩在椭圆里。

GRPO 是这条线上的后裔，DeepSeek 用它做后训练（V4 时代）。**同一个家族，三代：TRPO 给刹车，PPO 把刹车拧成代码，GRPO 把代码删一半**。

## 结尾

回到开头两个 agent。

A 崩，不是学得快，是不认识云：梯度指哪打哪，窄方向一脚踩掉 50 倍预算，昨天会的今天全忘。

B 稳，每一步都先回答两个问题：往哪走（surrogate 梯度），走多大（KL 预算）。闭式解把这两件事拧成一个式子，步长自己会按云的形状调。

**方向交给梯度，大小交给曲率。** 这就是 TRPO。

不过 TRPO 有个工程包袱：每次更新都要解一次 $F^{-1}$，参数一多就贵。下一篇，看 PPO 怎么用一句 clip 把这桌数学换成三行代码。

一个问题留给你：这篇的信任域，是先把约束优化严格推导出闭式解，再交给计算机去算的——这一点你意外吗？读下来哪个点最不容易理解？评论区聊聊。

🔥 **近期热门**：

[多维高斯：为什么同一步长差1万倍？](https://mp.weixin.qq.com/s/GjNkcQ70B3WBzaVPwqVTgg)

[策略梯度是什么？直接改概率行不行](https://mp.weixin.qq.com/s/IcoJTY4b1c-p0Njrxb7isA)

[Q-learning是什么？没有转移表怎么解](https://mp.weixin.qq.com/s/W9Bd--EtnidWy65Yx4Kyfw)

[PPO：被顶会拒稿，怎么成了RLHF发动机？](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw)

觉得这步走明白了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，强化学习原理系列，从 Bellman 一路拆解到 GRPO。关注后回复「强化学习」，我把系列合集链接发你。

## 参考资料

1. Schulman, J., Levine, S., Abbeel, P., Jordan, M., & Moritz, P., [Trust Region Policy Optimization](https://arxiv.org/abs/1502.05477), ICML 2015. TRPO 原文，Kakade-Langford 下界与自然梯度出处在第 2-3 节。
2. Sutton, R. S., & Barto, A. G., [Reinforcement Learning: An Introduction](http://incompleteideas.net/book/RLbook2020.pdf), 2nd ed., MIT Press, 2018. 第 13 章策略梯度与自然梯度路数。
3. Schulman, J., Wolski, F., Dhariwal, P., Radford, A., & Klimov, O., [Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347), 2017. PPO，TRPO 的工程化后裔。

#强化学习原理 #TRPO #信任域 #自然梯度 #数解AI
