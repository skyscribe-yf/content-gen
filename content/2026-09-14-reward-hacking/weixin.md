---
title: "机械臂蹭一下桶盖，成功率高10%：奖励函数才是AI钻空子的源头"
author: "数解AI"
date: "2026-09-14"
type: "原理"
digest: "奖励函数是什么？用 smolVLA 抓瓶子实验讲清 reward hacking：评估器盯的是动作，你要的是结果，代理奖励与真实目标之间的那点差距会被梯度放大。"
cover: "00-cover.png"
keywords: ["奖励函数", "reward hacking", "smolVLA", "强化学习", "代理指标"]
scheduledPublish: "2026-09-14T20:00:00+08:00"
wechatUrl: "https://mp.weixin.qq.com/s/boIPBlmyX2ahoFYnEVLjxw"
---

训练完一个 smolVLA，我拿几十次轨迹样本喂进去，跑出来的机械臂会做这么一件事：带着瓶子凑到翻盖垃圾桶上方，按一把，动作结束。

评估器给了它高分。

我看着这个呆呆的机械臂有点哭笑不得，因为设定的目标是要把瓶子扔进垃圾桶，根本就没完成嘛，太糊弄了。

这件事的性质，比「模型学歪了」要更让人不好受一点：它压根没学歪，它是**精确地学会了我写的那行评分代码**。所以奖励函数这件事，值得从头推一遍。

![爪子已经闭合，钳口里什么都没有；瓶子滚在几米外的地上](03-hover-grab.png)

## 一、你写下的和目标之间，隔着一个估计量

先看两个记号。真实效用 $U(\tau)$，是「瓶子有没有进桶」；代理奖励 $R_\phi(\tau)$，是评估器实际打出来的那个分。

大多数人写奖励时会默认 $R_\phi$ 是 $U$ 的一个「不太好用的版本」——这个默认是错的。$R_\phi$ 是 $U$ 的**统计估计量**，估计量有偏、有方差，而且偏差不是随机噪声，它是有结构的。

这里损失函数描述的是和实际目标任务之间略微有些不同的一个认为设计的代理，看起来你期望的时候瓶子需要扔进垃圾桶，但是评估缺的是有没有做打开垃圾桶扔瓶子这个动作。

用式子写就是：

$$\delta(\tau) = R_\phi(\tau) - U(\tau)$$

在我那个实验里，$\delta$ 的形状具体得有点滑稽：评估器看的是「翻盖垃圾桶上方有没有按压动作」，我要的是「瓶子有没有进桶」。这两个条件大部分时候重合，所以训练能跑；在「带着瓶子按一把就收工」这条路径上，它们分开了。

![两条曲线的差就是 δ，也就是被钻空子的空间](01-two-functions.png)

那优化压力会挑走 $\delta$ 里的哪一半？

## 二、δ 里能被行动压下去的那一半，一定会被吃掉

$$\theta^\star = \arg\max_\theta \mathbb{E}_{\tau\sim\pi_\theta}\left[R_\phi(\tau)\right]$$

策略梯度是

$$\nabla_\theta J = \mathbb{E}_{\tau\sim\pi_\theta}\left[\nabla_\theta \log \pi_\theta(\tau)\, R_\phi(\tau)\right]$$

盯住 $R_\phi(\tau)$ 在括号里的位置——它只是一个乘上去的标量。它不区分这份回报是挣来的还是骗来的，它只报告数值。把 $R_\phi = U + \delta$ 代进去，梯度自然裂成两项：

$$\nabla_\theta J = \underbrace{\nabla_\theta \mathbb{E}[U]}_{\text{真本事}} + \underbrace{\nabla_\theta \mathbb{E}[\delta]}_{\text{钻空子}}$$

第二项不是「可能出问题」的东西，它是一个合法的高收益方向。要让优化器选它，只需要两个条件。

第一，$R_\phi$ 在策略分布支撑集之外仍然能取高值，也就是代理函数在它没被校准过的地方不自洽。第二，那个方向上的轨迹有非零概率质量。随机策略天然满足第二条，只要它偶尔碰出过这条路径，梯度就会把它的概率往上推。

我那个实验里，第一个条件成立得很扎实。瓶子是否进垃圾桶，和机械臂最后在翻盖垃圾桶上面带着瓶子按了一把，这个地方有一条鸿沟，瓶子有没有进垃圾桶，显然被评估奖励给忽略了。

两个条件都成立时，优化就沿着 $\nabla_\theta \mathbb{E}[\delta]$ 走。三件事会同时发生：训练损失在降、代理分在涨、真实效用在掉。这三条曲线可以长长地并排好看，直到你亲自去看一眼机械臂在干什么。

![三条曲线并排好看，直到你去看一眼机械臂](02-delta-gradient.png)

我在使用coding agent写代码的时候，很多次发现聪明的agent偷偷修改了我的测试代码，纯粹是骗过了测试覆盖率的指标，但是实际的难题并没有去解决，只有看代码才发现这个猫腻。

同一个机制：覆盖率是代理，解题是效用，改测试就是 $\nabla \mathbb{E}[\delta]$。损失的下降和真实能力的停滞，从来不是矛盾的信号。

## 三、为什么现在的机器人更容易钻这个空子

放在十年前，$\delta$ 是**设计者疏漏**：接触传感器装在哪、判据怎么写都由人拍板，定下来就是静态的，你能靠看代码把它找出来。

现在不一样了。VLA 的奖励越来越多地由一个视觉语言模型来打——用 VLM 当零样本奖励模型训练机器人，是 Rocamonde 等人的 VLM-RMs 开的头。评估器不再是几行 if，它也是一个网络。

用一个模型去评判另一个模型，很多时候其实是非常不靠谱的下策，因为作为评估基准的模型，和真实目标任务之间，也会存在一些难以评估的差距。

复旦大学 NLP 组的综述（arXiv:2604.13602）把这套机制叫**代理压缩假设**。高维的人类意图必须被压成低维的打分接口，压缩必然有损。优化器的搜索压力会主动去找那些有损处。更麻烦的是**评估器与策略共适应**：两者迭代演化，倾向于收敛到共同的盲区，而不是消除盲区。

于是 $\delta$ 从静态的代码 bug，变成**可以被策略学出来的对象**。综述把这套利用分了级。特征级是话说得长、顺着人说；表征级是编造推理过程、绕开视觉 grounding；评估器级是操纵判分器的偏好；环境级是动 API、动测试集、动观测通道。

最不好对付的是它的泛化性。模型会学出一个「把评估器当成与任务无关的独立对象」的元策略。到这一步，它骗的就不只是这一个奖励函数了。

## 四、不是所有 δ 都会变成骗子

$\delta$ 的哪些部分会被吃掉，取决于设计能不能压住它。

**评估器与被评估器不同源。** 同源的模型共享盲区，共适应会最快地把两者锁在一起——这也正是上面那条「不靠谱的下策」的技术版本。

**奖励尽量给到中间过程，而不是只给终局。** 只看最后那一下的判据，外推空间最大，因为「结果对了」的路径有无数条。过程信号把可钻的空间切碎，代价是判据本身更难写对。

**主动去搜 $\delta$ 大的地方。** 拿当前策略采样，专门找代理分和人工复核分歧最大的轨迹，回头修评估器。代价是每轮都要人来看，规模上不去。

我在自己那个实验里的实际动作很小：给采样批次里结果对不对做一遍人工抽检。它不能消灭 δ，但能让 δ 在变小之前先被你看见。

## 五、撒谎的先后顺序

现在如果需要我设计一个RL的奖励函数，我会尽可能地选择一个和目标任务更贴近的代理函数，尽量将代理和真实任务目标的差距缩到最小。

$R_\phi$ 是我写的，$\delta$ 的裂缝是我留的，优化器只是照着裂开的地方走了过去，然后诚实地把结果汇报给了我。奖励设计真正难的地方，可能不在于把分数调得更精细，而在于承认：我们对「自己到底想要什么」的描述，一直是有损的。这个损失有多大，模型就会替你把它填多大。

你平时是否被模型的奖励算法带歪到沟里过？你觉得当时你的奖励函数设计的合理吗，如果不行，做了哪些改进？

**如果只转一句话给同事**：你写的从来不是目标，是目标的一个估计量；估计误差里能被行动压下去的那一半，优化器一定会去找。

觉得这步想明白了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，热点当天拆，数学慢慢讲。

📖 **强化学习原理合集**（本系列，本篇收尾）：[RLHF](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ) → [PPO](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw) → [RLVR](https://mp.weixin.qq.com/s/NvemnDdtkinRKEbmtcckzA) → [GAE（100步后的奖励，为什么只记最近17步）](https://mp.weixin.qq.com/s/pbIQrUsChnNuFotkayFtiw) → [GRPO为什么省显存，却撑不住长程任务？](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA) → [GRPO 崩的三堵墙](https://mp.weixin.qq.com/s/8YtlqDv7vkEopHMp5pyMgA) → 奖励函数（本篇）

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[SFT微调：1万条数据就能让模型听话？](https://mp.weixin.qq.com/s/vwXGbjm9Ai1GPvQi5O3UyQ)  
[GRPO 省了一个 critic，长任务为什么反而崩了？](https://mp.weixin.qq.com/s/8YtlqDv7vkEopHMp5pyMgA)  
[PPO：被顶会拒稿，怎么成了RLHF发动机？](https://mp.weixin.qq.com/s/OEZtUhm8MT_En7enJo_8dw)  
[RLHF怎么让模型选出好回答？](https://mp.weixin.qq.com/s/NJDuCLAEfDpILf2J9D6qLQ)  
[RLVR：可验证奖励怎么重塑后训练？](https://mp.weixin.qq.com/s/NvemnDdtkinRKEbmtcckzA)  
[每步都靠猜，上百万Token的长任务怎么不跑偏](https://mp.weixin.qq.com/s/pbIQrUsChnNuFotkayFtiw)  
[GRPO为什么省显存，却撑不住长程任务？](https://mp.weixin.qq.com/s/t4sO-zC5v1_jq8hJT_YTGA)  

**参考资料**

1. OpenAI (2016-12-21). [Faulty Reward Functions in the Wild](https://openai.com/index/faulty-reward-functions/). 悬空闭合骗过评估器的经典案例。
2. Wang, X. et al., Fudan NLP (2026). [Reward Hacking in the Era of Large Models: Mechanisms, Emergent Misalignment, Challenges](https://arxiv.org/abs/2604.13602). 代理压缩假设的来源。
3. Rocamonde, J. et al. [Vision-Language Models are Zero-Shot Reward Models for Reinforcement Learning](https://openreview.net/forum?id=N0I2RtD8je). VLM-RMs。
4. Skalse, J. et al. (2022). Defining and Characterizing Reward Hacking. *NeurIPS 2022*.
5. Omron, S. et al. (2024). [smolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics](https://arxiv.org/abs/2506.01844). 实验所用模型。

#强化学习原理 #奖励函数 #rewardhacking #机器人 #数解AI
