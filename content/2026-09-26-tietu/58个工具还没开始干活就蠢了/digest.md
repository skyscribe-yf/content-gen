# 58 个工具，还没开始干活就蠢了

> 2026-09-26 贴图草稿。拟 9 月 26 日发。未发布。数字见同目录 `sources.md`。图：`01.png` `02.png` `03.png`。

## 手敲文本

工具越多，Agent 越蠢。不是模型突然变笨。是开场就把工具说明书全塞进上下文。

Anthropic 2025 年 11 月 24 日给过一张账单。GitHub 35 个工具大约 2.6 万 token，Slack 11 个大约 2.1 万，再加 Sentry、Grafana、Splunk。58 个工具，大约 5.5 万 token。活还没开始干。Jira 再加一台，大约又是 1.7 万。他们自己见过工具定义吃掉 13.4 万。

更糟的是选错。名字像 notification-send-user 和 notification-send-channel，就爱拿错。同一套大工具库，开了 Tool Search，Opus 4 从 49% 到 74%，Opus 4.5 从 79.5% 到 88.1%。这是他们当时的内部 MCP 评测，不是今年的公开榜。

修法很土。先只加载搜索本身，大约 500 token。用到再拿 3 到 5 个，大约 3 千。他们另有一组 50 个以上的 MCP 工具：传统开场大约 7.7 万 token，搜完大约 8.7 千，少 85%。按那组例子，200K 窗口剩下的上下文是 19.1 万对 12.3 万。不要和前面 58 个工具那张账单混成一次测量。

Claude Code 现在默认就是这套。文档写得很直：一次塞进 30 到 50 个以上，选工具准确率就掉。一次搜索默认最多加载 5 个。工具少于大约 10 个，全加载往往更快。

Codex 更晚才把默认改过来。2026 年 6 月 22 日那次合并写明：以前要开开关，或者堆到至少 100 个，才藏到 tool_search 后面。现在模型和接口支持的话，MCP 工具默认全藏。模型先看见搜索，搜到了，下一轮才拿到 schema，再调用。

OpenAI 9 月 10 日的 Agents API 把同一件事写成产品：按需加载，省 token，搜到的定义贴在上下文末尾，好保住前面的缓存。别读成接上就自动全藏。Agents API 默认仍是全加载，要自己打开 tool_search。单个函数藏不干净，名字和说明还在，藏的主要是参数。要省，收成命名空间或 MCP，一个空间别超过 10 个函数。gpt-5.4 及以后才支持。

接上一个工具，和让模型看见它，是两步。你现在的 Agent，开场看见几个？

<a class="wx_topic_link" data-topic="1" style="color: #576b95;">#Agent</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#MCP</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#工具调用</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#上下文</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#数解AI</a>
