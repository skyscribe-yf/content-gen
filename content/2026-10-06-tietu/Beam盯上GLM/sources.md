# 事实源

> 2026-10-06 贴图。数字核对自 Reflection 官方博客原文和文中原图。不把图上估读的点写成精确分数。

## 主来源

- 标题：Introducing Beam: Reflection’s 501B open-weight model
- URL：https://reflection.ai/blog/introducing-beam
- 原图：`src/bench.png`（算力横轴）、`src/efficiency.png`（token 横轴）、`src/rl.png`（rollout 横轴）
- 图头原文：Open-weight · 501B parameters · 23B active

## 可写事实

| 项 | 事实 | 出处 |
|---|---|---|
| 是什么 | Reflection 第一只开源权重模型。稀疏 MoE，总参 501B，激活 23B。面向编码、推理、agent | 正文首段 |
| 预训练 | 23.8 万亿 token。另有一处写预训练在 6144 张 GB300 上、不到 4 周 | 正文 |
| 对标 | 编码和 agent 上，称可与更大的 GLM 5.2 竞争，并在追 Qwen 3.8-Max。原始能力上，Kimi K3 仍在前面。Beam 的卖点是推理时更省 | 正文 “Model Capability” |
| 算力 | 高级推理基准上，称分数与 GLM-5.2 相当，推理算力少 3 到 4 倍。对 2T+ 的 Qwen 3.8-Max，差距更明显 | 正文 |
| 图上能看的 | 黑线 Beam，橙点 GLM-5.2，蓝点 Qwen3.8。Beam 挤在算力轴 / token 轴左边，GLM 在更右边。Qwen 蓝点在多张图上更高、也更靠右。这张图没有 Kimi | `src/bench.png`、`src/efficiency.png` 图例 |
| 算力口径 | FLOPs ≈ 2 × 激活参数 × 平均生成 token。生成 token 含推理和最终答案。不含 prefill、注意力随上下文的变化、服务开销。是估算，不是实测账单。别人的分数来自 Artificial Analysis 和 DataCurve | Figure 2 说明 |
| RL | 1.05 万张 GB300，4 周，超过 1 亿次 rollout，上下文最长 256K。沙箱约 13 亿次。环境约 100 万个。图上这条曲线用了其中约 8000 万次，到 8000 万仍在涨。对比：Inkling 3000 万次，MiMo 75.3 万次 | 正文 + Figure 3 说明 |
| 权重 | 还在最后的红队和评测。Apache 2.0，本月晚些时候才放权重、技术报告、模型卡。现在只能排队早鸟 | 正文开头和结尾 |

## 口径边界

- 「少 3 到 4 倍」是他们的说法，不是第三方复测。大约相当于只用 GLM-5.2 的四分之一到三分之一，正文可以这么翻译，但要带「号称」。
- 不把图上估读的百分比写成精确分。不说 Beam 分数超过 GLM 或 Kimi。
- 这张效率图没有 Kimi。Kimi K3 仍领先，只来自正文那一句。
- 不写「我跑过」。权重还没放。
- 预训练的 6144 张卡，和 RL 的 1.05 万张卡，不要混成一次。
