---
title: "一年没写过一行代码的 C++ 老手，怎么保证代码不出事"
author: 数解AI
date: "2026-11-30"
type: "实践篇"
series: "软件工程"
digest: "一年没写过一行代码的 C++ 老手，靠四个 AI 审查 agent 把住代码质量——CppCon 2026 上 C++ 与 AI 共存的工程答卷。"
cover: "00-cover.png"
keywords: "C++, AI, CppCon, 多智能体, 代码审查"
wechatUrl: ""
---

2026 年 9 月，美国科罗拉多，CppCon 2026。一个有四十年经验的C++老手上台演讲，先坦白交代了一件事：自从去年 11 月之后，他一行代码没亲手写过了——不是不写，而是每一行都出自 AI 之手。台下坐着的 C++ 程序员，第一反应大概都是「你在扯吧」。

可他把问题直接给甩了出来：把键盘整个交给 AI 的人，又怎么能保证代码不出事？

## 先立人：AI 从访客变成了房间

站在演讲台上的是 Jody Hagins，LSEG/MayStreet 高频交易基础设施的工程师，日常对付的是 feed handlers、数据规范化和低延迟系统，写 C++ 写了四十年。

他有足够的资格来怀疑 AI：1980 年代研究生阶段他就做起了 AI——Lisp、Smalltalk、基于模型的推理，还两度穿过 AI winter 活着回来，所以他的怀疑不是叶公好龙式的怀疑。

他的结论是：工具终于追了上来，但只对那些愿意伸手的人。演讲摘要里他把这一年说得更直白："A year ago, AI was the visitor we were evaluating. Now, it is the room we work inside, and the question for C++ programmers is no longer whether to take the technology seriously but how to keep doing serious work in its presence." 

翻译过来意思是这样的：一年前，AI 是我们评估的访客；现在，它是我们在其中工作的房间，C++ 程序员要回答的不再是要不要认真对待这项技术，而是怎么在有它的房间里继续做严肃的工作。

他也提前给自己定了调："It is not a theoretical presentation, but a working practitioner's report."——这不是理论展示，是一线实践者的工作汇报。

其实这个演讲并不是一个孤例，翻看cppcon的其他一些主题演讲，整体上对AI的态度已经变成了几乎全盘接受和略显无奈的冷寂。

## C++ 简直是 AI 最不想碰的语言

为什么「房间感」在 C++ 这边格外强？看看 CppCon AI++ 201 课程页列出的五大挑战就懂了。

其一，编译延迟直接打破快速迭代的反馈环，AI 改完一行要等很久才知道对错；其二，头文件和源文件分裂成两处，AI 得同时盯着两边才拼得出全貌，上下文需求被放大；其三，模板错误信息"read like encrypted ransom notes"——读起来像加密勒索信；其四，未定义行为能编译、能跑、但是错的，AI 连自己错在哪都不知道；其五，构建系统的复杂度是又要穿越的一层。

这五条因素叠加起来，会导致C++几乎像是 AI 最不想碰的语言。至于语言选型和 agent 的适配性，我们之前用 192 个真实任务辨证过 Rust（见《[Rust真的是AI agent时代的最佳语言吗？192个任务辨证看看](https://mp.weixin.qq.com/s/_QjsrRZ0hfxaepldCt5Lhw)》）：同一门语言，简单活通过率第一、难活垫底——顺不顺手，取决于你让它干什么。

偏偏是对 AI 最不友好的语言，最先摸出了一套完整活法。

![C++ 对 AI 的五大不友好](02-cpp-ai-friction.png)

联想到最近X上还有一些鼓吹Rust的程序员慢慢回到了 C++，有时候客观冷静的观察和判断，应该比跟风和热潮显得更重要。

## 他的答案：四个审查员，各看一遍

同时在另外一场 workshop 预告视频里，Hagins 的原话只有一句："I have code reviews done by four separate agents."——我的代码审查由四个独立的 agent 完成。

注意，不是一个通用助手大包大揽，而是四个各带 persona 的专职审查员。persona 就是给模型指派的身份：换身份不换模型，模型的判断口径也会跟着变。

你还在质疑这种额外加一个身份提示的prompts是否真的能产生作用的时候，别人已经将那些你看不上的奇技淫巧，系统化地打磨来提高代码review的效率。

### 四个审查员，各看一摊

常规审查员的提示词被限定在具体目录里，产出写进 feedback.md，还被明确切断了构建权限——"you do not have access to build tools. Do not build anything." 你无权使用构建工具，什么都别构建。

API Audrey 专盯接口设计；Nate 的人设是 1970 年代贝尔实验室的 C 老手；还有一位安全关键老将，履历是 NASA、核电站、导弹发射井那一路。

他的纪律要求说得很清楚："None of them should be tasked with reviewing everything. Their focus is very small and confined." 他们都不该被派去审查所有东西，焦点必须小而封闭——小焦点才能查深。

大家逐渐取得的共识是，小而专精的agent往往能收到奇效。

### 小焦点，再汇总

四个审查员之外，还有一个汇总 agent，把四份审查汇成一份「改什么」清单；他甚至会让一个模型专门分析四份审查之间的分歧——分歧本身就是信号。

为什么换身份有用？Hagins 的答案是："Models behave differently when you give them personas." 你给模型 persona，它们的行为就不同——套身份几乎零成本，却是最便宜的控制手段。

现场共识也在往这边靠：另外一位大会的演讲者Alexandrescu 的 slide 写着"stop using an agent"，全场先是惊讶，因为**所有人都听见他把重音放在了单数上，他接着说的是要用多个**。

讲代码审查出身的 Muldoon 补了一刀：AI 让写代码变快了，没让审查变快，一个没人认真读就批的大 PR，只是把问题从「写」搬成了「审」。多 agent 的价值不在数量在分工，这点我们在《[Anthropic 实测多智能体强 90%，为什么另一家说千万别建？](https://mp.weixin.qq.com/s/Y6aPD8t8h2-KCUseKXc0mQ)》里也掰过。

这里没说的其实是，用agent来审查代码真的很慢，比写代码要慢得多，生成是非常简单了，验证可能比生成要重要的多。

![四审查员工作流示意](01-four-reviewers.png)

## 小步快跑：把编译器的反馈喂回 loop

审查之外，他还总结了一套工作策略，全部围绕一件事：别让 AI 一次吞太多。

总结起来的套路就是：

- smaller changes，改动切小；
- compile-after-every-change，每改一处就编译一次；
- fast-compiling test files，准备好编译飞快的测试文件；
- showing both files，把 .h 和 .cpp 同时摆到 agent 眼前；
- explicit instructions about what goes where，明确告诉它什么放哪。

这一串动作连起来，就是一个 agentic loop——模型自主「读、改、跑」的循环——而他的策略本质上是在给这个循环装上密集的反馈点。

课程页上他的收尾金句是这样写的："Every line comes from Claude Code. You prompt, you guide, you review, you course-correct, but your fingers don't type C++." 

每一行都出自 Claude Code，你提示、你引导、你审查、你纠偏，但你的手指不敲 C++代码。

他也不迷信现成工具，AI++ 101 的宣传语是："Not Claude Code. Not Cursor. A simple thing you fully understand." 不是 Claude Code，不是 Cursor，是一个你完全理解的简单东西——harness（你给模型搭的那套外挂架子）要自己搭，你得知道 loop 的每个零件，才知道该在哪一环加控制。

其实在上一场 talk 里，他直接完整搭出来了一个 OPRA feed handler，没手写一行代码。

![小步快跑：把反馈点密集装进 agentic loop](03-agentic-loop.png)


## Daisy 的坚守：会困惑人的，就会困惑 agent

另一半答案来自 CppCon 2025 keynote 上的 Daisy Hollman，Anthropic Claude Code 团队成员，在 WG21 混了八年多，mdspan、executors、atomic_ref、ranges 都有她的份。

她把 C++ 程序员在 AI 之上做的大部分事情归结为一件：工程化 context window——按她的原话，它就是"the input layer to the model"，模型的输入层，喂什么、喂多少、什么时候压缩，全是这门工程的手艺。

她现场的警告更加振聋发聩："Even though C++ allows them, doesn't mean you should do them. You're going to confuse people. And if you're going to confuse people, you're going to confuse agents." 

C++ 允许你那么写，不等于你该那么写——你会困惑人，而你会困惑人，你就会困惑 agent。

她让模型做了一批 C++ 小问题，ADL 这类「同 token 难关联行为」的特性出错最多。所以她的建议是："Prioritize better encapsulation." 优先做更好的封装——封装良好、单测充分、不再人肉去碰的模块，才是可以托付给 agent 的单元，封装既是给人看的，也是给 agent 画的安全边界。

她的 C++ 建议没有一条是新的。software craftsmanship的手艺活技巧并没有过时，只是受众多了一个。

![上下文工程：context window 像一张桌子](04-context-window.png)

听起来感觉惊讶吗？其实毫不意外，现在的大模型是基于概率的，困惑读越高的场景，模型表现的越差。反而是当你把可能的输出分布限制的越紧的时候，输出的确定性越大，甚至到不确定性可以忽略的地步，你就赢了。

## 暗线：标准委员会在contracts上的撕扯

巧的是，同一时期的 WG21 也在吵一个同层的问题。

C++26 技术工作 2026 年 3 月 28 日完成，contracts（pre/post/contract_assert）以 114:12:3 留在标准里；DIS 国际投票据报道被否；11 月的 Búzios 会议接着处理分歧——截至目前，分歧尚未解决。

这场冲突，表面是 contracts，底层是同一个问题：AI 时代，什么才叫「可检查的意图」。Sutter 在 BeCPP 2026 给了一页直答："Directly expressing intent helps AI (too)"——直接表达意图，对 AI 也有帮助。

语言特性上来看，range-for、lambda、concepts、contracts，语言一直在演化成能直接表达意图的形态；签名上的 pre/post，让人、静态分析器、优化器、AI 都不必去推 body 里到底发生了什么。

反方（Bjarne 阵营）的质疑也有一句：给不了保证的可选检查，救不了大规模 AI 生成代码的审查。两边的完整论战，我们在《[60% 的赞成票，为什么救不了 C++26？](https://mp.weixin.qq.com/s/FE4WEuT1-Ozz4uYtvfCG7w)》里展开过，这里不重复。

工业界倒先动了手：Shopify 为让 AI agent 改主题页更顺，反过来把架构改成「人好读、显式契约、反馈清楚」——agents just want the same things as humans，agent 想要的，和人想要的一模一样。

其实矛盾的地方还是在于，如何让意图的表达更少有歧义，这样人类程序员和Agent程序员都能更确定地完成高层意图。

## 总结

两场演讲拼起来是一句话：AI 没有降低对 C++ 工程师的要求，它把要求从「写」挪到了「审、架构、封装、判断」。

四十年老手的答案是四个各带 persona 的审查 agent 加一个汇总 agent，小步快跑把编译器的反馈喂回 loop；WG21 老兵的答案是会困惑人的构造就会困惑 agent，封装和单测这些三十年前的老忠告一条都没过时。

这场大会的复盘里，老牌 C++ 博主 Dargo 有句话更扎心："accepting the machine's diff feels like signing someone else's work." 接受机器交上来的 diff，感觉像在别人的作品上签名——签之前，你得看得懂。

这正是《[写代码已经不再是瓶颈，交付依然困难重重，AI Native SDLC能解决吗](https://mp.weixin.qq.com/s/ljp5ovIFPI3l9rmlGDDZUw)》里那个瓶颈的 C++ 版本。

### 你的答案

前面文章的评论区里，还是有不少古法的程序员对AI coding嗤之以鼻，看完顶级社区大佬们的分享，你觉得自己的想法会被改变吗，还是会更加坚持自己的观点？

如果读到这里觉得有所启发，欢迎点赞 👍、收藏 ⭐ 备用，转发给写 C++ 的朋友。关注「数解AI」，AI 原理和工程，慢慢深入拆解。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  

**参考资料与数字溯源**

1. CppCon Academy AI++ 201 课程页（Hagins）：https://cppcon.org/class-2026-ai201 ——五大挑战清单、小步快跑策略、「Every line comes from Claude Code」与 OPRA feed handler 实测口径
2. CppCon Academy AI++ 101 课程页（Hagins）：https://cppcon.org/class-2026-AI101/ ——「Not Claude Code. Not Cursor. A simple thing you fully understand」与履历口径
3. Daisy Hollman keynote 页（CppCon 2025）：https://cppcon.org/2025-keynote-daisy-hollman ——「the input layer to the model」「Prioritize better encapsulation」引文出处
4. Herb Sutter trip report（2026-03）：https://herbsutter.com/2026/03/ ——114:12:3 投票结果原文「114 in favor, 12 opposed, and 3 abstaining」
5. Sutter BeCPP 2026 讲稿《C++: Growing in a world of competition, safety, and AI》——「Directly expressing intent helps AI (too)」一页

#CppCon #软件工程 #AI编程 #数解AI