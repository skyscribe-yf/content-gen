# 58 个工具，还没开始干活就蠢了 · 数字来源

核对日：2026-09-25。图上数字都来自下面三处原文，不采用营销号的「上下文废一半」「省 95%」这类没给分母的说法。第三方教程里的 73 工具 / 3.98 万 token 不进图。

## 账单和准确率：Anthropic 工程博客

- 2025-11-24，*Introducing advanced tool use on the Claude Developer Platform*
- https://www.anthropic.com/engineering/advanced-tool-use

五台服务的开场账单（博客原文，token 为大约值）：

| 服务 | 工具数 | token |
| --- | --- | --- |
| GitHub | 35 | ~26K |
| Slack | 11 | ~21K |
| Sentry | 5 | ~3K |
| Grafana | 5 | ~3K |
| Splunk | 2 | ~2K |
| 合计 | 58 | ~55K |

- 58 = 35+11+5+5+2，博客没把合计写出来，图上的「58 个」是算出的。55K 是五项大约值相加，博客写的是 “approximately 55K tokens before the conversation even starts”。
- Jira 单独大约 17K。再加服务器会很快到 100K+。
- Anthropic 内部见过工具定义在优化前吃掉 134K token。这是他们的观察，不是对照实验。
- 最常见的失败是选错工具、填错参数。例子：`notification-send-user` 对 `notification-send-channel`。

同一篇里的对照例子（50+ MCP 工具，和上面 58 个不是同一组，图上分开写）：

- 传统：工具定义预先全加载约 72K；开场总占用约 77K。
- Tool Search：搜索工具本身约 500 token；用到再加载 3–5 个相关工具，约 3K；开场总占用约 8.7K。
- 博客原话：token 用量减少 85%；相对传统做法，保留的上下文是 191,300 对 122,800。191,300 = 200,000 − 8,700，122,800 = 200,000 − 77,200，对得上，所以这组例子按 200K 窗口算。图上写「200K 窗口里剩下 19.1 万对 12.3 万」，19.1 万 / 12.3 万是 191,300 / 122,800 四舍五入。
- 内部 MCP 评测，大工具库：Opus 4 从 49% 到 74%；Opus 4.5 从 79.5% 到 88.1%。88.1 − 79.5 = 8.6 个点，图上这句是算出的。模型是当时的 Opus 4 / 4.5，不是 2026 年的现役模型。

适用边界（同一篇）：工具定义超过约 10K token、已经选错工具、多台 MCP、工具数 10 个以上，才划算。少于 10 个、每个会话都要用、定义很短，收益不大。搜索多一轮，延迟要自己扛。

## 现在的默认行为：Claude Code 文档

- https://code.claude.com/docs/en/agent-sdk/tool-search.md
- 核对日页面仍写：tool search 默认开启。定义先不进上下文，只给一份摘要，用到再搜。
- 一次搜索默认最多加载 5 个最相关的工具，之后留在上下文里，直到发现它们的那段消息被压缩。
- 选工具准确率在一次加载超过 30–50 个时下降。50 个工具可以占 1 万到 2 万 token。
- 少于大约 10 个、定义放得下时，全加载通常更快。
- 目录上限 10,000 个工具。
- `ENABLE_TOOL_SEARCH=auto` 才是「定义占到窗口 10% 再开启」。默认（不设这个变量）是直接开启，不是 10% 门槛。图上不写「超过 10% 才懒加载」。

## Codex 把默认改掉：2026-06-22

- https://github.com/openai/codex/pull/29486
- sayan-oai 合并，commit `c53b1da`，2026-06-22。
- 原文：以前只有开了功能开关，或者至少 100 个工具，MCP 工具才会躲到 `tool_search` 后面。
- 改完：模型和接口支持 tool search、以及 namespaced tools 时，有效 MCP 工具全部推迟加载。不支持时仍直接暴露，避免旧组合坏掉。
- 模型实际看见的顺序：第一轮只有 `tool_search`，搜到匹配工具，下一轮才拿到 schema，然后再调用。

## OpenAI 写成产品：2026-09-10

- Agents API 公告：https://openai.com/index/introducing-the-agents-api/
- 工具搜索文档：https://developers.openai.com/api/docs/guides/tools-tool-search
- 公告原话：tool search 按需加载相关工具定义，有助于降低 token 和费用，并保住模型缓存。
- 文档：新发现的工具插在上下文末尾，是为了不冲掉前面的缓存。Responses API 里只有 gpt-5.4 及以后支持 `tool_search`。
- 单个推迟加载的函数，模型开头仍看得到名字和说明，藏掉的主要是参数 schema。命名空间或 MCP 服务开头只露出名字和说明，里面的函数要搜了才展开。
- 文档建议一个命名空间少于 10 个函数。Agents API 默认仍是急切加载，要推迟必须自己加 `tool_search` 并给函数设 `defer_loading: true`。图上写了这条，避免读成「接上 MCP 就自动全藏」。

## 不进图

- 9 月 24 日营销帖里的「100 个工具吃掉一半上下文」没有测量。Codex 的 100 是旧门槛，不是实测消耗。
- OpenRouter 9 月 24 日上了带 tool search 的 Server Tools Marketplace，是产品上架，没有新数字。
- claudefa.st 2026-09-24 的 73 工具 / 39.8K / 5K 是教程举例，不是 Anthropic 或 OpenAI 的测量。
