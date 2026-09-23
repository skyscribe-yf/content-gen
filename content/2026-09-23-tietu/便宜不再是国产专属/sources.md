# 价格与说法来源（2026-09-23 核对）

单位除非另注，均为每百万 token。人民币折美元按 7.2，只为横比，不是结算价。

## 海外

- Claude Opus 5.5：https://www.anthropic.com/claude-opus-5-5 （2026-09-22）
  - 输入 $4、输出 $20、缓存读取 $0.20、缓存写入 $5
  - 相对 Opus 5（$5 / $25 / 缓存读 $0.50）牌价 −20%，缓存读 −60%
  - 官方：默认设置、典型负载成本 −40%；输出快 30% 以上
  - Fast 模式 $8 / $40，最高约 2.5 倍速
  - 网络安全类请求大多路由到 Opus 4.8
  - Sonnet 5.5、Haiku 5.5：随后几周
- GPT-6 Sol / Luna：https://openai.com/index/introducing-gpt-6-sol-and-luna/ （2026-09-22）
  - Sol $2 / $10，Luna $0.10 / $0.50
  - 对比基线是 GPT-5.6 促销价：Sol $4 / $20，Luna $0.20 / $1.20
  - 官方标题写 50%。Luna 输出 1.20→0.50，实际约 −58%
  - Astra 仍为 $10 / $50（9 月 3 日已发布）
- API 价目（含缓存、长上下文）：https://platform.openai.com/docs/pricing.md （2026-09-22）
  - Sol 短上下文：输入 $2、缓存 $0.20、缓存写入 $2.50、输出 $10
  - Luna：输入 $0.10、缓存 $0.01、输出 $0.50
  - 输入超过 272K，整单输入 2 倍、输出 1.5 倍
- OpenAI 自家 AutomationBench 1.0.6：Sol xhigh 33.2%，$0.27/任务；Opus 5 max 成本 11.1 倍。表中没有 Opus 5.5。不要和 Anthropic 页上 Zapier 的另一套 AutomationBench 分数混画。

## 国产

- DeepSeek：https://api-docs.deepseek.com/quick_start/pricing （页面 2026-09-19 仍为现行价）
  - Flash 闲时：未命中 $0.15、命中 $0.003、输出 $0.60；忙时翻倍
  - V4 Pro 0813 闲时：未命中 $0.66、命中 $0.022、输出 $1.98；忙时翻倍
  - 忙时：工作日 01:00–04:00 与 06:00–10:00 UTC
- 智谱：https://docs.bigmodel.cn/cn/guide/start/pricing
  - GLM-5.3：¥8 / ¥28，缓存命中 ¥2
  - GLM-5.3-Flash：¥0.8 / ¥2.8，缓存命中 ¥0.23
- Kimi：https://platform.kimi.com/docs/pricing/chat-k3
  - kimi-k3：缓存未命中 ¥20、命中 ¥2、输出 ¥100；5 分钟缓存写入 ¥20
- 通义国内刊例：https://help.aliyun.com/zh/model-studio/qwen3-7-max （华北2）
  - Qwen3.7-Max：输入 ¥12、输出 ¥36、缓存命中 ¥2.4
  - 图上用刊例价，不把 5–6 月的限时折扣当成现价

## X

- Aaron Levie，2026-09-22：单任务成本、agent 的杰文斯悖论。https://x.com/levie/status/2102477253070430322
- 同日也有帖把 Sol 说成「量化版 Astra，降价大于升级」。这是说法，不是官方规格。
