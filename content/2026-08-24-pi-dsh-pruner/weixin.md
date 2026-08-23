---
title: "Pi这波把DSH剪枝骂惨了"
keywords: ["Pi", "DSH", "DeepSeek Harness", "harness"]
series: Agent前线
wechatUrl: ""
subtitle: ""
---

Pi把 DeepSeek Harness 的剪枝骂成 permanently-lossy，删了就找不回来。

这评价真不客气。

官方笔记里直接写：strictly better than dsh's permanently-lossy pruner。

他们盯的已经不是谁多几个 Tool、谁的 Demo 更炫。

一个 Agent 连续跑 50 个小时，它还知道自己到底干过什么吗？

DSH 的做法是 tool result 太长就留头留尾、中间裁掉。

3 万字日志，真正的报错卡在第 12000 个字符，一压就没了，后面模型再聪明也读不回来。

Pi 那边是 prune + spill，Context 里只留一小段，完整结果落到磁盘，模型要用自己 grep 回去。

拿 GLM-5.3 和 DeepSeek V4 Flash 跑了 19 个真实 Session，Context 占用降 26%～35%，uncached prefill 降 72%～88%，信息还能恢复。

更离谱的是 Claude。

新一代 Claude 塞进第三方 Harness，有时候反而更容易把 Tool 调错，自己生成 requireUnique、matchCase 这种 Pi 根本没有的参数。

一个很合理的猜测是，后训练越来越适配 Claude Code 自己的 Schema。

模型越强，和自家 Harness 绑得越死。

Claude + Claude Code、DeepSeek + DSH、GPT + Codex，以后单独看模型可能越来越没意义。

话说回来，Cordis 那套 Effect / Coeffect 看起来很干净，卸载还能 undo。

但现阶段大多数 Agent 还不需要 0 downtime，为这抛出 88 页论文，确实有点过了。

Harness 这东西，开始越来越像 AI 时代的操作系统了。

你现在还信「一切皆插件」，还是觉得该先管住状态？评论区交流交流呗

#Pi #DeepSeek #harness #DSH #数解AI
