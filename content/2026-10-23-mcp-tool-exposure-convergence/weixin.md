---
title: "pi 和 OpenAI 不约而同：MCP 工具，答案本来就应该长这样"
wechatUrl: "https://mp.weixin.qq.com/s/jJHG1bn2_F10kmZ0pBCm5Q"
author: "数解AI"
date: "2026-10-23"
type: "工程观察"
series: "AI Agent 工程"
digest: "OpenAI 给 Codex 合了一个 PR，两个月后 pi 发布 1.0，再往前 Anthropic 已经把按需搜索做进默认。三家没商量，写出了同一张图纸：工具定义不进上下文，按需加载，或交给脚本。而三家又都不敢把它设成默认。关键词：MCP、三档暴露、工具搜索。"
cover: "00-cover.png"
keywords: ["MCP", "三档暴露", "tool search", "AI Agent"]
---

2026 年 8 月，OpenAI 给 Codex 合入了一个不大的PR，改动的总结是这样写的：MCP 工具被分三种方式暴露——直接声明、按需搜索、或者只许代码模式调用。

如果故事到这儿结束，这只是 OpenAI 的内部改动。但两个月后，另一家开源当红agent公司发布的pi 1.0，文档里是同样的三档。

如果再往前回溯大半年，你会发现Anthropic早已经把按需搜索做进了 Claude Code 的默认行为。

谁也没牵头，谁也没跟风。答案本来就应该长这样，才是唯一合理的选项。

上一篇[骂 MCP 最响的人，最终把 MCP 请进了核心](https://mp.weixin.qq.com/s/qp7XGIEJdMgSto5YN2T-rg)讲的是 pi 怎么把 MCP 请回核心。这篇换一个角度仔细看看：另外两家是怎么解决同一个问题的。

## 一、同一个问题，三个团队，同一张图纸

Anthropic又是如何处理MCP带来的上下文严重膨胀的问题呢？codex如何应对这个挑战？

先把时间往前拨。这套东西最早的命名者不是这三家，是 Cloudflare。

2025 年 9 月，Cloudflare 发了篇博客讲「Code Mode」：他们 2500 多个 API 端点，如果按「一个端点一个工具」全塞进上下文，工具定义要吃掉 117 万 token，超过任何模型的窗口。、

他们的解法是两个工具，约 1000 token，降了 99.9%。

Anthropic 的做法是分层下药。

定义层是 Tool Search Tool：工具定义不进上下文，只给一份摘要，模型按需搜索加载，最多同时加载 5 个。官方给了一个自动开启的阈值：可推迟的定义占到上下文窗口的 10% 就自动激活。

官方给的两个理由很实在：50 个工具的定义要占 10K 到 20K token；超过 30 到 50 个工具之后，模型的选择准确率会下降。后者跟 token 无关，是注意力问题——[Context Rot 是真的吗？上下文还没满，模型为什么就先认输了](https://mp.weixin.qq.com/s/6bdNSe1hiGFUvL1qV_ICUw)已经深入拆解过这个问题了。

Codex 的动作分两步，第一步容易被忽略：2026 年 6 月，MCP 工具就已经默认走 tool search 了。在那之前，只有当开了 feature flag 或者工具数超过 100 个，工具才会被藏进搜索后面。6 月这个 PR 把这个条件直接删了——无条件默认。

8 月的 PR 才把三档补齐：直接声明、按需搜索、只许代码模式调用，服务器可以针对每一档单独退出。到了 v0.119.0，一个 200 个工具的服务器连上来，不再注入 200 份 schema。

pi 这边，上一篇详细拆解过它的四档：直接声明、按需搜索、只许脚本调用、隐藏。但是有一个细节还是值得单独拎出来说道说道。

这个重要的点就是，对与按需搜索档的工具，不放进描述里面去。所以 MCP server 连上来的时候，系统提示里的工具段落压根不变——这是为 prompt cache 的经济性角度考虑而做出来的设计取舍。

同样的问题，雷同的设计，难道这真的是巧合吗？

![三家独立收敛到三档暴露的时间线：Anthropic 2026-01 默认、Codex 2026-06 默认搜索、2026-08 补齐三档、pi 2026-10 落地（图源：openai/codex PR #29486 与 #36781、code.claude.com/docs、pi 官方文档）](01-convergence-timeline.png)

三家文档摆在一起，同一张图纸：工具定义不进上下文，要么按需搜索，要么交给脚本。

![三档暴露对照：直接声明 / 按需搜索 / 代码调用——三种语言，同一张图纸（图源：openai/codex PR #36781、code.claude.com/docs、pi 官方文档 mcp.md）](02-three-tiers.png)

## 二、代码跑在哪一侧，三家给了三个答案

三档暴露只是入口。真正的分歧在：那段编排代码，跑在谁的机器上。

pi 的沙箱在 harness 侧，跟着工具流水线走，每次调用仍过权限闸门，调用链可审计。

Anthropic 的代码沙箱在服务商侧，是 Code Execution 工具。中间结果由脚本消费，根本不回客户端。

Codex 的沙箱是本地 V8 隔离环境，exec 和 wait 两个工具，脚本就躺在本机，用户能读。

对于我个人而言，透明可审计一直是至关重要的。要不然，编辑在哪个地方跑偏了，事后怎么追查原因，怎么做针对性改进呢？

三种位置对应三种信任模型：可审计、不回传、可复现。这不是谁强谁弱，是三套不同的账。

![三种代码沙箱位置：harness 脑侧（可审计）、服务商侧（结果不回传）、本地 V8（脚本透明）](03-placement.png)

## 三、工具吐回来的东西，太大了

编排之外还有个现实问题：工具一次吐回来的东西，比模型能吃的多得多。

pi 给两条路。走 bash，模型只看尾部 2000 行；走 codemode，同一个工具的大结果最多给 1 MiB，超了保留头尾，落盘留全量路径。

Anthropic 的答案是让中间结果死在脚本里：模型只看最终输出，过程数据不过它的眼。

Codex 管的是限额本身：每个工具有自己的 output_token_limit，超了才截断，而且截断之前有个 hook 先跑，脱敏、格式化都赶在字节进上下文之前。

大概一年前，模型还不是那么聪明的时候，经常会不知不觉地组合出一个看起来很弱的bash脚本来，这样的脚本最终很可能会产出海量的输出，倾倒在本来就捉襟见肘的上下文里面。

这个问题其实并没有随着模型进化被完全解决，大规模强化学习训练其实仅仅是部分缓解了问题。除了去努力优化工具的命令提示和文档外，类似context mode这样的工具一直是备受欢迎的一种解决方案。

![结果侧三种管法：bash 尾部 2000 行、codemode 1 MiB 封顶、per-tool 限额加 hook（图源：pi 官方文档、Anthropic engineering blog、OpenAI 官方配置参考）](04-result-limits.png)

## 四、谁也不敢默认开

到这里，收敛的故事该收尾了。但三家还做了一个不约而同的决定：谁都没敢把它设成默认。

pi 只在 MCP 开启时自动启用代码模式，作者亲口给的四个理由，上一篇也说过了：benchmark 不够、编码层次麻烦、功能本身占 system prompt、小模型会过度使用。

Codex 官方配置页上白纸黑字：这个功能 under development，off by default。而且这句话背后有一个真实的事故：一个 issue 里，稳定版 IDE 把开发中的代码模式静默带进了用户线程，模型开始自己签发终止指令，把还在正常运行的 MCP 调用给毙了。那个 issue 至今还挂着没有很好解决。

Anthropic 这边，tool search 是 beta，遇到老模型或者走代理，直接回退成全量加载。

我其实非常能理解他们设计方面的谨慎，因为目前细则上还是不太具有明显的确定性收益。很多时候具体效果还不得不量体裁衣，视具体情况而定。

三家独立收敛，又独立默认关。这不是保守，是同一份判断做了三遍：方向对，但收益不确定、成本确定，赌注就压小。

目前这个阶段，务实的态度还是根据实际的需求场景和测试效果，多测试多改进，并密切关注进一步的演进才是正解。

![三家代码模式的默认状态：pi 仅 MCP 下自动开、Codex 官方明示默认关、Anthropic beta（图源：OpenAI 官方配置参考 2026-10-21 现读、lobste.rs 作者回复、code.claude.com/docs）](05-default-off.png)

## 五、地皮还是不够分

所以，三家不约而同换掉的，是同一个默认值：工具定义全量灌进上下文。

溢出有人治，涣散有人治。但还有第三种病没人治——撞车。

工具定义、工具结果、会话历史，都在抢同一块有限的地皮；而两条信息互相打架的时候，没有任何一家有冲突检测层，全靠人在 loop 里发转舵指令。[Context Rot 是真的吗？上下文还没满，模型为什么就先认输了](https://mp.weixin.qq.com/s/6bdNSe1hiGFUvL1qV_ICUw)

还有一个至关重要的问题，是如何更好地维护上下文窗口内信息的密度和混淆情况，有空下次再探讨吧。你觉得这个缺失的冲突检测，该长什么样？

觉得这篇把三家的路子讲清楚了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，AI 原理和工程，和你一起慢慢深入拆解。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[骂 MCP 最响的人，最后把 MCP 请进了核心](https://mp.weixin.qq.com/s/qp7XGIEJdMgSto5YN2T-rg)  
[Context Rot 是真的吗？上下文还没满，模型为什么就先认输了](https://mp.weixin.qq.com/s/6bdNSe1hiGFUvL1qV_ICUw)  

**参考资料与数字溯源**

1. openai/codex PR #36781「Add per-surface MCP tool exposure controls」，merged 2026-08-03
2. openai/codex PR #29486「Use tool search for MCP tools by default」，merged 2026-06-22
3. OpenAI 官方配置参考 developers.openai.com/codex/config-reference：features.code_mode.enabled 原文 "under development and off by default"，2026-10-21 现读核
4. openai/codex issue #29122（状态 open，2026-06-19 建，2026-07-23 更新）：稳定版 IDE 静默激活开发中代码模式、模型签发 terminate:true
5. Anthropic《Advanced Tool Use》，anthropic.com/engineering，2025-11-24（Programmatic Tool Calling：脚本消费中间结果、模型只看终点）
6. Claude Code 文档《Scale to many tools with tool search》，code.claude.com/docs：50 工具占 10-20K tokens、超 30-50 个工具准确率下降、默认最多加载 5 个、ENABLE_TOOL_SEARCH=auto 的 10% 激活阈值（2026-10-22 现读核）
7. Cloudflare《Code Mode》，blog.cloudflare.com，2025-09-26（命名来源）；《Code Mode with MCP》，2026-02-20：2500 端点 1.17M tokens → 2 工具 ≈1000 tokens
8. pi 官方文档 codemode.md / mcp.md（本机 @earendil-works/pi-coding-agent）：四档暴露、bash 尾部 2000 行 vs 1 MiB
9. 系列前篇：[骂 MCP 最响的人，最后把 MCP 请进了核心](https://mp.weixin.qq.com/s/qp7XGIEJdMgSto5YN2T-rg)；[Context Rot 是真的吗？](https://mp.weixin.qq.com/s/6bdNSe1hiGFUvL1qV_ICUw)

#MCP #三档暴露 #tool search #上下文工程 #数解AI
