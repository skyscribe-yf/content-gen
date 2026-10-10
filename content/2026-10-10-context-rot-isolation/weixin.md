---
title: "Context Rot 是真的吗？上下文还没满，模型为什么就先认输了"
author: "数解AI"
date: "2026-10-10"
type: "工程观察"
series: "AI Agent 工程"
digest: "窗口远没用完，模型就先认输了。正方说 F1 掉 45.5%，反方说 15 万 token 内测不到退化。而子代理省下的不是时间，是它后面每一次的判断。关键词：Context Rot、长上下文、子代理。"
cover: "00-cover.png"
keywords: ["Context Rot", "长上下文", "子代理", "Agent 上下文隔离"]
---

跑了一夜的 agent 停在中途。

你翻它的上下文：窗口用了一半不到，工具调用记录正常，没有报错，也没有超限。但它的结论已经开始自相矛盾——同一个问题，它先给出 A，隔了十几步又给出 B。

**它没崩，也没满，它是先放弃了。**

这个问题，基本上所有模型都会出现，也就是大家经常调侃的大模型流口水现象。

所以懂行的朋友都知道一个会话不能复用太久，需要经常主动压缩上下文，或者fork重新开一个会话。

## 一、它没崩，也没超限——它是先放弃了

### 这不是感觉，是有人专门去测了

上海交大、上海人工智能实验室和 GAIR 合作的一篇论文，盯的就是 agent 长程搜索这件事。

论文编号是 arXiv:2606.29718。

四个开源旗舰模型：GLM-4.7、GLM-5.0、Qwen3.5-397B-A17B、MiniMax-M2.5。窗口都在 20 万 token 上下，Qwen3.5 是 25.6 万。

三百条轨迹，三个基准。

![三个数据集上，轨迹越长、放弃与不确定的比例越高（图源：arXiv:2606.29718）](02-length-vs-giveup.png)

结论一句话：

> **在上下文很长的时候，模型会在远未耗尽窗口之前，就给出放弃的、或者"不确定但其实错了"的答案。**

不是等到塞满了才变慢，是根本没塞满就不干了。

![模型会在上下文远未耗尽窗口之前就给出放弃或不确定的错误答案（图源：arXiv:2606.29718 图 1）](01-premature-termination.png)

### 论文里还有一处细节，比结论更刺人

他们**主动把闭源模型排除在外**——GPT-5.4 和 Claude Opus 4.7 都没进样本。

原因写得很直白：这些模型的推理过程是加密的，你无法分析它到底为什么失败。

也就是说，你花更多钱买的那个模型，恰恰是**你连它怎么坏的都看不见**的那个。

长任务偶尔"忽然就不对劲"，这不是错觉。

这条链路早就有人画出来了：[每步都靠猜，上百万Token的长任务怎么不跑偏](https://mp.weixin.qq.com/s/pbIQrUsChnNuFotkayFtiw)。

我觉得最麻烦的地方在于这个开始含糊不清，看起来像是降智不遵循指令的情况是什么时候开始发生的，完全没有办法实现界定，很多时候只能凭借感觉和经验来判定。

## 二、先说正方：一家做向量库的公司，比模型厂更早测出来

Context Rot（上下文腐化）这个词是怎么立住的？

最有意思的一点：**最早把实验甩出来的不是模型厂，是一家做向量检索的公司。**

### Chroma：加一个干扰项就掉分

Chroma 2025 年那份报告测了 **18 个模型**。

GPT-4.1、Claude 4、Gemini 2.5、Qwen3 都在内。

一共跑掉 **194,480 次调用**。

结论是：即使条件最简化，性能仍随输入变长而退化，而且退化方式**不均匀**。

更狠的两条：

- **加一个干扰项就掉分，加到四个继续叠加**；
- 针和问题**越不相似**，掉得越快。

![干扰项越多，性能掉得越多（图源：Chroma《Context Rot》，2025）](04-distractor-count.png)

![针与问题相似度越低，随长度退化越快（图源：Chroma《Context Rot》，2025）](05-needle-similarity.png)

### Anthropic：上下文是有限资源

之后模型厂自己下场。

Anthropic 2025 年 9 月的工程博客直接采用了这个词。

它给了一句很本质的定义：**上下文是有限资源，边际收益递减**。

模型有一份"注意力预算"，每多塞一段就是从这份预算里划走一块。

底层原因是 token 两两相关，n 个 token 就是 n² 条关系。

### 临界阈值：43.2%

硬数字这边，一篇 2026 年 1 月的论文（用的是 Qwen2.5-7B）给出一个临界阈值：**43.2%**。

五种方法交叉验证，区间 40%–50%，标准差 1.2%。

越过这个点，F1 从 **0.556 掉到 0.302——下降 45.5%**。

效应量 Cohen's d 高达 **8.2**。

这不是缓慢衰减，是断崖。

![Qwen2.5-7B 在阅读理解任务上的 F1：越过临界点后断崖式下滑（图源：arXiv:2601.15300）](03-critical-threshold-f1.png)

### 最有用的一条：不是垃圾太多，是内容太相关

今年 9 月有一份实测，把上下文分成**和任务无关的**、**和任务相关的**两类。

- 无关上下文：Claude Opus 5 几乎不掉，0.50 一直平到 1.25MB。GPT-5.6 Sol 从 0.31 掉到 0.24。
- 相关上下文：**两个都掉**。Opus 5 从 0.50 → 0.425（0.55MB）→ **0.398**（1.05MB）。Sol 从 0.347 → **0.26**。

所以不是"垃圾太多"，是**内容太相关**。

![相关上下文下，两个模型都掉；越接近真实工作负载，代价越明显（图源：Boolean《Context Rot Quantified》，2026-09-15）](07-related-drop.png)

这个区别很关键：你没法靠"只喂干净资料"躲开这件事。架构决策、未解决的 bug、半成品结论，全都是相关的，也全都在这份账上。

注意力预算这条线，前面写过三次。

从数学角度是[为什么AI上下文越长越慢？两道数学硬墙一次讲透](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q)；从架构角度是[智谱阿里为什么拆注意力？KV缓存砍4.4倍](https://mp.weixin.qq.com/s/5w1mEVLW5igvJ28Dn6pe9A)；想从最底层看起，可以回到[注意力机制是什么？别再当数据库查询](https://mp.weixin.qq.com/s/KrilwX6VRjI9KfjvD7C6kw)。

## 三、反方：15 万 token 以内，受控实验测不出来

到这里，故事该反转了。

今年 6 月有一篇预印本，标题就冲着这个议题来：《Is Context Rot Real?》。

它的方法比前面那些都严：**预注册**的固定针 / 增长干草堆因子设计，把上下文体量和针的位置交叉起来测，机械评分。

四个模型：gpt-5.5、gpt-5.4、gpt-5.4-mini、claude-sonnet-4-6。

结果是：

- 注册网格共 **12,570 次试验**；
- 其中 **7,330 条**"针确实存在"的试验里只失败 **48 次**；
- 准确率 **0.9935**，失败率的单侧 95% 上界是 **0.87%**；
- 上限拉到 **150,000 token**。

一句话：**在这些探针上，观测不到长度驱动的退化。**

![同样一组模型，在无关上下文里通过率几乎不降——反方所测正是这种情形（图源：Boolean《Context Rot Quantified》，2026-09-15）](06-unrelated-flat.png)

这一巴掌打得不轻。它等于说：你们前面测出来的，可能根本不是"长度"的问题。

## 四、两边测的不是同一个东西

那到底谁对？

那篇长程搜索论文里有一句话把这件事说穿了。

**现有的 Context Rot 研究大多聚焦单轮的长输入**——典型就是大海捞针。

而 agent 任务的上下文是**多轮的、多来源的、渐进累积**的。

所以：

- 反方测的是——一根针放在更长的干草堆里，还能不能找得到；
- 你的 agent 面对的是——这十几轮里的工具输出、报错、半成品结论，还会不会继续参与**后面每一次**判断。

**争议双方都没错，错的是把它当成同一个问题。**

你的现场，两种失败同时存在，而且长得不一样。

其实两个问题的后果都很严重，操作agent的人如果能有足够的背景知识来正确地判断具体是哪一种，然后有的放矢去应对更好。

如果是发生了上下文冲突导致模型陷入困顿，那么及时下达转舵指令，帮助模型获取清晰而又无歧义的上下文，比放任它去猜测和胡乱验证要好得多。

如果是因为太长导致上下文注意力涣散，那么及时fork或者是压缩上下文才是正解。

## 五、子代理省下的不是时间，是「参与权」

回到标题那半句：模型为什么会在窗口没用完之前就认输？

### 官方文档给了一条朴素到没人认真读的判据

Claude Code 的官方文档是这么说的：

**当一个子任务会"淹掉你的主对话"时，就把它扔给子代理。**子代理在它自己的上下文里做这件事，只把摘要交回来。

Anthropic 那篇多智能体工程复盘里，把这个动作叫 **intelligent filters**（智能过滤器）。

子代理负责过滤，主 agent 只拿结果。

他们还给了必须这么做的理由。

主 agent 的上下文一超过 **200,000 token** 就会被截断，所以它得先把计划存进 Memory。

### 隔离不便宜，账要照实算

同一篇里，Anthropic 承认 agent 本身就比普通对话多用约 **4 倍** token。

多智能体系统是 **15 倍**。

所以我要说的不是"隔离很便宜"——它不便宜。

**它省下的是"参与权"：那些你后面已经不需要的东西，不再有权参与你接下来的每一次判断。**

"参与权"是个自造词，但意思很实在：把上下文想成会议室，真正的成本不是屋里坐了多少人，是**这些人还有没有发言权**。

一个已经查完、结论拿走的搜索过程继续坐着发言，就是在稀释你对关键信息的注意力。

很多时候，我觉得无脑追逐超长上下文，然后对agent执行过程可能出现的大偏差弃之不顾的人，行为逻辑着实难以理解。

因为他们可能压根就不在乎他们的钱包，也很可能不在乎所浪费的时间，加上很多模型提供商对于超过一定长度的上下文之后，会加倍收费的定价策略，可能这些人也毫不在意吧。

是不是模型厂商就故意借口推理成本增加来收取高价格，然后给你提供的服务是打折扣的？自己需要多多判断吧。

### 定价也有一个看不见的悬崖

这个"加倍收费"不是错觉，我把价目表翻了一遍。

- **OpenAI** 官方价目表里，"短上下文"和"长上下文"是两组独立的列。同一个模型，长上下文档**输入价正好 2 倍**、输出价 1.5 倍。比如 gpt-6-sol，短档输入 $2 / 百万 token，长档 $4；输出 $10 对 $15。
- **Anthropic** 已经把这个加价**取消**了。官方定价页写着：Claude 4.6 及之后（Haiku 5.5 除外）以**标准价**提供完整 100 万上下文。只剩 Haiku 5.5 在超过 10 万 token 时仍适用长上下文价。
- **阿里云百炼**的阶梯计费更彻底。**不是超出的部分贵一点，而是这一次请求的所有 token 都按所落档位的单价结算**。差一个 token 越过临界线，整次请求改价。

所以性能有一个看不见的临界阈值（43.2%），计价也有一个看不见的临界阈值。

**两个悬崖，一个你测得到，一个要等账单。**

### 代价：它只回你一段没有过程的话

这一切有一个代价必须说清。

子代理只回你一段**没有过程的话**。它的失败不会报错，它会把"我猜的"写成"我查到的"。

这代价有多真实，我有过一回。

曾经有一次，我尝试让opencode去对一整天产生的巨量的代码变更做一次性审计，然后基于我那复杂的checklist来仔细审查，报告问题到github上面去。

结果还没有读取完所有的diff,上下文就超了，自动压缩的结果又是乏善可陈的，真的是赔了夫人又折兵。

这个案例值得停一下：它**同时**踩了两种病——内容太多直接读爆，压缩之后又救不回来。

相关前情三条：系列里的记忆篇是[给 Agent 装了记忆，为什么它还是不懂我的项目？](https://mp.weixin.qq.com/s/4z-PvTBKv8yBohgdE8-itQ)；长上下文在架构上的代价，[同样 1M 上下文，KV 缓存差 15 倍：四家架构差在哪一层](https://mp.weixin.qq.com/s/7BdQlueJrRJ5f-x3v_2VqA) 算过一笔。

而"多智能体到底该不该建"，系列里也早算过——[Anthropic 实测多智能体强 90%，为什么另一家说千万别建？](https://mp.weixin.qq.com/s/Y6aPD8t8h2-KCUseKXc0mQ)

## 六、两种药：先分清是「撞车」还是「涣散」

上面那个 opencode 的例子，真正的问题不是"没压缩"，是**下错了药**。

这两种病的药完全不一样：

- **撞车**（上下文互相冲突、模型陷入困顿）→ 及时下达**转舵指令**，把它拉回清晰而无歧义的上下文。放任它猜测、胡乱验证，只会越走越远。
- **涣散**（太长、注意力被摊薄）→ **fork** 或**压缩上下文**才是正解。

前提是操作的人得有足够背景知识，**先判断是哪一种**。

判错，就下错药。

### 压缩不是万灵药

Anthropic 自己承认，压缩最难的地方正是"留什么、丢什么"——**过度压缩会丢掉那些重要性后来才显现的细节**。

OpenAI 这边的态度更直接：他们专门写了压缩的 API 文档，把它做成了一等的服务端能力。

他们博客里给的定位是——**把压缩当作长跑的默认原语，而不是应急兜底。**

### 加密的压缩项，和看不见的损失

但有个细节很值得注意：服务端压缩返回回来的是一个**加密的压缩项**。

你看到它还在跑，**你看不到它丢掉了什么**。

这和第一节那件事是同一个病根。

闭源模型因为推理过程加密，连"它为什么失败"都分析不了；压缩项加密，连"它丢了什么"也看不见。

**压缩最大的风险不是压得狠，是它没有告诉你它丢掉了什么。**

### 压缩能力本身，也在选型范围内

这个问题其实还有更复杂的一面，是不同的agent的上下文压缩效果差异很多，比如codex就以极其优秀的上下文压缩能力著称，你可以放心地压缩三四次都不丢失太多智能。

而相对而言很多agent只要压缩一两次就显得不堪大用了。

说明一句：这个"三四次对一两次"是我自己的一线使用经验，没有公开实验支撑。

能站住的只有"压缩是一等能力"——OpenAI 官方把压缩当默认原语就是这个态度。

但结论仍然成立：**"直接压缩"不是通用解，长活交给谁，本身就是一道上下文压缩能力的选型题。**

Cognition 也说过同一件事的另一面。

跑得通的模式是"多个 agent 贡献智能，但**写入保持单线程**"。

### 两条判据

于是两条判据可以合起来用。

1. **任务侧——按参与度派活，不按长度。** 派子代理之前问一句：这份内容，我后面还要不要让它参与每一次判断？要，就留在主上下文（哪怕它很长，比如架构决策和未解决的 bug）；不要，就扔出去（哪怕它很短，比如一段日志）。
2. **故障侧——先分清撞车还是涣散。** 撞车就转舵，涣散就 fork 或压缩。

围绕"取舍"，前面写过四篇。

[信息熵：压缩1000倍，为什么信息反而少？](https://mp.weixin.qq.com/s/BkGWzKxiJE2mlPMlZgb7ag) 讲熵和压缩的关系；[上下文并行：1M序列为什么切了会坏？](https://mp.weixin.qq.com/s/UB_ILj-62K3VBUY4_AopSw) 讲切分时边界上的代价。

[稀疏注意力怎么挑重点？DeepSeek-V4 只算 1/64](https://mp.weixin.qq.com/s/QcZUcxYZUw27_J2ykESUHA) 讲模型自己在 token 之间怎么挑重点。

至于压到什么程度还算安全，可以看[KV缓存压到1bit：省92%显存，凭什么不掉点？](https://mp.weixin.qq.com/s/Oy-GyqEB8IP4_0nmvZ7EDQ)

回到开头那个跑了一夜的 agent。

它缺的不是更大的窗口，是一条**把它不再需要的东西挡在外面的边界**——以及一个能分辨"它到底是撞车了还是涣散了"的人。

自己根据实际的应用场景，编排和设计合理的分工场景，用好当下AI及其强大的一般推理能力，做好分治，就能从AI里面得到更多更好更快的结果。

而这样，就需要操作Agent的人时不时盯着它的轨迹看看有没有纠偏，所以从人们把agent比作是harness的情况来看，还真的是需要人类时刻把好缰绳，不能放手吗？

觉得这篇把 Context Rot 这笔账算清了，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，AI 原理和工程，慢慢拆。

📖 **[AI Agent 工程合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4680422529625325570#wechat_redirect)**：给 Agent 装了记忆，为什么它还是不懂我的项目？ → 多智能体路线之争 → Pi Durable：工具调用中途崩溃，重发还是放弃？

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[随机变量为什么不是变量？它其实是个函数](https://mp.weixin.qq.com/s/5BxjOUblW64DXNffHc2sxQ)  
[每步都靠猜，上百万Token的长任务怎么不跑偏](https://mp.weixin.qq.com/s/pbIQrUsChnNuFotkayFtiw)  
[为什么AI上下文越长越慢？两道数学硬墙一次讲透](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q)  
[智谱阿里为什么拆注意力？KV缓存砍4.4倍](https://mp.weixin.qq.com/s/5w1mEVLW5igvJ28Dn6pe9A)  
[给 Agent 装了记忆，为什么它还是不懂我的项目？](https://mp.weixin.qq.com/s/4z-PvTBKv8yBohgdE8-itQ)  
[同样 1M 上下文，KV 缓存差 15 倍：四家架构差在哪一层](https://mp.weixin.qq.com/s/7BdQlueJrRJ5f-x3v_2VqA)  
[信息熵：压缩1000倍，为什么信息反而少？](https://mp.weixin.qq.com/s/BkGWzKxiJE2mlPMlZgb7ag)  
[上下文并行：1M序列为什么切了会坏？](https://mp.weixin.qq.com/s/UB_ILj-62K3VBUY4_AopSw)  

**参考资料与数字溯源**

1. Xia, Wang, Huang, Liu《Diagnosing and Mitigating Context Rot in Long-horizon Search》，arXiv:2606.29718，2026，https://arxiv.org/abs/2606.29718 —— 四个开源旗舰模型 / 300 条轨迹 / 未耗尽窗口即放弃 / 排除闭源模型
2. Chroma Research《Context Rot: How Increasing Input Tokens Impacts LLM Performance》，2025，https://research.trychroma.com/context-rot —— 18 个模型 / 194,480 次调用 / 单干扰项即掉分 / 相似度越低退化越快
3. Anthropic《Effective context engineering for AI agents》，2025-09-29，https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents —— 上下文是有限资源 / attention budget / n² / compaction 取舍
4. Wang, Min, Zou《Intelligence Degradation in Long-Context LLMs》，arXiv:2601.15300，2026-01，https://arxiv.org/abs/2601.15300 —— 43.2% 临界阈值 / F1 下降 45.5% / Cohen's d=8.2
5. Boolean《Context Rot Quantified》，2026-09-15，https://www.boolean.ai/blog/context-rot-quantified —— 相关上下文 0.50→0.398、0.347→0.26；无关上下文几乎不掉
6. 《Is Context Rot Real? A Controlled, Cross-Provider Null…》，Zenodo 预印本，2026-06-18 —— 12,570 次试验 / 准确率 0.9935 / 失败率上界 0.87% / 上限 150,000 token
7. Claude Code 官方文档《Create custom subagents》，https://code.claude.com/docs/en/sub-agents —— 「在自己的上下文里做、只把摘要交回来」
8. Anthropic《How we built our multi-agent research system》，2025-06-13，https://www.anthropic.com/engineering/multi-agent-research-system —— 子代理是 intelligent filters / 200,000 token 截断 / 4 倍与 15 倍 token
9. OpenAI API 文档《Compaction》，https://developers.openai.com/api/docs/guides/compaction —— 保留后续轮次所需状态的压缩 / 服务端压缩 / 加密压缩项
10. OpenAI 博客《Shell + Skills + Compaction》，https://developers.openai.com/blog/skills-shell-tips —— 「把压缩当作长跑的默认原语，而不是应急兜底」
11. OpenAI 官方价目表，https://developers.openai.com/api/docs/pricing —— 短 / 长上下文两组独立列；输入 2 倍、输出 1.5 倍
12. Anthropic 官方定价页，https://platform.claude.com/docs/en/about-claude/pricing —— Claude 4.6 及之后（Haiku 5.5 除外）以标准价提供完整 100 万上下文
13. Cognition，Walden Yan《Multi-Agents: What's Actually Working》，2026-04-22，https://cognition.com/blog/multi-agents-working —— 多 agent 贡献智能、写入保持单线程

#ContextRot #长上下文 #AIAgent工程 #上下文工程 #数解AI
