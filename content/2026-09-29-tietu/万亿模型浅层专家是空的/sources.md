# 万亿模型，浅层专家是空的 · 数字来源

核对日：2026-09-29。图上数字来自 turboderp 的帖和截图、Hugging Face 的 config 与 safetensors 计数。不采用他没点名的「六个 Qwen」。X 互动数会变，不进图。

## 帖

- 主帖：https://x.com/turboderp_/status/2104702394718150834
- 时间：2026-09-28 22:38:49 UTC，北京时间 9 月 29 日 06:38
- 查看时公开计数约 308 赞、94 收藏、2.0 万浏览。只用来判断这条在被讨论，不进图
- 量化入口：https://x.com/turboderp_/status/2104855465280569661 （9 月 29 日 08:47 UTC）
- 830B 那句：https://x.com/turboderp_/status/2104903528502153309 （9 月 29 日 11:58 UTC）
- HongyeJin 回复：https://x.com/serendip410/status/2104837350912299386

主帖原句：去掉第 1–12 层的 expert blocks，再去掉第 1–4、6、8–11 层的 attention blocks，端到端 KLD 基本不受影响；这些块对残差的贡献在 BF16 舍入误差这个量级。可以剪掉约 1T 参数的 17%，模型大体还是同一个。That's six whole Qwens.

9 月 29 日补的原句：不是模型有问题，也不是在质疑榜单。它大约只用了 83% 的权重。需要长上下文评测才能完全确认。含义是可以从约 1000B 收到约 830B。

量化原句：给 Pro 做量化时撞上的，在 MOPD 更新之前。前 13 层在 1.5 bpw 的量化误差是 0。Flash 也许没有这个问题，他还没跑完。会复跑 Pro-MOPD，当时卡在磁盘。

HongyeJin 原句：Good point! That's also what we suspected before. Will have a new discussion about this soon. 他没有在这条帖里确认机制就是 v2.5 的静默专家死亡。那一层连接是回复里别人提的，不进图当结论。

## 他的两张图

贡献图标题：MiMo-V2.6-Pro-RL: what each early layer adds to the residual stream。副题：Reference model on wikitext, layers 0 to 24 of 70。

图上的文字标注，不是从曲线估出来的 y 值：

- layers 7 and 12: attention does real work
- MLPs join in from layer 17
- 空心点图例：zero (underflows fp16), drawn at the axis floor
- 阴影：global attention layers

图上不抄对数轴上的具体高度。第 5 层注意力他留下了，但图上没有单独的文字标注，所以图 1 只写「删除列表里没有这一层」。

对照表从帖内截图读出，读了两遍一致。没有 CSV。完整模型一列，KL 和 agreement 他没填。

| 项 | 剪过 | Noise floor | 完整 |
| --- | --- | --- | --- |
| Perplexity | 1.595870 | 1.594923 | 1.595245 |
| KL div vs full, mean | 0.006378 | 0.005079 | — |
| KL div vs full, median | 0.000385 | 0.000273 | — |
| Label in top 1 | 0.8384 | 0.8385 | 0.8391 |
| Label in top 5 | 0.9814 | 0.9817 | 0.9816 |
| Agreement vs full, top 1 | 0.9769 | 0.9792 | — |
| Agreement vs full, top 2 | 0.8812 | 0.8929 | — |
| Agreement vs full, top 3 | 0.7517 | 0.7754 | — |

子集表：

| 子集 | token | 剪过 | 完整 | 差 |
| --- | --- | --- | --- | --- |
| All | 137,708 | 1.5959 | 1.5952 | +0.0007 |
| Reasoning prompts | 79,136 | 1.6219 | 1.6212 | +0.0007 |
| Tools defined | 18,394 | 1.3802 | 1.3784 | +0.0018 |
| Ending in a tool call | 11,292 | 1.3424 | 1.3406 | +0.0018 |
| Everything else | 40,178 | 1.6520 | 1.6522 | −0.0002 |
| English | 71,373 | 1.6394 | 1.6397 | −0.0003 |
| Chinese | 53,198 | 1.5439 | 1.5420 | +0.0019 |
| Other languages | 13,137 | 1.5768 | 1.5767 | +0.0001 |

算出的、图上标明的差：

- 1.595870 − 1.595245 = 0.000625。子集表把同一对数字收成 1.5959 / 1.5952，差写成 0.0007。两套都在图上，不混成一个数。
- 0.006378 / 0.000385 = 16.6。他没写这个倍数。
- 0.7754 − 0.7517 = 0.0237。他没写这个差。
- 0.8391 − 0.8384 = 0.0007。
- 语言三行：71,373 + 53,198 + 13,137 = 137,708。
- 任务四行：79,136 + 18,394 + 11,292 + 40,178 = 149,000。不是全部的切分。
- 1000 × 0.83 = 830。这是他那句的口算，不是文件计数减法。

Noise floor 怎么造的，帖子正文没有。图上只保留列名。

## 参数账

config：https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL/raw/main/config.json
2026-09-29 读取。

- num_hidden_layers = 70
- moe_layer_freq：第 0 层是 0，第 1–69 层是 1。第 1–12 层都是 MoE
- n_routed_experts = 384，n_shared_experts = null，moe_intermediate_size = 2048，hidden_size = 6144
- 注意力：128 个 Q 头，8 个 KV 头，QK head_dim 192，V head_dim 128。attention_bias = false
- hybrid_layer_pattern 里第 0、7 层是全局注意力。模型卡写 70 层里 10 层全局、60 层滑动窗口

每层专家：

384 × 3 × 6144 × 2048 = 14,495,514,624

12 层：173,946,175,488 = 1,739.46 亿。图上写 1,739.5 亿，也写精确整数。

Hugging Face API：https://huggingface.co/api/models/XiaomiMiMo/MiMo-V2.6-Pro-RL
safetensors.total = 1,024,216,603,392。分项 BF16 10,647,286,656、F32 26,496、F8_E4M3 13,378,781,184、U8 1,000,190,509,056。U8 恰好等于 69 × 14,495,514,624，所以这一项按参数个数计，不是按打包字节计。

173,946,175,488 / 1,024,216,603,392 = 16.98%。他写 17%。图上用 16.98%，旁边写他写成 17%。

剩下：1,024,216,603,392 − 173,946,175,488 = 850,270,427,904 = 8,502.7 亿 = 0.8503 万亿。

模型卡写的是 1.02 万亿总参数、42B 激活。那是另一个分母，图 3 写明了。

9 层注意力的 QKVO：

每层 6144×(128×192) + 6144×(8×192) + 6144×(8×128) + (128×128)×6144 = 267,386,880
9 层 = 2,406,481,920 = 24.06 亿。图上写 24.1 亿。层归一化没算。不进 16.98%。

「六个 Qwen」不进图。1,739.5 亿不是某一档公开 Qwen 参数量的整数倍，他也没点名。

## 不进图

- 互动数
- 从对数轴上读出来的贡献比例
- Flash MOPD「没有这个问题」。那是回复里的判断，他自己没确认
- v2.5 静默专家死亡的机制等同。只保留 HongyeJin 的原句
- MOPD 复跑结果。他还没跑
