# 大纲：C++ 与 AI 共存——CppCon 双演讲的工程答卷（软件工程系列第 3 篇）

Date: 2026-11-21
Slug: cpp-ai-coexistence
发布目标: 2026-11-30 20:00（每 2 天 1 篇纪律；11-28 后第一个双日档，队列无占用无冲突；已登记 schedule：drafting）

## 定位

- **矩阵位置**：支柱⑥ K 组「圈外工程大事件」事件轨 + H 组「圈外化」验轨（矩阵 §五明写的待验题：Agent 轨需要一个绑到圈外大事件的题）；**软件工程系列第 3 篇**（frontmatter `series: "软件工程"`，前两篇 2026-10-18 诊断篇 / 2026-10-20 落地篇聊 AI Native SDLC）
- **赢面（作者 grill 定，H 组口径）**：吃搜一搜长尾（标题/摘要埋「C++ × AI × CppCon」）+ C++ 圈微信群转发；推荐流低是预期内，不按推荐流 KPI 自评
- **受众**：C++ 程序员（作者明确选择，否决「写给 AI 圈」）。全新读者独立可读；系列连续性只走 frontmatter + 内链，正文零系列导航、零篇名引用
- **题眼**：对 AI 最不友好的语言之一，反而最先摸出了与 AI 共存的完整活法——四审查员制（攻）× 封装优先（守）× 标准层暗线（语言正在为 AI 改自己）
- **承重出处**（research brief 第二三四节为单一事实源）：AI++ 201 课程页 cppcon.org/class-2026-ai201（五大挑战 + strategies 逐字，HTTP 200，检索日 2026-11-21）；AI++ 101 页 cppcon.org/class-2026-AI101/（harness 金句 + Hagins 履历）；Daisy keynote 页 cppcon.org/2025-keynote-daisy-hollman（摘要直引）；Hagins 摘要金句经微软 VS C++ 博客交叉验证；四审查员原话 = workshop 预告视频转录（口径稿内注明）

## 结论（交付句）

**AI 没有降低对 C++ 工程师的要求，它把要求从「写」挪到了「审、架构、封装、判断」。** 四十年 C++、两次 AI winter 幸存的老手，把键盘整个交给 AI 之后的答案是：四个各带 persona 的专职审查 agent 加一个汇总 agent，小步快跑把编译器的反馈喂回 loop；而 Claude Code 团队的 WG21 老兵给出另一半答案——会困惑人的构造就会困惑 agent，封装和单测这些三十年前的老忠告，一条都没过时。同一时期，标准委员会在 contracts 上打的那场架，争的其实是同一个问题的语言层版本：AI 时代，什么才叫「可检查的意图」。

## 标题候选

- **T1（定稿，作者 grill 选定）**：「一年没写过一行代码的 C++ 老手，怎么保证代码不出事」——人物反差 + 疑问钩子；关键词 C++ 在 10-13 字自然出现；前 22 字窗口完整落反差；Hagins 原话「I haven't written a line of code since last November」直接撑标题；过 SEO 9 条自检（唯一短板：标题无「AI」二字，靠摘要 keywords 兜底）
- T2（备选，作者若想补 AI 关键词）：「一年没写过一行代码的 C++ 老手，怎么让 AI 保证代码不出事」——前 24 字出 AI，牺牲一点口语利落
- T3（备选，疑问后置式）：「C++ 老手把键盘交给 AI 一年，审查他交给了四个 agent」——信息量大但无问号、悬念弱于 T1
- 封面叠字（≤12 字、两行连读成句、主谓完整）：主候选「代码全交给 AI / 然后呢」（10 字，问句有画面）；备选「一行代码没写 / 质量怎么保」（12 字）

## 结构（篇幅豁免：作者 grill 原话「字数不用管」→ quality_check.json exempt「篇幅」，目标 2500 字上下，禁灌水；小标题=悬念链）

**开头（~180 字，事件场景钩子，AI 执笔不占原声槽）**：2026 年 9 月的 CppCon 2026，美国科罗拉多。一个四十年 C++ 老手上台，先交代一件事：去年 11 月之后，他一行业余代码没写过——不是不写，是每一行都出自 AI 之手。台下坐着的 C++ 程序员大概第一反应都是「扯吧」。问题直接摔出来：把键盘整个交给 AI 的人，怎么保证代码不出事？

### S1 先立人：AI 从访客变成了房间（~300 字）
- 是谁：LSEG/MayStreet，做高频交易基础设施（feed handlers、normalization、低延迟系统），四十年 C++
- 怀疑资格：1980 年代研究生阶段就做 AI（Lisp、Smalltalk、model-based reasoning），两次 AI winter 幸存者——他的怀疑是真的怀疑，结论是「工具终于追了上来，但只对那些愿意的人」
- 标题即论点（摘要直引）：「A year ago, AI was the visitor we were evaluating. Now, it is the room we work inside, and the question for C++ programmers is no longer whether to take the technology seriously but how to keep doing serious work in its presence.」
-  practitioner 口径（摘要直引）：「It is not a theoretical presentation, but a working practitioner's report.」
- 【原声槽 1】

### S2 C++ 简直是 AI 最不想碰的语言（~300 字）
- 五大挑战（AI++ 201 课程页逐字）：编译延迟打破快速迭代的反馈环；头文件/源文件分裂成两处、放大上下文需求；模板错误信息「读起来像加密勒索信」（encrypted ransom notes）；未定义行为能编译、能跑、但是错的；构建系统复杂度是又要穿越的一层
- 反直觉落点句（独立成段）：偏偏是对 AI 最不友好的语言，最先摸出了一套完整活法。
- 【原声槽 2】

### S3 他的答案：四个审查员，各看一遍（~450 字，核心节，可拆 2 个 ###）
- 原话（workshop 预告视频）：「I have code reviews done by four separate agents.」
- 四个审查员各带 persona、职责狭窄：常规审查员（提示词限定目录、输出 feedback.md、切断构建权限——「you do not have access to build tools. Do not build anything.」）；API Audrey；Nate，1970 年代贝尔实验室的 C 老手；安全关键老将，履历是 NASA、核电站、导弹发射井那一路
- 纪律一（原话）：「They shouldn't none of them should be tasked with reviewing everything. Their focus is very small and confined.」——小而封闭的焦点才能查深
- 纪律二：再加一个汇总 agent，四份审查汇成一份「改什么」；他甚至会让一个模型去分析四份审查之间的分歧
- persona 是廉价的控制手段（原话）：「Models behave differently when you give them personas.」——换身份不换模型
- 现场共识各一句支撑：Alexandrescu 的 slide 写着「stop using an agent」，全场惊讶于他把重音放在**单数**——他接着说要用多个；Muldoon：AI 让写代码变快，没让审查变快，一个没认真读就批的大 PR 只是把问题从「写」搬成了「审」
- 【原声槽 3】

### S4 小步快跑：把编译器的反馈喂回 loop（~300 字）
- strategies（AI++ 201 课程页逐字）：smaller changes；compile-after-every-change prompts；fast-compiling test files；showing both files（.h 和 .cpp 同时摆到 agent 眼前）；explicit instructions about what goes where
- 收尾金句（课程页原话）：「Every line comes from Claude Code. You prompt, you guide, you review, you course-correct, but your fingers don't type C++.」
- harness 一句（AI++ 101 宣传语）：「Not Claude Code. Not Cursor. A simple thing you fully understand.」——自己搭 harness，理解 loop 的每个零件，才知道在哪一环加控制
- 证据一句（课程页）：上一场 talk 里他完整搭出一个 OPRA feed handler，没手写一行代码
- 【原声槽 4】

### S5 Daisy 的守：会困惑人的，就会困惑 agent（~350 字）
- 是谁：Daisy Hollman，Anthropic Claude Code 团队成员，WG21 八年多（mdspan、executors、atomic_ref、ranges）
- 主论点（keynote 转录原话）：context window「is the input layer to the model」——C++ 程序员在 AI 之上做的大部分事情，本质是工程化这个输入层：喂什么、喂多少、什么时候压缩
- 老忠告新解释（转录原话）：「Even though C++ allows them, doesn't mean you should do them. You're going to confuse people. And if you're going to confuse people, you're going to confuse agents.」——她现场让模型做了一批 C++ 小问题，ADL 这类「同 token 难关联行为」的特性最常出错
- 封装是敢交给 agent 的前提（转录原话）：「Prioritize better encapsulation.」——封装良好、单测充分、不再人肉碰的模块，才是可以托付给 agent 的单元
- 落点句（独立成段）：她的 C++ 建议没有一条是新的。craftsmanship 没有过时，只是受众多了一个。
- 【原声槽 5】

### S6 暗线：同一时期，标准委员会在同一件事上打架（~350 字）
- 一句背景（不展开）：C++26 技术工作 2026-03-28 完成，contracts（pre/post/contract_assert）以 114:12:3 留在标准里；DIS 国际投票据报被否；11 月 Búzios 会议处理分歧——**只写到「分歧未决」，禁提任何裁决表述**（结局未核实）
- Sutter 的正面论点（BeCPP 2026 一页直答「AI 怎么影响语言设计」）：「Directly expressing intent helps AI (too)」——range-for、lambda、concepts、contracts，语言一直在演化成能直接表达意图的形态；签名上的 pre/post 让人、静态分析器、优化器、AI 都不必去推 body
- 反方一句（不展开）：Bjarne 阵营认为给不了保证的可选检查，救不了大规模 AI 生成代码的审查——投票数字、阵营论战、PACT/Fun2spec 全部不写，内链出去
- 工业界信号一句：Shopify 为让 AI agent 改主题页更顺，反过来把架构改成「人好读、显式契约、反馈清楚」——agents just want the same things as humans
- 【原声槽 6（方向 grill 已定：note 2 §5.4 判断①）】
- 内链：《60% 的赞成票，为什么救不了 C++26？》

### 收口（~200 字）
- 两场演讲拼起来是一句话：AI 没有降低对 C++ 工程师的要求，它把要求从「写」挪到了「审、架构、封装、判断」
- Dargo（CppCon 2026 现场综述原话）：「accepting the machine's diff feels like signing someone else's work.」——签别人的名之前，你得看得懂
- 【原声槽 7】
- 【原声槽 8：结尾互动问】

**尾部**：🔥 热门文章区（`scripts/hot_articles.py --md --cited content/2026-11-30-cpp-ai-coexistence/weixin.md` 生成，禁手写，行间不留空行、行尾两空格）+ 内链 4-5 篇（取 brief 第五节：11-02 contracts 篇必选 / 微软 Go 重写 TS 他用 C++ 写一遍 / Anthropic 多智能体之争 / Rust 192 任务 / AI Native SDLC 交付篇，全部微信 URL）+ 话题标签 3-5 个（#软件工程 #CppCon #AI编程 #数解AI 方向）

## 配图

- **封面**：`make_cover.py`——AI 无字底图（明快严肃风格：浅色中性底 + 低饱和 + 强对比，prompt 禁文字）+ PIL 叠金色发光字「代码全交给 AI，然后呢」两行；跑 `check_cover.py`，放大文字区逐字验底部笔画
- **图 1（AI 概念图，禁承载数字）**：S3 四审查员工作流——四个 persona 框（常规/API Audrey/贝尔实验室 Nate/安全老将）并行指向一个汇总 agent，再指向「改什么」清单；每个审查员配一句话职责
- **图 2（AI 概念图，禁承载数字）**：S2 C++ 五大不友好清单式信息图（编译延迟/头源分裂/模板错误像勒索信/UB 能跑但错/构建系统），纯文字图标排布
- **图 3（AI 概念图，可选）**：S5 上下文工程示意——context window 像一张桌子，「喂什么、喂多少、什么时候压」三个动作；不画则不补

## 检查清单（既有 + 本篇定制）

- [ ] `docs/article-quality-check.md` 19 项全过；成稿跑本篇 `quality_check.py`（定制项：原声/术语/内链/豁免）
- [ ] 段落 300-600 字（2026-11-15 项目级新规）；小于 300 字不分段；醒目句独立成段；`##` 节 ≥5（S1-S6 + 收口）；超 400 字节补 `###`；开头禁标题开场（第一段必须是钩子文本，禁 `##` 起首、禁把标题抄成第一行）
- [ ] **篇幅豁免**：quality_check.json `exempt` 加「篇幅」并放大 body_max/all_max；禁以豁免为由扩写结构、重复铺垫
- [ ] 新术语 ≤2：persona（给模型一个具体身份）、agentic loop（模型自己调工具、看结果、再决定的循环）；context window 用人话「模型的输入层」带过不算新术语；C++ 术语对目标读者是母语可正常用
- [ ] 承重数字/引文以 `.grill/cpp-ai-coexistence-research.md` 第二三四节为单一事实源；Búzios 禁提裁决；Hagins 演讲时段模糊为「CppCon 2026 一场演讲」；四审查员引文口径 = workshop 预告视频；114:12:3 只作一句背景；DIS 守「据报道」
- [ ] 撞车红线：contracts 只在 S6 一节；禁重述投票细节/阵营论战/PACT/Fun2spec/Lahiri/Intent-Formalization；11-02 篇内链必须出现在 S6
- [ ] 系列登记：frontmatter `series: "软件工程"`、`type: "实践篇"`（前两篇诊断/落地）；正文零系列导航、零篇名引用；digest 埋搜一搜关键词（C++/AI/CppCon/agent）
- [ ] 标题 T1 过 `docs/article-title-seo.md` 9 条自检；封面文字 ≤12 字且两行连读成句
- [ ] 原声 ≥5 进稿（终检门禁：≥5 逐字在场 + `【作者填入】`清零；第一轮质检 `--skip-voice` 不管）；原声句禁 ★ 前缀、禁 blockquote、按正文段落直排
- [ ] 结尾互动问 30 秒可答（质检 §16）；文末问题不禁系列导航
- [ ] 尾部热门文章 `hot_articles.py --md --cited` 生成 + `--self-check`；内链全部用微信 URL；话题标签 3-5 个
- [ ] 发布四步：`bash scripts/precheck_and_open.sh content/2026-11-30-cpp-ai-coexistence --skip-voice` → 作者 VS Code 改稿填原声 → `--no-open` 终检 → `baoyu-post-to-wechat`（grace+blue，remote-api）存草稿箱
- [ ] 档期 2026-11-30 20:00（每 2 天 1 篇纪律）；目录名 = 发布日期；发布后回填 frontmatter `wechatUrl`

## 作者原声槽

原声进稿：1 / 下限 5（槽 6 方向已由 grill 定：note 2 §5.4 判断①；其余待作者在 VS Code 填入，AI 禁代拟、禁代填、禁催稿）
填写方式：AI 写 `weixin.md` 时各槽位留 `【作者填入】` 占位符；作者在 outline 或 weixin.md 填均可，**以 weixin.md 为准**；可粘 grill 逐字原话或 vault 笔记逐字原话，算 1 处；可整槽标「跳过」；原声门禁在发布前终检把关（≥5 逐字在场 + 占位符清零，第一轮质检 `--skip-voice` 不管）。

### 槽 1 · 开头钩子之后
- 状态：待填
- 类型：判断/第一反应
- 位置：S1 段落（practitioner 口径引文）之后、S2 之前
- 为什么这里：读者（C++ 程序员）第一反应大概率是「扯吧」，这里需要你的第一反应给全文定调——你站哪边
- 问你一句：你读到「四十年 C++ 老手一年没写过一行代码」的第一反应是什么——「这不可能」还是「迟早的事」？
- 方向：判断（亲历作者已明示没有，禁编）
- 原句：【作者填入】

### 槽 2 · S2 五大不友好之后
- 状态：待填
- 类型：判断/吐槽
- 位置：「偏偏是对 AI 最不友好的语言，最先摸出了一套完整活法」之后
- 为什么这里：C++ 读者在这里最有表达欲，你的判断替他们把情绪说出来
- 问你一句：这五条（编译慢/头源分裂/模板错误像勒索信/UB 能跑但错/构建系统）里，你觉得哪条对 AI 最致命？哪条其实被高估了？
- 方向：判断/吐槽
- 原句：【作者填入】

### 槽 3 · S3 四审查员制之后
- 状态：待填
- 类型：判断
- 位置：「换身份不换模型」落点之后（或 Muldoon 一句之后）
- 为什么这里：全文最核心的方法论，需要你对「值不值」表态——四个 AI 审查员 vs 一个认真读代码的人
- 问你一句：如果只能选一边——四个各带 persona 的 AI 审查员，还是一个真正认真读代码的人——你信哪边？为什么？
- 方向：判断（可标「跳过」，作者 grill 未选此领域）
- 原句：【作者填入】

### 槽 4 · S4 小步快跑之后
- 状态：待填
- 类型：判断/类比
- 位置：「fingers don't type C++」金句之后
- 为什么这里：「小改动 + 每次编译」本质是反馈环工程学，读者容易在这里对照自己的活儿
- 问你一句：「把当时最快的反馈信号喂回 loop」这套思路，换到你自己熟悉的场景（不限于 C++）里，对应的最快反馈是什么？
- 方向：判断/类比
- 原句：【作者填入】

### 槽 5 · S5 老忠告之后
- 状态：待填
- 类型：判断
- 位置：「craftsmanship 没有过时，只是受众多了一个」之后
- 为什么这里：全文价值观落点，你的判断决定读者认不认这个账
- 问你一句：封装、单测、别写让人意外的构造——这些老忠告在 agent 时代是真增值了，还是只是换了个说法？
- 方向：判断（可标「跳过」）
- 原句：【作者填入】

### 槽 6 · S6 暗线（方向 grill 已定）
- 状态：待填
- 类型：判断
- 位置：Sutter「Directly expressing intent helps AI (too)」与 Bjarne 反驳一句之后、内链之前
- 为什么这里：暗线节的论点需要你自己的判断压舱——这是你笔记里现成的原生观点
- 问你一句：你笔记 §5.4 判断②的后半句（「当生产者（agent）数量级增长、审查者数量不变时，不能保证运行的检查＝不存在的检查」）——粘原文、或按你要的篇幅精简，均可，算 1 处
- 方向：判断（grill 已选定，来源 vault note 2 §5.4）
- 原句：【作者填入】

### 槽 7 · S6 之后或收口「签别人的名」之后
- 状态：待填
- 类型：判断
- 位置：S6 工业界信号（Shopify）之后，或收口段 Dargo 引言之后（二选一，以 weixin.md 实际位置为准）
- 为什么这里：「显式契约是 agent 的第一等公民接口」这个判断需要你的立场句
- 问你一句：语言设计该优先给「保证」（by-construction）还是「可写的检查」（可跳过）——AI 时代你站哪边？一句话就够
- 方向：判断（可标「跳过」）
- 原句：【作者填入】

### 槽 8 · 收口之后（互动问）
- 状态：待填
- 类型：互动问
- 位置：文末，回收题眼「怎么保证代码不出事」之后
- 为什么这里：质检 §16 要求 30 秒可答的问题；圈外化验轨靠评论区互动把 C++ 圈读者留下来
- 问你一句：换成你自己的话问出来——比如「你自己手上的代码，敢让 AI 写几成？哪部分永远自己写？」（方向：30 秒可答，钩读者自己的 workflow）
- 方向：互动问
- 原句：【作者填入】
