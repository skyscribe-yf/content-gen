# 原始素材（话题：GLM-5.3-Flash 揭晓与大模型价格战）

> 素材来源：作者提供的 9 张 X/社交平台截图（`/home/skyscribe/图片/贴图/0827/pic1~pic9`，2026-08-27 凌晨收集）。
> 截图已复制到本目录：`pic1` ~ `pic9`（jpg）。

## 素材（逐张截图内容要点）

| 图 | 来源 | 内容 |
|----|------|------|
| pic1 | SemiAnalysis @SemiAnalysis_ | Ox Alpha 已揭晓为 GLM-5.3-Flash；每日 100T tokens 处理量由中国芯片提供。OpenRouter 24 小时请求量榜 #1（23.2K 请求，第二名 DeepSeek V4 Flash 约 9.8K） |
| pic2 | Da7em @Da7Tech | GLM-5.3-Flash 之前 ZCode 缓存命中率约 98%，现在降到 78.4%，限额消耗更快——基础设施在负载下挣扎？ |
| pic3 | Sebastian Raschka @rasbt | GLM-5.3-Flash 架构：3:1 混合注意力（34 层 KDA + 11 层 MLA/DSA）、MoE 从 744B-A40B 缩到 320B-A18B、DeepSeek V4 风格 mHC 残差路径（4 并行流）、原生视觉编码器 |
| pic4 | 架构图 | GLM-5.3-Flash (320B-A18B)：1M 上下文、153k 词表、每 token 激活 18B（5.6%）、2 共享+8 专家 |
| pic5 | Arena.ai | Qwen3.8-Flash-Next：Code Arena WebDev 排名 #8、1617 分（AutoEval），开源权重模型约 #3 |
| pic6 | Cinq @WhosCinq | 「从无限使用到这个 :(」套餐配额对比：Grok 4.6=169、GPT 5.6 Luna=2,050、GLM-5.3-Flash 2x=3,160、MiniMax M3=3,200、Qwen3.7 Plus=4,300 |
| pic7 | OpenCode @opcode | GLM-5.3-Flash（前 Ox Alpha）上线 OpenCode Go，限时双倍用量（40 万查看）；Cinq 引用吐槽 |
| pic8 | Zixuan Li @ZixuanLi_ | GLM-5.3-Flash 官方 Z.ai API 50% 折扣两周：输入 $0.075、输出 $0.25、缓存输入 $0.015，第三方聚合商同样适用；价格对比图（vs GLM-4.5 / Claude Sonnet 4 / GPT-4.5 Turbo / Qwen3.5-Flash） |
| pic9 | Lumina @LuminaBench | Qwen3.8 Flash 每 token 只激活 6B 参数，却击败 Qwen3.8 27B 全部基准；8/14 项基准击败 397B Qwen3.7 Plus（6B vs 17B 激活）；采用 Qwen 4 架构 |

## 补充信息（可选）

- 发布日期：2026-08-27
- 目标读者：关注大模型 API 价格与国产模型的开发者
- 想突出的重点：Ox Alpha 真身揭晓 + GLM-5.3-Flash 半价/双倍用量开打价格战 + Qwen 同日跟进
- 不想写的：无
