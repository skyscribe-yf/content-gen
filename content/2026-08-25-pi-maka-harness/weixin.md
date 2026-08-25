---
title: "Pi 的新架构，答案早就在数据库论文里了"
keywords: ["Pi", "harness", "数据库", "Maka", "Agent"]
series: Agent前线
wechatUrl: "https://mp.weixin.qq.com/s/QB_nJbrDU0G2vipZk8m1YQ"
subtitle: ""
---

Pi 的 harness v2 文档出来后，Maka 内部群大家直接愣住了。

因为它和我们在 Maka 里做的架构几乎一致。

Maka 的核心作者很多都是 database 背景出身的。两条完全不同的路径，最后设计出几乎一样的架构，这事本身就很能说明问题。

共同的主链路是这样：

持久化事实 → 派生运行状态 → 派生模型上下文 → 派生 UI → 崩溃后重新归约。

连 tool 的边界都一样：先写执行意图，再做副作用，再写结果。

Pi 是 tool_started_intent → execute → tool-result entry。

Maka 是 T1 toolDispatch → execute → T2 function_response。

其实就是 OS 和 db 那一套——预写日志、事件溯源、可恢复的持久化操作。

所以工程没有银弹。当我们最后做了很多工作之后，发现核心原理还是软件工程的那些内容。

人也很关键。Pi 的作者 Mario Zechner，奥地利人，做 libGDX 那个。2025 年底折腾了个极简 coding agent，两晚写出来，本来只给自己用。默认就四个工具：read、write、edit、bash，提示词压得很短，其他全靠你自己加。

口号写得很直：There are many agent harnesses, but this one is yours.

后来被 Earendil 收了，Mario 入股，发文标题就叫 I've sold out，核心继续开源。bio 写着 Old man yelling at Clauses，讨厌 Agent 越做越重、提示词越写越长。自己测过 MCP 和 CLI，结论和很多人实际感受一样：CLI 往往更省、更稳。

所以 Pi 长成现在这样，不是产品经理推出来的功能清单，是一个老开源作者按自己脾气做的壳。

你手头的 harness 敢断电重启吗？评论区交流交流呗

#Pi #harness #Agent #数解AI
