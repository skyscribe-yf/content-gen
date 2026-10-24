---
title: "骂 MCP 最响的人，最终把 MCP 请进了核心"
wechatUrl: "https://mp.weixin.qq.com/s/qp7XGIEJdMgSto5YN2T-rg"
author: "数解AI"
date: "2026-10-21"
type: "工程观察"
series: "AI Agent 工程"
digest: "pi 从骂 MCP 到把 MCP 请进核心，靠的是一个叫 codemode 的功能。GitHub Copilot 的工具定义曾吃掉 73% 的上下文，连官方都砍到了 13 个工具。换掉的不是 MCP，是全量灌工具声明这个默认值。关键词：MCP、codemode、上下文工程。"
cover: "00-cover.png"
keywords: ["MCP", "codemode", "上下文工程", "AI Agent"]
---

2025 年 7 月，Flask 的作者 Armin Ronacher 写了篇文章骂 MCP。MCP 是 Anthropic 2024 年 11 月开源的工具协议，本意是让 AI 接工具即插即用。

他开骂的主要是MCP的两宗罪：不具有可组合性，还吃上下文。2026 年 9 月，同一个人改口说：我们相信，影响一件事的最好方式是拥抱它。

Pi社区反对了这么久的MCP，最后靠这个codemode才悄悄把mcp给请了回来。MCP果真有这么不堪吗？

**这不是打脸故事。真正被换掉的东西，比 MCP 本身更底层。**

## 一、问题是真的：Copilot 先撞的墙

先看这事儿有多大。

### 同一个模型，两样命

2025 年 8 月，开源项目 Cline 报了一个 issue。

经 Copilot 用 Claude Sonnet 4，窗口只有 128k，别处是 1M。

后果是频繁 condensing（自动压缩）、代码生成延迟。

2025 年 10 月，GitHub 官方 MCP server 一接上，token 从 34k 涨到 80k。

用户实测发现，竟然有66 个工具。

### 73%，第一条消息就触发压缩

到 2026 年，Copilot CLI 上系统提示加工具定义占掉 146k/200k。上来就是73%！第一条消息就可以触发自动压缩上下文！

![同一个模型在 Copilot 里只剩 128k 窗口；官方 MCP server 一接上，token 从 34k 涨到 80k（图源：cline/cline issue #5740、github/github-mcp-server issue #1286）](02-copilot-context.png)

2025 年 11 月，GitHub 官方博客承认：VS Code Copilot 能经 MCP 访问数百个工具。

其实一年多以前，我曾经深受Copilot智障的影响却不明所以。因为同样的Claude Sonnet模型，在其他工具里面用愣是效果比Copilot里面好不少。

后来才发现微软给的上下文窗口本身就很小，而Github官方的工具就要一次性占掉大量的上下文，导致干不了多少活，就会触发自动压缩了。偏偏微软还很“贴心”地把压缩行为给隐藏了起来。

那时候很多任务干一半就戛然而止的情况是屡见不鲜，让人觉得麻烦不已。没有人觉得agent可以变得非常有用，然而这才是一两年前的事情而已。

最大的 MCP 厂商之一当时自己承认，自己动手：砍工具数量，上 embedding 路由，核心只留 13 个。同时，pi却选了另一条路。

## 二、骂 MCP 的人，和拒绝 MCP 的人，进了同一家公司

2025 年 11 月，pi 的作者 Mario Zechner 写了篇文章。标题就是个问句：《What if you don't need MCP?》

pi.dev 上明晃晃挂着一句：Pi does not support MCP。

当时我就好奇，对MCP的支持究竟会走到一个什么样的地步？他们会把MCP重新加回来吗？

2026 年 4 月 8 日，Armin 创立的 Earendil 收购了 pi，Mario 加入。骂 MCP 的人，和拒绝 MCP 的人，坐进了同一家公司。

![pi 与 MCP 关系的四站时间线：2025-07 批评、2025-11 拒绝、2026-04 收购、2026-09 请回（图源：mariozechner.at、earendil.com）](03-timeline.png)

2026 年 9 月 29 日，Earendil 发文《"You Said No MCP!"》：MCP 进核心。Hacker News 上 672 点、360 条评论。

逆转的理由说得很直白：MCP 需要的和 pi 需要的是同一个东西——一个能折腾的解释器沙箱。

他们也承认，MCP 至今仍不好组合。但那是服务器和各家 harness 的问题，不是协议的。

## 三、codemode：让 AI 在沙箱里写代码调工具

### 大脑和手，不是一回事

codemode 的出发点是一组区分：harness 是大脑，受信任；执行环境是手，不一定。

bash 只能组合“能跑的程序”。可 read、view_image、subagent 根本不是程序，得由 harness 按协议注入。

这就好比是一个非常聪明的经理，去指导新来乍到但是有一些工作经验的老手。

交代任务的时候只需要给一个略微模糊的要求，和可以使用的资源，老手便能通过自己已有的经验去尝试探索和完成往往就能达到不错的效果。

反之，如果这名经理都事无巨细地交代所有步骤，他自己的宝贵的精力会很快耗费殆尽而效果未必就会更好。

### 沙箱里没有后门

codemode 的做法：让模型写一段 JavaScript，在沙箱里编排工具调用。沙箱无网络、无文件系统、无定时器，唯一出口是调工具。

这不是限制太多，是信任边界画得清楚：代码碰不到机器，只能碰工具。

中间结果由脚本自己消费，模型只看最终输出。同一个工具的大结果，走 bash 模型只看到尾部 2000 行，走 codemode 最多 1 MiB。

MCP 工具连上来有四档可选：直接声明、按需搜索、只许脚本调用、隐藏。不再只有全量灌进上下文一种姿势。

![MCP 工具的四档暴露：直接声明、按需搜索、只许脚本调用、隐藏（图源：pi 官方文档 mcp.md）](04-exposure-tiers.png)

脚本里的每次工具调用，仍要过 pi 的权限闸门。codemode 不是法外之地。

![大脑与手：harness 受信任，沙箱无网络、无文件系统、无定时器，唯一出口是工具（图源：lucumr.pocoo.org/2026/10/6/codemode）](01-brains-vs-hands.png)

## 四、这么能打的设计，作者为什么默认关着？

但 codemode 默认不开。pi 只在 MCP 开启时自动启用它。

作者在技术社区 Lobsters 亲口解释：跨模型 benchmark 不够。codemode 本身在 system prompt 里很占地方，小模型会过度使用它。

![默认关的三个理由：benchmark 不够、占 system prompt、小模型过度使用（图源：lobste.rs 作者回复）](05-default-off.png)

他还说，pi的做法，是benchmark “Badly”。现在很多判断是 “vibes based and looking at user reports”。

同时明确拒绝为特定模型打补丁。

那么，pi作者说的所谓的vibed bias，又是什么意思呢。

vibes based 直译就是凭感觉：证据不足的时候，看用户报告，压小赌注。那么是否可以说，在模型快速迭代的今天，即便是开源agent harness标杆的pi，也是在靠感觉来做优化，是吗？这样真的就靠谱吗？

默认关不是保守。方向对，但收益不确定、成本确定，那就赌小一点。代价也照实说：错过优化，回归发现慢。

pi 的兜底是把压缩前的原文留在会话树里，随时能回看。

作者承认的未解问题也有：脚本中途失败要整体重跑。这条线系列里拆解过——[Pi Durable：工具调用中途崩溃，重发还是放弃？](https://mp.weixin.qq.com/s/_gnfMHGfYW5yxtm6UJkfxg)

## 五、换掉的不是 MCP，是那个默认值

所以回到开头那个问题：pi 骂的从来不是 MCP，是“把工具声明全量灌进上下文”这个默认值。

codemode 不是投降，是给 MCP 换了一个不烧上下文的载体：中间结果由脚本消费，模型只看终点。

而它默认关着，因为作者自己清楚：方向对，赌注要小。

**真正被换掉的，是“工具定义全量灌进上下文”这个默认值。判断一个技术该不该骂，先看是谁的默认值。**

但是这个问题的核心，就是期望解决日益增长的context需求，和模型有限的context window大小之间的矛盾，以及很麻烦的注意力退化问题，对吗？

工具定义、工具结果、会话历史，都在抢同一块有限的地皮。codemode 是抢地皮的一种姿势。而上下文“撞车”——两条信息互相打架——还没人治。[Context Rot 是真的吗？上下文还没满，模型为什么就先认输了](https://mp.weixin.qq.com/s/6bdNSe1hiGFUvL1qV_ICUw)

![工具定义、工具结果、会话历史，都在抢同一块有限的上下文地皮（示意图）](06-context-land-grab.png)

至于 Anthropic 和 Codex 怎么接招，有空再写吧。

觉得这篇把 codemode 的来龙去脉讲清楚了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，AI 原理和工程，慢慢拆。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[微软用 Go 重写 TypeScript，他一个人用 C++ 又写了一遍](https://mp.weixin.qq.com/s/GmPJAh8ERPkm64KzYirV2g)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[Pi Durable：工具调用中途崩溃，重发还是放弃？](https://mp.weixin.qq.com/s/_gnfMHGfYW5yxtm6UJkfxg)  
[Context Rot 是真的吗？上下文还没满，模型为什么就先认输了](https://mp.weixin.qq.com/s/6bdNSe1hiGFUvL1qV_ICUw)

**参考资料与数字溯源**

1. Armin Ronacher《Tools: Code Is All You Need》，lucumr.pocoo.org，2025-07-03
2. Mario Zechner《What if you don't need MCP?》，mariozechner.at，2025-11-02
3. Earendil《"You Said No MCP!"》，earendil.com，2026-09-29
4. Armin Ronacher《What is Codemode》，lucumr.pocoo.org，2026-10-06
5. Hacker News 讨论（672 点 / 360 条评论），news.ycombinator.com/item?id=49906637，2026-09-30
6. cline/cline issue #5740：Copilot 内 Claude Sonnet 4 窗口 128k，2025-08-21
7. github/github-mcp-server issue #1286：加官方 MCP 后 34k→80k tokens，2025-10-23
8. github/copilot-cli issue #3539：System/Tools 占 146k/200k（73%），2026-05-27
9. GitHub Blog《How we're making GitHub Copilot smarter with fewer tools》，2025-11-19
10. pi 官方文档 codemode.md / mcp.md（本机 @earendil-works/pi-coding-agent 1.3.0），2026-10 核

#MCP #codemode #上下文工程 #AIAgent工程 #数解AI
