# 原始素材（话题：DeepSeek Harness 自己人开撕）

> 素材源：`/home/skyscribe/图片/贴图`（2026-08-24 06:03–06:13）
> 类型：贴图（图片消息），非长文

## 素材

### 图 1（截图 2026-08-24 06-04-58.png → 01-cui-liked.png）

Yifan Xu（@yifanxu_ephai）2026-08-23 15:20 UTC：
「崔老师给我点赞了，还有谁觉得我是dsh的黑子？」
截图显示 Tianyi Cui 和另外 100 人点赞了其 14 小时前的炮轰帖。

### 图 2（截图 2026-08-24 06-04-37.png → 02-yifan-rant.png）

Yifan Xu 原文（2026-08-23 07:47 UTC，约 7.4 万浏览 / 239 赞）：
- DSH 没什么真正的原创创新
- Tianyi 团队对 harness / build a better agent 理解相当一般
- 工具设计一眼从 Claude 搬几个、从 Codex 搬几个凑出来
- 社区把 UI design 当成 harness = 彻头彻尾的反向 harness
- DSH agentic 能力远低于平均水平，却谈「自进化」和 AGI

引用 Ruiteng Huang：dsh 最早期 commit 受 cordis 思想和架构影响，可从 git 历史核实。

### 图 3（deepseek-harness-system → 03-dsh-architecture.jpg）

架构图《DeepSeek Harness：给 Agent Loop 插上完整能力》：
- Cordis Context 提供服务插座
- Agent Loop 调度五个必需槽位：ctx.agents / ctx.sessions / ctx.llm / ctx.tools / ctx.systemPrompt
- 缺任一核心服务 → Agent Loop 不激活
- 完整 Harness = 五个核心服务就绪 + 入口 + 至少一个可用模型 Provider

## 事实核对（2026-08-24）

- DeepSeek Harness（dsh）2026-08-13 以 MIT 开源，v0.1 Developer Preview
- 团队负责人崔添翼（Tianyi Cui，@tianyi），2026-03 加入 DeepSeek
- 内核是 Cordis 插件框架，「Everything is a plugin」
- 2026-08-20 发 rc.8，补多模态，并接入 Claude Code / Codex 子代理
- Yifan Xu 炮轰帖 + 崔添翼点赞发生在 2026-08-23
