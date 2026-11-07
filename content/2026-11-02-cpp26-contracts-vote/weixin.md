---
title: "60% 的赞成票，为什么救不了 C++26？"
wechatUrl: "https://mp.weixin.qq.com/s/FE4WEuT1-Ozz4uYtvfCG7w"
author: "数解AI"
date: "2026-11-02"
type: "行业观察"
digest: "C++26 批准投票据知史上首次被否：12 票赞成、9 票反对，矛头指向 contracts——检查能不能随时关掉。AI 写的代码没人审查，这个问题每个用 AI 写代码的人都会遇到。"
description: "C++26 批准投票据知史上首次被否：12 票赞成、9 票反对，矛头指向 contracts——检查能不能随时关掉。AI 写的代码没人审查，这个问题每个用 AI 写代码的人都会遇到。"
cover: "00-cover.png"
---

10 月 24 日，ISO C++ 委员会召集人 Robert Seacord 用两句话宣布：C++26 的批准投票，没通过。据报道，20 张 P 成员国选票里只有 12 张赞成，需要 14 张；22 张国家体选票里 9 张反对，上限是 5 张。

两道门槛，一道都没够。这应该是 C++ 标准史上第一次倒在最终投票门前。杀死它的不是一个 bug，是一个问题：如果检查可以随时关掉，它还叫检查吗？

这个问题，每个用 AI 写代码的人，马上都会遇到。

作为一名深耕 C++ 技术十几年，然后这几年逐渐转移了主要注意力的老技术人，看到这个新闻甚至有点恍如隔世。

难道 C++0x 最后变成十六进制数 0xa 的历史还要重演？这都什么年代了，他们所争论的话题，是否还能够让这门古老、复杂、高效但是又僵化的语言具备更持久一些的生命力？

## 一、60% 的赞成，为什么过不了关

先把投票上的数字说清楚：P 成员国赞成票要过三分之二，国家体反对票不能超过四分之一。

12 除以 20 是 60%，差 2 张；9 除以 22 是 41%，超了 4 张。任何一道不过，草案就过不了。60% 的多数，救不了它。

据报道，反对票来自丹麦、芬兰、伊朗、意大利、日本、卢森堡、罗马尼亚、西班牙和瑞典，并且波兰和美国弃权。

而反对票的矛头，几乎全部指向同一个特性：contracts。

这已经是 contracts 第二次倒在门前：2019 年被移出 C++20；2026 年 3 月 Croydon 又以 114:12:3 把它留在 C++26。

![](01-dis-vote-thresholds.png)

## 二、杀死 C++26 的，是一个叫 contracts 的特性

contracts 是什么？写在函数签名上的机器可读意图：pre(条件)、post(条件) 挂在声明上，函数体里还能写 contract_assert。

它的卖点很直白：边界条件不必再读函数体去猜，签名上就写着。

但 C++26 采用的 P2900 方案，给每个断言留了四种运行语义。

ignore 不求值，observe 打报告后继续，enforce 打报告后终止，quick_enforce 是低开销版 enforce。

致命的是：语义在构建时选定，同一份源码，在不同编译单元里可以有不同语义。

这个就好比只在 DEBUG 模式下打开的 assert，如果关键的逻辑有一些放在了这个 assert 里面被展开计算，正式发给用户的软件行为就会和开发模式下不尽相同。

![](02-contract-semantics.png)

## 三、Bjarne：这不是契约，是能关掉的断言

先纠正一个误解：Bjarne 反对的并不是契约本身，而是 P2900 这个设计——领衔的 P4334R0 五位作者里包括 SG21 前主席 Spicer。

他们的论证，可以挑三条最硬的看看。

第一条，焦点错位。P2900 把契约定位成调试支持，可 Eiffel 的文档说发布时就要关掉断言，C 的 assert 在 NDEBUG 下直接消失。

微软的 C# Code Contracts 早就废弃。P4334R0 的原话：这等于只在靠近海岸时才穿救生衣。

第二条，给不了保证。安全必须是对整个代码库的保证，而契约主要提供使用处的检查；监管和社区要的 always-on，这个设计给不了。

第三条，没做完。GCC 只有实验性实现，Clang 的状态页写着「No」，两个编译器厂商在反对者里。

日常最需要的虚函数契约、原值捕获、UB 框架，全部推到了 C++29。

还有条成本论证最重：投票前改默认值，改的是没人依赖的文字；发布后再改，改的是未来十年代码照着哪个默认值写。

他们的替代方案：固化标准库 always-on，实测 0.3% 开销，加库式契约——更简单、已实现的替代方案已经存在。

其实我倒是挺能理解 Bjarne 推崇的固化的方式，而不是仅仅作为语言机制层面的约束。

但是考虑到各种历史上的语言演化过程中的僵化和决策进度缓慢的问题，可能 Sutter 的略微激进的方式更能适应当今这个快速变化的世界。

## 四、Sutter：意图直接表达，人、工具、AI 都受益

再纠正一个误解：Herb Sutter 是支持者——contracts 被他列为 C++26 三块功能性安全收益之一，「比 C 的 assert 宏好无限倍」。

他在 BeCPP 2026 上讲过一段直接回答 AI 的话：语言一直在演化成能直接表达意图的形态——range-for、lambda、concepts、contracts，已经能帮人帮工具的，也帮 AI。

签名上的 pre/post，让人、静态分析器、优化器、AI 都不必去读函数体。

但是请注意，Sutter 的收尾论证是程序性的：「委员会仍然想要 contracts。」而设计方自己的论文 P3846R1 承认：保证式执行是另一个需求，C++26 给不了。

还有条流程证据。Spicer 的自清算论文原话里这么说过：我主持过 SG21，我也反对 C++26 contracts——他承认把技术反对压到论文离开 SG21 之后才公开。

根据我个人使用 AI 的经验来看，现在主流的大模型的指令遵循能力已经非常强，以至于到了过于僵化、照单全收的境地。

代码里面存在的一些注释和文档，只要被 agent 读取到了，就会被一股脑纳入到后续步骤的推理中去。

尽管这个过程还带有一些概率上的不确定性，叠加上已有的 RLVR 技术和环境里面的验证手段，很多错误的采样轨迹其实大多情况下也会被很好地掩盖过去。

## 五、AI 写的代码没人审查，这场争论被放大了

为什么一门老旧的编程语言委员会专家们内部的争吵，值得关心 AI 的人来投入精力了解？

### 规模不对称：写的比看得快

主要原因其实来自于规模不对称：AI 生成代码的速度，第一次显著超过人类审查的速度。

有时候 AI 一次性写出来上万行的代码，我其实很难仔细地逐一阅读和审查这些代码，只能做到草草看个大概。

这时候，debug-only 检查的相对价值在下降，always-on 保证的相对价值在上升。

Hacker News 上一条被广泛引用的评论说得很准：LLM 代码 99% 能跑，其余线上崩；contracts 只是让它崩在 violation handler 里。

还有个更细的问题：跨编译单元不一致的语义，对工具是致命的。

AI 和静态分析器要把 pre/post 当稳定前提推理，语义可变，前提就没了——Spicer 说的「不能当 must-run check 用」，翻成 agent 语言就是不能当可信前提用。

### 契约有用，但有权衡

三个实证说明契约有用、但有权衡。

PACT 用契约违反用例增强提示，契约指标提升 18.13 个百分点，但牺牲了功能正确性。

Fun2spec 在数百万行 C++ 上合成后置条件，87% 通过测试校验。「要不要有契约」在工程上已经不是问题，「执行语义稳不稳」才是。

最有戏剧感的一件事是：P4208R0 这一篇作者栏写着「Reply-to: Claude Opus 4.6」的 WG21 论文，用对抗式审查逐条审 P2900，11 个部分成立、1 条反而给出了反对意见。

论文自己披露的原话是：AI 的输出必须永远由人验证。

这个世界变化真是大。还记得，没几年前某次 CppCon 大会上，对委员会核心成员的 grill the panel 环节互动里面，还有一个专门处理文案工作的小姐姐，被 Herb Sutter 隆重介绍过。这位小姐姐的工作，显然已经被 Claude 替代了吧。

![](03-code-flood.png)

## 六、前哨战之后：谁给规格背书？

### Búzios 的裁决

接下来看 Búzios。11 月 16 日到 21 日 WG21 还要继续在巴西开会表决，SC22 主席有四条路：重新投票、修改草案、降级成技术规范、取消项目。

支持方论文 P4433R0 的诉求已经写明：不动 contracts，再投一次。

还有一种可能性来自于 ISO 工作小组的兜底机制：对于那些注册 36 个月但是还没过批准的提议，会被自动取消。所以这个决策，理论上拖到 2027 年底。

### 规格没有 oracle

但比 C++26 命运更大的事已经在发生。微软研究院的 Lahiri 今年 3 月给它起了名字：intent formalization——把非形式意图变成可检查的规格。

他断言，决定 AI 让软件更可靠还是只让软件更多的，就是这件事。而瓶颈不在生成规格，在验证规格：能验证代码的机器，验证不了规格——规格没有 oracle，除了用户本人。

尽管是纯文字的规格，还是有很多环境方面的约束，和自动化执行的测试验收方式可以来检查这些规格。

### 留给下一篇的问题

谁给规格背书？这是 contracts 之争的一般化版本，时间关系，我准备把这个话题留到下一篇深聊。

你的项目里，那些检查是随时可以关掉的吗？评论区聊聊。

如果读到这里，欢迎点赞 👍、收藏 ⭐ 备用，转发给正在被 agent 放养的朋友。关注「数解AI」，慢慢深入拆解。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  

**参考资料与数字溯源**

1. Robert Seacord（ISO C 委员会召集人）LinkedIn（2026-10-24）：DIS 投票 12/20 赞成、9/22 反对；官方记录未公开，本文均为据报道口径
2. Mateusz Pusz《The result of the C++26 DIS ballot》（2026-10-25）：反对票九国名单（波兰、美国弃权）；「据知」史上首次
3. wrocpp.github.io（2026-10-27，AI 生成、人工复核）：双阈值规则、四条出路、36 个月时限
4. The Register（2026-03-31）：Croydon 会议 C++26 技术工作完成，contracts 留任，投票 114:12:3；Bjarne「it's not minimal, it's not viable」
5. P4334R0《P2900 Contracts' fundamental flaws》（Stroustrup 等 5 人，2026-08-09）：救生衣比喻、保证 vs 检查、未完成三件套推 C++29、成本不对称论证
6. P4381R0（Spicer，2026-09-19）：「I chaired SG21. I also object to C++26 contracts」自清算
7. Herb Sutter trip report（2026-03）与 BeCPP 2026 讲稿：contracts 为 C++26 三块功能性安全之一；「Directly expressing intent helps AI (too)」
8. P3846R1（Doumler/Berne，2026-04）：承认「保证式执行是另一个需求，C++26 给不了」
9. P4433R0《Do not remove Contracts from C++26》（Doumler、Berne 等 16 人，2026-10-23）：Búzios 再投一次的诉求
10. P4208R0《C++ Contracts on Trial》（Falco，Reply-to: Claude Opus 4.6，2026-05-01）：AI 撰写的对抗式审查，11/12 站得住
11. PACT《Do Large Language Models Respect Contracts?》（arXiv 2510.12047）：契约违反用例增强提示 +18.13pp，牺牲功能正确性
12. Fun2spec: Code Contract Synthesis At Scale（Bloomberg/UIUC，FSE 2026）：数百万行 C++、87% test-validity
13. Lahiri《Intent Formalization: A Grand Challenge for Reliable Coding in the Age of AI Agents》（MSR，arXiv 2603.17150，2026-03）：瓶颈是验证规格，规格没有 oracle

#C++ #contracts #AI编程 #形式化验证 #数解AI
