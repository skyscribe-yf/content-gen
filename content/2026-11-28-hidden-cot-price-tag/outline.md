# 大纲：AI 把思维链藏起来，为什么反而收你 5 倍的钱

> 目录：`content/2026-11-28-hidden-cot-price-tag/`（发布日期变更时按规则重命名）
> 素材：`.grill/2026-11-28-hidden-cot-price-tag.md`（grill 日志）、`.grill/2026-11-28-hidden-cot-price-tag-research.md`（调研 brief 两轮，**单一事实源**）、`docs/series-plan-2026-11-latent-reasoning.md` §3.2/§6
> vault：`concepts/大模型原理/LatentReasoning-潜在推理研究全景.md` §9.6 厂商栈 / §9.7 五障碍 / §10.1 商业账 / §10.6 四因
> 系列：挂靠「Latent 思维链」，本篇为系列第 2 篇（共 4 篇）；**开头零系列导航**，系列互链走文末

## 一、定位

- 读者：调过 API、为 thinking/reasoning 付过钱的工程师；**默认「读思维链」是调试与监控手段**；不一定分得清「隐藏思维链」和「latent reasoning」，但一定在账单上见过思考的代价
- 认知目标：把「隐藏思维链更便宜」这个直觉纠过来——**token 照常生成、照常按输出计费，只是不返回给你**；并知道四家里只有一家在 API 文档里承诺思维链全量返回，另外三家是明确的设计选择，背后有五道坎
- 不是：光谱 ①–⑧ 与四条路线综述（L1 已覆盖，本篇只一句带过 + 内链指回）、监控替代方案清单（L3 的事）、循环扩展的是什么能力（L4 的事）、DeepSeek 为什么选择全量返回的动机推测（无一手依据，禁写）
- 轨道：文章轨（场景钩子 + 悬念链 + 官方文档原话举证 + 回扣开头）
- 基调：**先信，带限定**——四家可见粒度全部开到官方文档，可正面写；媒体报道类内容（Astra）带限定；国产负面发现如实写，不拔高

## 二、核心结论

**一句话**：你以为厂商把思维链藏起来是为了省成本——恰恰相反，**思考的 token 照常逐 token 生成、照常按输出计费，只是不再返回给你**；四家现役输出单价全是输入的 5 倍（DeepSeek 峰时 3–4 倍），一个难 query 能烧掉 1 万以上的隐藏思考 token，总成本翻 3–6 倍。**隐藏思维链在商业上是加价项，不是省钱项。**

**三层**：

1. **计费层（一手确认）**：Google 定价页每张模型卡标着「Output price (including thinking tokens)」，同页写明「Every token the model processes is counted and billed, including thinking tokens」——这是厂商自己写在定价页上的，不依赖任何推测。
2. **可见性层（四家官方文档夹击）**：OpenAI「we don't expose the raw reasoning tokens」、Anthropic「No `display` setting returns the raw chain of thought」、Google「By default, only the final output is returned」——三家都明确写不返回原始推理；只有 DeepSeek 写着「the chain-of-thought content is returned via the `reasoning_content` parameter」。
3. **为什么层（五道坎）**：CoT 监控是安全刚需、latent 隐蔽行为有实证威胁、工程代价、收益不确定、计费结构——第五条直接回扣第一层。

**落点（读者能带走的一问）**：如果你的工作流靠「读思维链」判断 agent 有没有跑偏——这件事，四家里只有一家还完整支持。

## 三、标题候选

| # | 标题 | 判断 |
|---|---|---|
| 1 | **AI 把思维链藏起来，为什么反而收你 5 倍的钱？** | 主选。反常识（藏=省钱的错觉被打破）+ 数字反差（5 倍）+ 为什么；核心关键词「思维链」在前 8 字自然出现；痛点（贵）普通读者与 API 用户都有；前 22 字内数字反差落在窗口内 |
| 2 | 四家旗舰只有一家给你看思维链，凭什么 | 备选。数字反差（四家/一家）+「思维链」关键词前置；但「凭什么」信息缺口弱于「为什么」，且无金额数字 |
| 3 | 你付的输出价里，有一部分买的正是「不给你看」 | 备选。反转陈述句，转发场景有劲；但非疑问句，推荐流点击率通常弱于反常识疑问 |

- **封面文字（≤12 字，脚本叠字，AI 底图须无字）**：`思维链藏起来更贵`（8 字，主谓完整；备选 `不给你看，反而更贵`）
- 硬规则：AI 只出无字浅色中性底图；封面文字 ≠ 标题一字不差；文字块 ≤25% 画面高、每行字高 ≥8%
- 术语约束：本篇新术语 ≤2（`reasoning_content`、hidden reasoning token），其余全人话化

## 四、开头（原声槽 1）

- AI 钩子（前两段，禁导航禁 `##` 开场）：为了弄清自己的 agent 到底烧多少 token，我把 202 次会话 compaction 翻了个底朝天——那笔账算的是「压缩省了多少」。但同一本账里漏了一半：**模型思考用的 token，我看不见，它却在计费**
- 一手措辞紧随（AI 写）：Google 定价页每张模型卡都标着「Output price (including thinking tokens)」，同页还有一句更直白的——「Every token the model processes is counted and billed, including thinking tokens」
- 原声槽 1（作者填）： compaction 审计里看到的真实数字 / 看到「思考也计费」时的第一反应
- 转折句（题眼，AI 写）：一笔漏算的账，和一张四家厂商的对比表——撞的是同一个东西：**「不给你看」从来不省钱，它只是个加价项**

## 五、结构（5 节，正文约 2000 字）

小标题连起来必须是一条完整故事链：漏算了一半账 → 四家只有一家返回 → 另外三家卡在五道坎 → 国产其实还没上桌 → 你依赖的监控通道只剩一家（回扣开头）。

### 1. 我审计了 202 次压缩的账，才发现漏算了一半（约 380 字，原声槽 1+2，配图 03）
- 功能：场景钩子 + 立 stakes（这本账我也算过一半）
- 要点：202 次会话 compaction 审计（已发 10-27 篇，数字可查证）；Google 定价页两句官方措辞逐字引；四家现役输出/输入倍率——OpenAI / Anthropic / Google 全部 **5×**，DeepSeek 峰时 **3×**（v4-pro）/ **4×**（flash）、谷时全项半价（峰时 = 周一至周五 UTC 01:00–04:00 与 06:00–10:00，中国法定节假日除外，周末整日谷时）；Google 带 2026-12-01 / 2027-01-01 两个调价时点；难 query 烧 1 万以上 hidden reasoning token → 总成本 3–6 倍（vault §10.1）
- 判断句：**隐藏思维链买的是「不给你看」，不是「更便宜」**
- 内链：《上下文压缩省了 77% token，为什么账单反而更贵？》（10-27，`https://mp.weixin.qq.com/s/p-2YkAFT6sBwdU5_dw5O2g`）——同一笔账的另一半
- 配图：03 一本账的结构（输入价 / 输出价 / 你看不见的思考 token 照常计费，AI 概念图，禁承载具体金额数字）

### 2. 四家里，只有一家把思考过程返回给你（约 400 字，配图 01，原声槽 3）
- 功能：全文承重墙，一张表 + 四句官方文档原话
- 四家（全部 2026-11-22 开官方文档核到关键句）：
  - **DeepSeek**（`api-docs.deepseek.com/guides/thinking_mode`）：「In thinking mode, the chain-of-thought content is returned via the **reasoning_content** parameter, at the same level as **content**」；thinking mode 默认开启、默认 effort=high；deepseek-v4-pro 与 deepseek-flash 均适用
  - **OpenAI**（`platform.openai.com/docs/guides/reasoning`）：「While we don't expose the raw reasoning tokens emitted by the model, you can view a summary of the model's reasoning using the `summary` parameter」——摘要需显式 opt-in，多轮只回传 encrypted reasoning tokens
  - **Anthropic**（`platform.claude.com/docs/en/build-with-claude/thinking`）：「**No `display` setting returns the raw chain of thought.**」；5.x 默认 `omitted`（thinking 字段为空，signature 只承载加密全量供多轮连续性），4.6 及更早默认 `summarized`
  - **Google**（`ai.google.dev/gemini-api/docs/thinking`）：「By default, only the final output is returned. You can enable thought summaries with `thinking_summaries`」；thought signature 是加密表征
- 判断句：不是「只有 DeepSeek 敢给你看」——**另外三家的官方文档都明确写了不返回原始推理**，这是设计选择，不是技术做不到
- o1 官方原话可逐字引（2024-09，openai.com/index/learning-to-reason-with-llms，已逐字核实）：「balancing user experience, competitive advantage, and the option to pursue the chain of thought monitoring, we have decided not to show the raw chains of thought to users」——注意这句里「保留 chain-of-thought 监控的选项」是被权衡掉的那一项
- 配图：01 四家可见性对比（AI 概念图，四列对比意象，标签脚本后加或仅图形）
- ⚠️ 禁写「与内部推理 token 逐字一致」（DeepSeek 未声明）；禁写「2026-09 起 API 以 thinking signature 代替原始思维链返回」（L1 的不准确说法：raw CoT 从未向 API 调用者返回，signature 是加密载体不是可读替代）；禁写 omitted 成为 5.x 默认的具体月份（文档未给切换日期）

### 3. 另外三家不是不上，是五道坎（约 420 字，配图 02，原声槽 4+5）
- 功能：回答「为什么」，五障碍逐条一段（vault §9.7）
  1. **CoT 监控是安全刚需**——Pachocki 2026-09-02 X 帖（TNW 2026-09-04 逐字转述）：「I want to prevent a race into unmonitorability kicked off by confused reporting.」；更早的一级锚点：2025-07 四十机构立场论文（arXiv:2507.11473，Pachocki 为共同作者）称 CoT monitorability 是「a new and fragile opportunity」
  2. **latent 隐蔽行为有实证威胁**——ICLR 2026 有输出对齐 / latent 携带不对齐的研究
  3. **工程代价**——looped 结构与流水线并行不兼容、KV 语义全新
  4. **收益不确定**——Raschka：Astra 的提升主要来自训练而非循环结构（一句带过，Astra 细节 L1 已讲，内链指回）
  5. **计费结构**——hidden token 按输出计费是收入来源（**回扣 §1**，全节的钉子）
- 判断句：五道坎里最实的那道不是技术，是第 5 条——**「不给你看」本身就是门生意**
- 内链：《机械臂蹭一下桶盖，成功率高10%：奖励函数才是AI钻空子的源头》（09-14，`https://mp.weixin.qq.com/s/boIPBlmyX2ahoFYnEVLjxw`）——监控通道收窄的另一面，是钻空子更难被发现
- 配图：02 五道坎（AI 概念图）
- 原声槽 4：五条里哪条是真坎、哪条你觉得是借口
- 原声槽 5：你会为「可见」换供应商吗

### 4. 国产阵营其实还没上桌（约 300 字，原声槽 6）
- 功能：诚实的负面发现 + 国产落点（吃 `docs/theory-practice.md`）
- 要点：DeepSeek-V4-Pro-0813 的 HF config.json 直读——61 层，**无** looped / latent / recurrent / depth / recursion 类参数；唯一邻接项是 MTP（`num_nextn_predict_layers=1`），训练期与投机解码用途，不是 test-time latent reasoning。GLM-5.2、Kimi K2.6 本轮直读同样干净；Qwen3.5 仓库 gated，没直读到（只能写「未直读、未发现」，不承重）
- 判断句：所以别以为国产已经在搞 latent reasoning 了——**目前只有 DeepSeek 一家在「可见性」上做了不同的选择**，而它选择的恰恰是「给你看」
- 唯一的前沿规模探索：腾讯 WeLM（2607.08186，80B/617B，n=4），官方博客定位研究与探索、未确认上线产品线
- ⚠️ 禁写「架构上绝无任何 latent 机制」（`dspark_*` 等非标参数功能未证，禁引申）；禁推测 DeepSeek 为什么选择全量返回
- 原声槽 6：WeLM 这种「研究博客、未上线」的国产进展，你会等它上线还是先看论文

### 5. 你依赖的那条监控通道，只剩一家还给（约 300 字，收口，原声槽 7+8）
- 功能：回扣开头 + 给读者带走的一问
- 要点：我审计 compaction 是为了知道 agent 烧了多少 token；但比 token 更关键的是——**定位跑偏时读的那个「过程」，四家里只有一家还完整返回**
- 一句带过 + 内链指回 L1：思维链的可见性其实是一条八档光谱，「不给你看」和「根本没有」是两种完全不同的东西（L1 拆过光谱与四条路线）
- 收口问句（AI 写）：如果你的工作流靠读思维链判断 agent 有没有跑偏，这件事从哪一档开始失效？
- ⚠️ **禁在文末或收口写「下一篇 / 接下来三篇」预告**（2026-11-07 废止红线）；系列连续性只靠文末互链
- 原声槽 7：收口问句的真实答案（你会为「可见」多付钱 / 换模型吗）
- 原声槽 8（备选）：有没有哪次你发现思维链和最终答案对不上

## 六、配图计划（3 张，均 AI 概念图轨道，不出数字）

| 文件 | 内容 | 轨道 |
|---|---|---|
| `01-vendor-visibility.png` | 四家「给不给你看思维链」对比：一家全量返回、三家明确不返回原始推理的对比意象 | AI 概念图（prompt 禁文字，标签脚本后加或图中仅图形） |
| `02-five-obstacles.png` | 五道坎：监控刚需 / 实证威胁 / 工程代价 / 收益不确定 / 计费结构 | AI 概念图 |
| `03-billing-structure.png` | 一本账的结构：输入价、输出价、你看不见的思考 token 照常生成照常计费，只在 API 返回处被拦掉 | AI 概念图（禁承载具体金额） |

## 七、内链清单（文内自然位置，禁堆文末）

1. L1《加入100个dummy token，算术能力飞涨10.7分》（11-22 今晚 20:00 发）——**（待发布）**，发布后第一时间回填 URL；本篇 §2/§5 各指回一次
2. 《上下文压缩省了 77% token，为什么账单反而更贵？》（10-27）`https://mp.weixin.qq.com/s/p-2YkAFT6sBwdU5_dw5O2g` —— §1 同一笔账的另一半
3. 《上下文压缩的极限：删掉一个 token，任务为什么可能注定失败？》（10-25）`https://mp.weixin.qq.com/s/XdAACdIWD2F6d8rq-ZszKg` —— §1 信息账（备用）
4. 《机械臂蹭一下桶盖，成功率高10%：奖励函数才是AI钻空子的源头》（09-14）`https://mp.weixin.qq.com/s/boIPBlmyX2ahoFYnEVLjxw` —— §3 监控通道收窄的另一面
5. 《1,250 篇论文之后：AI 自己练自己，为什么只有两条线敢上生产？》（11-12）`https://mp.weixin.qq.com/s/8O45vlW6bCqOlObyf2lF7Q` —— §4 测试时计算对照（备用）

（备选未用：《记忆诅咒》11-20 未发布，留给 L3）

## 八、作者原声槽（7+1 个候选，全部占位符；本篇走 AI 全权代填，作者 VS Code 终审逐槽确认）

计数：待填 8 / 已填 0 / 跳过 0。门禁：发布前终检 ≥5 逐字在场 + 占位符清零。
代填口径：只锚作者有据可查的真实工作流（10-27 篇 202 次 compaction 审计实数、DeepSeek 全量可见用户身份、prompt 调试日常、读思维链定位 agent 跑偏），禁编未经历的戏剧化事件，每槽 40–70 字。

**槽 1**（§1 开场）
- 位置：钩子之后、转折句之前
- 为什么这里：全文 stakes 立在这里——读者先确认「这本账我也算过」，后面五倍价才落得下来
- 问你一句：你审计那 202 次 compaction 时，算的是哪本账？看到「思考 token 也计费」这句时第一反应是什么？
- 方向：审计里看到的真实数字 + 一句反应，禁拔高成「机制发现」
- 原句：【作者填入】

**槽 2**（§1）
- 位置：「加价项」判断句之后
- 为什么这里：论断需要用户侧证据，否则只是复述定价页
- 问你一句：你有没有哪次账单是被 thinking / reasoning token 抬起来的？当时在跑什么？
- 方向：一个具体 query 类型 + 量级感受，一两句
- 原句：【作者填入】

**槽 3**（§2）
- 位置：四家对比讲完之后
- 为什么这里：承重墙需要作者评分，否则是文档摘录
- 问你一句：四家里你日常用哪几家？读不到思维链全文的时候，你靠什么判断它有没有跑偏？
- 方向：一个替代信号（输出质量 / 耗时 / 重试次数）举一个真实例子
- 原句：【作者填入】

**槽 4**（§3）
- 位置：五道坎讲完之后
- 为什么这里：五条障碍的轻重只有干过的人分得出来
- 问你一句：五条里你觉得哪条是真坎、哪条你觉得是借口？
- 方向：挑一条 + 一句理由，可以和槽 3 呼应
- 原句：【作者填入】

**槽 5**（§3）
- 位置：本节末尾（「不给你看本身就是门生意」之后）
- 为什么这里：这一句最扎心，需要用户侧回应才不显得泼冷水
- 问你一句：如果有供应商把「可见」当成卖点并据此加价，你会买吗？界限在哪？
- 方向：会 / 不会 + 一个条件
- 原句：【作者填入】

**槽 6**（§4）
- 位置：国产负面发现之后
- 为什么这里：负面结论需要作者判断托住，否则像在黑国产
- 问你一句：WeLM 这种「研究博客、未上线」的国产进展，你会等它上线再用，还是先看论文？
- 方向：一句判断 + 一个前提
- 原句：【作者填入】

**槽 7**（§5 收口）
- 位置：收口问句之前
- 为什么这里：收口问句的分量取决于这里有没有真东西
- 问你一句：如果「可见」只剩一家还给，你会为此选它吗？还是已经有别的信号替代了读思维链？
- 方向：会 / 不会 + 你实际在用什么替代
- 原句：【作者填入】

**槽 8**（§5 备选）
- 位置：faithfulness 相关处（如正文提及「思维链和最终答案对不上」）
- 为什么这里：这是 L3 监控篇的种子，本篇先埋
- 问你一句：有没有哪次你发现思维链和最终答案对不上？
- 方向：一次具体经历，没有就标「跳过」
- 原句：【作者填入】

## 九、既有检查清单（追加项）

- [ ] 作者原声槽已填且进稿 ≥5（终检把关，第一轮质检不管）
- [ ] 「四家唯一」口径正确：只能说「四家里只有 DeepSeek 在 API 文档里承诺思维链全量返回」，禁写「与内部推理完全一致」
- [ ] 未复用 L1 的不准确说法：禁写「2026-09 起 API 以 thinking signature 代替原始思维链返回」；Anthropic 禁写 omitted 成为 5.x 默认的具体月份
- [ ] Pachocki 引句：只用 TNW 逐字转述 + arXiv:2507.11473 立场论文兜底，禁写成 X 帖逐字原话
- [ ] Astra 只一句带过且带「媒体报道 + 部分承认」限定；o1 原话为 openai.com 已逐字核实版本
- [ ] 国产禁写「架构上绝无任何 latent 机制」；`dspark_*` 非标参数禁引申；Qwen3.5 只写「未直读」
- [ ] 价格均为 2026-11-22 检索日刊例；Google 带 2026-12-01 / 2027-01-01 调价时点；DeepSeek 带峰谷口径
- [ ] 与 L1 分工执行：光谱 / 四路线 / Astra 细节 / 定价表全貌 / Anthropic 反蒸馏 → 只一句带过 + 内链指回
- [ ] 开头无系列导航、无 `##` 开场、无标题抄写；文末无「下一篇」预告
- [ ] 封面 00-cover.png 存在且过 check_cover.py；图片无 `images/` 前缀
