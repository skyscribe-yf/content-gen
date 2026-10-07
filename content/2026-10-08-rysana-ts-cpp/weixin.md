---
title: "微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍"
author: "数解AI"
date: "2026-10-08"
type: "行业观察"
digest: "微软用 Go 重写 TypeScript 花了 16 个月；一个 CEO 用 C++ 把它复刻到 100% 对位，账单约一万美元。当移植开始按 token 记账，选语言的记分牌就换了。"
cover: "00-cover.png"
keywords: ["TypeScript", "C++重写", "AI编程", "编译器"]
---

微软用 Go 重写 TypeScript，花了 16 个月，今年 7 月才正式发布。

这个月，一个人用 C++ 又把它写了一遍。

他叫 John，Rysana 的 CEO——公司主业是超高速 AI 推理。最新的进度推文里，他这么说：

> C++ port of TypeScript (targeting TS6) is now 100% at parity. It's 25-750x faster and 5-20x lower RSS. Matches TS6 1:1 on every test, every diagnostic is identical given the same inputs…

翻译一下：测试全过、输出对位，**每一个报错（diagnostic）都和原版逐字一致**。速度上，他的口径是快 25 到 750 倍。

第一次看到这个项目，还是觉得有点终于有人愿意干这种苦力活了，以今天AI模型的能力，多久可以干完呢？原来Anders团队做的架构选择终于是在AI时代被推翻了吗？

这两个问题，也是这篇想弄清楚的。

## 一、微软的 16 个月：第一批被划掉的，恰恰是 C++

2025 年 3 月，微软 TypeScript 团队宣布：编译器移植到 Go，代号 Corsa。

掌舵人 Anders Hejlsberg 是 TypeScript 之父，也是 C#、Delphi 的设计者。他反复强调一个词：是移植（port），不是重写（rewrite）。结构和语义要尽量保留，连历史怪癖都照单全收。

2026 年 7 月，TypeScript 7 发布。官宣的数字：VS Code 这种量级的代码库，完整检查从 77.8 秒压到 7.5 秒。

为什么是 Go？Anders 的理由全是一手工程约束：Go 有自动内存管理、支持循环数据结构、能编译成全平台原生码、并发顺手。C# 范式对不上——编译器核心连类都没有，全是函数和数据结构。Rust 也认真试过，方案一次次撞回同一堵墙：要么自己实现一套 GC，要么满身 unsafe。

落到一句话：这是移植，背后是 100 人年、50 万行的存量代码，等价性要逐字成立。选型不是在挑一门更酷的语言，是在挑一个能按期干完的方案。

为什么宁可移植也不重写？其实重写导致项目整体翻车，工作量被严重低估，问题难度在项目临近正式交付阶段，随着测试推进被急速放大，最终导致项目难产的例子可是屡见不鲜，可以说是软件工程的经典难题了，所谓Fred Brooks所说的焦油坑就是描述这种问题的，所以我猜想这也是微软宁愿选择移植也不重写的基本逻辑。（Fred Brooks，《人月神话》作者。）

## 二、更扎心的是：AI 试过，也不行

这套逻辑最扎心的注脚，来自 Anders 今年 1 月的一次访谈：他们考虑过让 AI 来做这次移植。

"我们试了，"他说，"That went not so great（不太行）。"原因也直白：要的是确定性——50 万行代码翻过去，行为必须和原来一模一样。让 AI 逐段翻译，"它可能这里那里幻觉一下，然后你就得逐行检查"。

他认可的另一种用法：让 AI 写"帮你移植的程序"——程序跑起来是确定性的。

这不是他一个人的体感。其实几个月前的最前沿AI，拿来写最复杂的项目也是屡屡碰壁的，改了东边漏了西边，按下葫芦起了瓢的事情可是屡见不鲜，更不要说是大模型早期常见的[死循环现象](https://mp.weixin.qq.com/s/HRHYjokuMpkjK0DhEAVOxA)和严重的reward hacking现象了。

reward hacking 的威力我们拆解过。机械臂蹭一下桶盖就能骗到高分——[《奖励函数才是 AI 钻空子的源头》](https://mp.weixin.qq.com/s/boIPBlmyX2ahoFYnEVLjxw)。

然而到了 2026 年下半年，这些"不行"开始批量过期。

## 三、然后是 John：约 10 万行、3 万个测试、每个报错逐字一致

先解释一句：John 复刻的是 TS6——JS 线上跑得最久、被当作行为金标准的那一版。速度对比的对手，才是微软刚发布的 Go 版 TS7。

下面的数字都来自他本人公布，暂无第三方验证。

10 月 1 日，他的 C++ 版 66,536 行。到 10 月 7 日，涨到约 10 万行：30,000+ 个测试 100.00% 通过，大项目对比全部对位。诊断输出逐字一致，内存（RSS）低 5 到 20 倍。

价格更有意思。10 月 2 日他算了笔账：这几天在移植上"花掉了大约一万美元的推理"（$10,000 of inference）。他的原话是："换成人类专家团队，得干好几年；而我没花多少时间。"

不知道这个费用是否是纯API费用，还是多个账号的订阅？反正是氪金的装备还是要有的，换算成程序员工资的话，也没有表面看起来那么多了，关键是这个几天时间有些太夸张了，甚至这个像素级的复刻才是当前AI模型恐怖实力的最直接表征！

动机也写在推文里：让"高速 AI coding agents"受益。

随着agentic coding实践的加速落地，我估计很多人都会发现，本地跑工具验证，或者其他脚本运行的时间，很多时候都已经大大超出了LLM推理和网络延迟的部分，我个人的比例甚至是1：3以上了，所以这些被调用的小工具，编译器检查，测试case验证等操作如果能被提速，是可以降低整体的等待时间的。当然如果你的场景都是跑一些玩具项目，从来不做验证，只靠一把梭哈，那么收益就很小了。

![两条重写路线：16 个月 vs 十天窗口](01-race.png)

## 四、这不是孤例：移植正在变成流水线

上个月，微软自己交过一份更硬的作业。GitHub Copilot 的 runtime 从 TypeScript 迁到 Rust。

43 万行 TS 变成 80 万行 Rust，大部分由 AI agents 完成。账单约 12 万美元的 token，加三周人手。基准里，吞吐（每秒会话数）7.55 → 120，15.9 倍；内存 1383MB 掉到 126MB。官方博客的原话是：这活手工做，"要花好几年、几百万美元"。

Bun 也差不多：53.5 万行 Zig 迁成 Rust，几乎全靠 Claude agents。测试通过率 99.8%，账单约 16.5 万美元。

后面两个数字还是让我情不自禁地换算了一下人民币等值是多少钱，居然超过一百万了！试想又有多少软件项目自身的价值能够超过一百万？

![三笔账单：$10K、$120K、$165K](02-bills.png)

连应用层也开始了。今天刚见报的 ArtCraft，用七个纯 Rust 应用给 Adobe 全家桶做了 clean-room 复刻。仓库根目录里，AGENTS.md 和 CLAUDE.md 直接躺着。

同一件事，Rust 阵营也有人在干——一个叫 ts-rust 的项目。John 顺手比过行数：据他说对方约 75 万行，自己的 C++ 只有约 10 万行。末了还丢下一句，"Rust 是不是太啰嗦了？"

## 五、先把账记上

三句"但"，免得变成爽文。

但一：所有数字都是他的自报口径，第三方验证还没有。口径本身也在滚——1000 倍、10 倍、25 到 750 倍，一路在变。

但二：100% 是"行为一致"，测试和诊断对得上；不等于生态可用。移植版他自己说"快发了"，但还没发。

但三：这波潮也有代价。Copilot 那次移植留下过几十处"能编译但行为不对"的回归。Bun 的 Rust 版被 Zig 作者骂过 "unreviewed slop"。"if it compiles, it's correct" 只是个段子。

改写的是逻辑，不是代价。

整体上我觉得还是很魔幻，尽管后遗症也是客观存在的，还是需要多一些乐观积极的态度，采用胡适之先生提倡的思维，加上一些小心的求证就好了。

## 六、被改写的，是那道选择题

回到开头那两个问题。

"多久可以干完"——微软答：16 个月加一个团队。John 这边，公开可查的只有推文上的十来天窗口，真实工期他没展开，先别急着把"几天"当结论。

"被推翻了吗"——Anders 们的选择没有错。换到 2026 年，Go 依然是那批约束下最稳的解。变的是等式本身。

旧记分牌上写的是人类工程约束：有没有 GC、移植性好不好、团队会不会维护、重写会不会翻车。当年每一项都指向 Go。

新记分牌上写的是机器与 agent 的约束：能跑多快、吃多少内存、能不能嵌进别人的系统。agent 的反馈循环受不受得了它，也是老账新算。当移植可以按 token 记账——一万美元、十二万美元、十六万美元——"谁来写、谁来维护"就不再是第一问。

一度编程语言作为软件架构最大决策的这个基本逻辑，已经被改写了。不是说编程语言这个架构决策变得完全无足轻重了，而是它考虑的要素和约束完全不同了。

![两块记分牌：旧表算人月，新表算速度与内存](03-scoreboard.png)

现在就宣布"语言随便选"还太早。移植是一回事，生态是另一回事，Anders 说的"逐行检查"也不会消失。但方向已经露头：人类成本项退场的速度，比所有人预料的都快。

选语言从来不只是技术题，它是"谁写、谁维护、谁承担翻车"的组织题。AI 把最后一项的定价改掉了，这道题就再也不是原来那道题。

如果只转一句话给同事：**当移植能被按 token 记账，选语言的第一问就不再是「谁来维护得起」。**

如果能在token管够的情况下，改写你手头的复杂项目，你希望选择哪门编程语言，主要考虑是什么？

觉得这篇把"选语言"这笔账算清了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，AI 原理和工程，慢慢拆解。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[随机变量为什么不是变量？它其实是个函数](https://mp.weixin.qq.com/s/5BxjOUblW64DXNffHc2sxQ)  
[机械臂蹭一下桶盖，成功率高10%：奖励函数才是AI钻空子的源头](https://mp.weixin.qq.com/s/boIPBlmyX2ahoFYnEVLjxw)  
[DeepSeek为什么会死循环?OOD是死穴](https://mp.weixin.qq.com/s/HRHYjokuMpkjK0DhEAVOxA)  

**参考资料与数字溯源**

1. John（@jrysana）推文系列（2026-09-27 ~ 10-07）：首推 ~1000x、测试数超 TS7、full 1:1、66,536 行、$10,000 inference、nearly feature-complete、100% at parity（25-750x）。均在 x.com/jrysana。
2. Anders Hejlsberg 官宣博客《A 10x Faster TypeScript》（2025-03-11）：devblogs.microsoft.com/typescript/typescript-native-port/；选型讨论汇总见 TheNewStack（2025-03-18）与 microsoft/typescript-go Discussion 411「Why Go?」。
3. Anders 谈 AI 移植「went not so great」：devclass（2026-01-28）。
4. TypeScript 7.0 GA（2026-07-08）：devblogs.microsoft.com/typescript/announcing-typescript-7-0/。
5. Copilot runtime 移植 Rust（430K→800K 行、$120K、15.9×）：devclass（2026-09-19），工艺文见 GitHub 博客。
6. Bun Zig→Rust（535K 行、99.8%、$165K、「unreviewed slop」）：devclass（2026-09-19）。
7. ArtCraft「Crafting Apps」七应用：getartcraft.com/apps；快科技-新浪财经（2026-10-07）。

#TypeScript #AI编程 #编译器 #大模型 #数解AI
