---
title: "Rust真的是AI agent时代的最佳语言吗？192个任务辨证看看"
wechatUrl: "https://mp.weixin.qq.com/s/_QjsrRZ0hfxaepldCt5Lhw"
author: "数解AI"
date: "2026-10-22"
type: "行业观察"
series: "行业观察"
digest: "固定模型、固定工具、八种语言、192 个真实任务——目前最像样的一次实测里，Rust 简单任务通过率 74.7 全场第一，难任务掉到 24.7 垫底，全程最贵。口号传开，是因为三件不同的活被混成了一句。关键词：Rust、AI agent、编程语言、实测。"
cover: "00-cover.png"
keywords: ["Rust", "AI agent", "编程语言", "实测"]
---

我的许多skill里面内嵌的工具和命令行程序，一开始使用的是Python或者TypeScript写的，原因很简单：早期的agent对这两种语言拟合的最好，更容易一遍就好。

问题是很多时候，skill调用起来后，Agent会耗费很多时间等待不能秒回的调用操作。这个问题如此严重以致于我很快就要Rust重写了里面的绝大部分，今年下半年以来的开源模型和harness都能处理的很好了。

但最近半年，一句口号把这件「按活选语言」的常识，推成了时代判决——「Rust 是 AI agent 时代的最佳语言」。

支持者有论文，有生产案例，有名人站台。我把公开讨论和唯一一次像样的实测放在一起看，结果答案还是需要分两半来辨证看待。

## 一、这个口号，把三件不同的活混成了一句

口号能传开，是因为三件工作被混成了一句：

- Agent 写应用代码时，Rust 最好写——有人吹，测量不支持全面胜利
- 写 agent 的运行时、沙箱、CLI，Rust 常常更合适——成立，而且有生产案例
- 整个 AI 栈都该换成 Rust——几乎没有认真的人这么说

拆开之后，每一件都要单独算账。先说我自己站在哪。

![口号拆解：三股线拧成一股绳](01-three-claims.png)

当时我的主要想法是，不能让Agent耗费大量时间在等待。

那样的话，纵然你可以并行开很多个Agent，最终效率也会提升有限，况且操作者也很快因为在多个缓慢执行的Agent任务上下文里面切换而变得疲惫不堪了。

我的账算的是第二件：等不起的活。第一件——agent 写 Rust 是不是最好写——是另一笔账，得看测量。

## 二、正方真正抓住的一点：能编译就大致正确

支持者真正抓住的一点是：写代码变便宜以后，瓶颈从「写得顺不顺」，挪到「有没有一个不会被说服的检查器」。

OpenAI 联合创始人 Greg Brockman 今年 1 月的说法最直白：if it compiles, it's ~correct。

GoDaddy 的论文把机制讲了一遍：所有权、借用检查、穷尽匹配，把合法程序的空间压窄，无效实现执行前就被拒绝。

最硬的生产案例是 GitHub：Copilot 的 agent 运行时从 TypeScript 整体迁到 Rust，83 万行生产代码、128 个 PR、14.5 周，期间照常发版。

动机不是语言信仰，是要离开 Node 和 V8——旧架构逼着各语言 SDK 拉起 Node 子进程。迁完之后，一轮会话从 5.25 秒降到 292 毫秒，18 倍提升！

Rust给我们的关于编译通过即正确的承诺，很多时候其实需要深入去讨论。

很多时候这不过是一种过度承诺，尤其是业务逻辑上的错误，它就无能为力，更不要说令人发指的unsafe泛滥问题，和RefCell滥用问题，都会造成大量的谬误。很多问题其实并没有被编译器完全解决，而是被转移了。编译通过，只排除了一类错。而检查器本身，是有价格的。

## 三、实测：192 个任务，答案分两半

口号吵了大半年，最像样的测量今年 6 月才出来。

Kun Chen 用 Meta 的 ProgramBench 基准，模型固定 gpt-5.5、工具固定 Codex，八种语言各写同一批真实程序。

沙箱断网，每种语言带 top 100 依赖的离线镜像，共 192 个任务。结果不出意外地分为硬币的两面了。

![ProgramBench：简单任务 Rust 74.7 对难任务 24.7](02-bench-split.png)

简单任务上，Rust 平均通过率 74.7，全场第一。

难任务上，Rust 掉到 24.7，垫底。50 点的跌幅是所有语言里最大的，和 JavaScript、Go、Java、C 挤在低分区，Python 和 TypeScript 留在上面。

还有一笔全程最贵的账：Rust 平均每个任务 1.40 美元——构建轮次最多，每次修复付一次 cargo build。

以我在AI大泛滥时代之前，手撸十几万Rust代码的经验来看，这个bench的结果毫无意外。

很多深层次的问题，还是需要耗费大量的精力去调整，尤其是一开始设计错误某些方向，后面想要调整依然是麻烦不断。那些复杂的边边角角，其实在我看来，大概是软件布道师们选择性遗忘的大沼泽地。

50 点的跌幅，远超单次运行的噪声。问题变成：难任务上，Rust 输在哪？

## 四、难任务为什么崩：反馈循环按分钟计费

难任务上，Rust 输的不是写得对不对，是等不等得起。

前 Bun 工程师 zack 10 月初把话说白了：Rust 不再是 agent 的默认最佳语言，编译时间太长，瓶颈是时间不是智能。

Node 作者 Ryan Dahl 更直接：Rust 从来不是 agent 的默认语言，应用代码属于默认语言。

Flask 作者 Armin Ronacher 干脆给了选型：能选就上 Go——go test 有缓存、语言「马虎」agent 不容易猜错、生态十年向后兼容。

掘金那篇《当 AI 写代码遇见 Rust 为什么会卡壳》把体感写活了：逻辑对了，借用链没证明，编译器照样拒绝。

生命周期报错牵着函数签名、结构体和调用链一起动，不像 Go 的类型不匹配，能一步修好。所以「能编译就大致正确」的另一面是：为了能编译，每次重试都在付账。

简单任务上这笔账划算——逻辑直、轮次少。难任务上账越滚越大：错误螺旋、重试变多、每次等 cargo。

护栏是真的。但护栏按分钟计费。

![反馈循环：每一次重试都要付一次编译](03-feedback-cost.png)

## 五、Rust 真赢的时候：有答案纸的移植

那 Rust 到底什么时候真赢？看今年 10 月这一周发生的事。

TypeScript 编译器移植到 Go 的时候，Anders Hejlsberg 试过 Rust，放弃了。前面文章已经讨论过了，且看[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)，和[一个人重构了Copilot 80万行代码到rust](https://mp.weixin.qq.com/s?__biz=MzkyMzQyODExNQ==&mid=2247486496&idx=1&sn=352adf684b9e1974035ee3567ecefae5&scene=21#wechat_redirect)

理由不是性能：借用检查器不允许编译器里到处都是的循环数据结构——带 parent 指针的树、互相引用的符号。

硬拆，移植会变成重写，重写会变成另一门语言。他们用 Go 拿到 11.9 倍提速，错误信息不变。

一周后，Bun 和 Theo 用 agent 把这份 Go 代码搬进 Rust，而且更快。

bun check 在 Next.js 的 2881 个文件上 2.4 秒，tsc 6 要 14.8 秒。Theo 的 tsc-rs 烧了 5 个月、约 2 万美元 token，他一行没读。

做成的条件只有一个：答案纸已经存在。tsc 7 的错误码就是测试，Go 编译器是裁判。

![有答案纸的移植：tsc 到 Go 再到 Rust 的搬运链](04-answer-sheet.png)

我的例子之所以工作很好，是因为验证那些工具的成败与否逻辑非常明确，裁判就靠原来TypeScript版里面已有的参照测试用例。

如果是完全重头写过的skill工具，那照样还是需要大量的试错和复盘挖掘。

上个月那篇[《150 倍的账》](https://mp.weixin.qq.com/s/KjW6JgeQ0uJ6aDEFN8ohxQ)，算的是同一件事的另一面：没有答案纸的时候，agent 交付的是被任务书带偏的对照实验。

把三、四、五节放在一起，规律出来了：Rust 赢的不是「写」，是「有裁判的搬」。

## 六、按活选语言，不按时代口号选

所以答案分两半，不是和稀泥，是账本的两页：

- 模型、评测、实验胶水 → Python：库在那里，agent 第一枪命中率也在那里
- agent 产品、MCP、插件、界面 → TypeScript：热门 coding agent 的产品层大多这样，新 API 文档先到这里
- 新的后端服务，要快而确定的改-编译-测试循环 → Go：测试缓存、结构接口、向后兼容
- 运行时、沙箱、权限边界、必须嵌进别的语言的热路径 → Rust：前提是团队里还有人能审查所有权和架构

这个分解是挺合理的，不过还要加上约束和验收标准明确的地方，收益可能更大。

![四层分工：Python、TypeScript、Go、Rust 各管一层](05-layer-table.png)

### 最后一笔账，是人

人可以少写，不能不会读。编译通过只排除了一类错；架构差、测量不公平、行为只是看起来像，编译器都不说话。

团队里如果没有人能分辨「借用检查器在抓真 bug」和「agent 在讨好编译器」，Rust 会把审查能力一起拿走。

我的 skill 工具还是 Rust 写的。但那是因为它们等不起，不是因为 Rust 赢了时代。

你们自己的Agent生态，有没有引入Rust作为热点路径上的加速器，还是很多业务都拿Rust做了重写?

觉得这笔账算得清楚，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，AI 圈的数字慢慢拆解。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[Agent 写的 Rust 快了 150 倍，为什么第一版只快 4 倍？](https://mp.weixin.qq.com/s/KjW6JgeQ0uJ6aDEFN8ohxQ)

有空我们可以再仔细探究下，这半年 agent 写 Rust 为什么突然变顺了？harness层面到底发生了怎样的变化。

**参考资料与数字溯源**

1. Kun Chen (2026-06-10)：ProgramBench 实测，本文 74.7 / 24.7 / 1.40 美元等数字出处。
2. GitHub Blog / Stephen Toub (2026-09-17)：Copilot 运行时迁移，83 万行 / 128 PR / 14.5 周 / 18 倍。
3. GoDaddy / Jay Gowdy (2026-07-06)；Greg Brockman (2026-01-02)。
4. zack (2026-10-02)、Ryan Dahl (2026-10-04)；Armin Ronacher (2025-06-12)。
5. 掘金《当 AI 写代码遇见 Rust 为什么会卡壳》(2026-10-05)。
6. TypeScript 7.0 发布 (2026-07-08)；Anders Hejlsberg「试过 Rust」访谈 (2026-08-17)；Bun PR #44361 (2026-10-06)；Theo tsc-rs (2026-10-07)。

#Rust #AI编程 #AIagent #编程语言 #数解AI
