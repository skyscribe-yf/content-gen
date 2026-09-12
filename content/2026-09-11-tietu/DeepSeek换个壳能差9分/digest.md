# DeepSeek 换个壳能差 9 分

> 素材：DeepSeek-V4.1-Flash 技术报告 §5.1.2 / Table 4 / 结论 + X 上对 model–harness 共训的讨论（非个人账单）

## 手敲文本（digest）

V4.1 技术报告一出来，大家盯架构、盯 KV cache。

我盯的是另一段。

同一只模型，换个 harness，DeepSWE 能从 65.5 打到 74.2。差 9 分。

Terminal-Bench 2.1 从 84.1 到 90.6。

更刺的是：DSH 带 26 个工具的 Standard，还没几乎只给 bash 的 Minimal 高。

工具越多，不一定越能打，有时候只是更会乱摸。

他们自己说了，后训练没发明新算法。配方还是 SFT、RL、蒸馏。

新的是把 Claude Code、OpenCode、Pi、DSH 几种模式，一起丢进 RL 里训。不同壳上跑出来的 checkpoint，再 merge 回去。

官方头条 90.6 用的是 DSH Minimal，74.2 用的是 mini-SWE。

不是裸模型分。是模型和指定壳绑在一起的分。

结论里还有一句将来时：接下来要做 model–harness 共同设计，让整套系统一起进化。

现在只是模型去适应各种壳。真一起长，那是下一章。

所以以后别再问 V4.1 和 Opus 谁更强。

先问：你用的是哪只 harness。

你现在还在看模型榜，还是已经开始挑壳了？评论区交流交流呗

<a class="wx_topic_link" data-topic="1" style="color: #576b95;">#DeepSeek</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#harness</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#DSH</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#V4.1Flash</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#数解AI</a>
