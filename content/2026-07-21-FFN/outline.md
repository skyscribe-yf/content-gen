---
title: "Attention都够了，为什么还要FFN？"
publishDate: "2026-07-21"
series: "Transformer 拆解"
---

# Attention都够了，为什么还要FFN？

## 写作承诺

用一个可运行的 2 维 SwiGLU 实验，回答 Transformer 层里注意力之后那一步到底做了什么。主线始终是：注意力先把上下文写进 token；前馈网络（FFN）再让每个 token 用同一套参数独立加工这份表示。全文不把 FFN 说成“记忆库”的确定结论，也不把模型配置外推成因果证据。

## 7 节结构：读者问题、证据与配图

| 节 | 标题与要回答的问题 | 关键证据／推导 | 配图位置 |
| --- | --- | --- | --- |
| 1 | **Attention都够了，为什么还要FFN？** 读者会问：Attention 已经汇入上下文，为什么还需要一个不再让 token 交流的 FFN？ | 先抛出“FFN 不交流却常占更多参数和计算”的冲突；用两三句前情说明注意力已把上下文写进 token，再用“圆桌交流后，每个人回到自己的思考室”建立分工。 | 紧接冲突段放 `01-roundtable-thinking-room.png`。封面 `00-cover-ffn.png` 用于文章头图，文字钩子为“不交流，最费算力？”。 |
| 2 | **注意力负责互相看，FFN 负责各自想** 读者会问：独立计算为什么不等于脱离上下文？ | 设 token 表示为 X。注意力的一个输出会由多个 token 的 K、V 加权而来，因此能跨 token 传递信息；进入 FFN 的 xᵢ 已带上下文。FFN 对每一行应用同一个 f，输出 yᵢ＝f(xᵢ)，没有 token 间混合。强调“共享参数”不等于“相互影响”。 | 沿用图 1：圆桌上的连线表示注意力，独立思考室表示逐 token 的 FFN。 |
| 3 | **一次 FFN 为何要先扩张、再开门、再投影？** 读者会问：中间维度变大和 SwiGLU 门控各有什么用？ | 给出与实验一致的 SwiGLU：gate＝SiLU(xW_gate)，up＝xW_up，hidden＝gate ⊙ up，y＝hiddenW_down。解释 expand：把 d_model 扩到 d_ff，提供更多可组合的特征方向；gate：按输入调节哪些特征通过；project：投回 d_model，才能与残差相加。避免宣称某一维对应某个确定语义。 | 讲完四步放 `02-swiglu-pipeline.png`。 |
| 4 | **两枚 token 会不会在 FFN 里偷偷互相影响？** 读者会问：怎样验证独立计算不等于脱离上下文？ | 运行 `experiment.py`：输入 X＝[[1.000, −0.500], [0.200, 1.000]]，得到 Y＝[[0.694, 0.154], [−0.042, 0.357]]。代码逐行重算与批量矩阵计算完全相等；分别扰动任一 token 后，另一 token 输出保持不变。结论只适用于这层 FFN：它不跨 token 混合，前后的注意力仍可带来上下文依赖。 | 在实验输出表之后放 `03-fixed-matrix-experiment.png`。 |
| 5 | **真实国产模型的一条旁注** 读者会问：这套结构只是教学玩具吗？ | 以 DeepSeek-V4-Pro 固定版本的 HuggingFace `config.json` 为可复查证据，只保留 `hidden_size: 7168` 与 `hidden_act: "silu"`：它们分别说明 token 主表示宽度和激活函数设置，不外推完整前向图或能力因果。 | 此节不单设图，避免把配置截图误画成未核验的精确架构。 |
| 6 | **Dense FFN 怎样长成 MoE？** 读者会问：前馈网络和 DeepSeek 的 MoE 是两套东西吗？ | 建桥：Dense FFN 是每个 token 都走同一个 expand→gate→project；MoE 是路由器为 token 选少数专家 FFN，再汇总输出。共性是“专家内部仍是 FFN”，差异是“是否选择专家”。链接既有 MoE 文，读者可在其中继续看真实模型如何组织 FFN。 | 结尾过渡处放 `04-transformer-preview.png`：从单一 FFN 分叉到受路由器选择的多个专家 FFN。 |
| 7 | **FFN 输出怎么安全回到 Transformer？** 读者会问：变换后的向量为何不会把原信息覆盖掉？ | FFN 输出通过残差连接与输入相加，归一化帮助数值尺度稳定；残差连接已有 2026-07-09 的系列文章可回读。这里仅预告归一化，或作为 Transformer 系列的下一站，不展开 Pre-Norm／Post-Norm 的公式和训练细节；收束为“交流 → 独立思考 → 保留原话并整理尺度”。用开放问题：你更想下一篇先拆归一化，还是回看残差连接？ | 使用图 4 的右侧 Transformer block 预览，文末不增加独立关注图。 |

## 文章节奏与事实核查清单

- 开头 200 字内给出反直觉冲突和“独立不等于没有上下文”的答案，不把论文标题当作技术事实的完整表述。
- 第 3、4 节严格复用 `experiment.py` 的 SiLU、矩阵、符号与输出；所有公式使用 Unicode，不使用 LaTex 分隔符。
- 第 5 节只保留已从官方 HuggingFace `config.json` 复核的 `hidden_size` 和 `hidden_act`，不补充 MoE 路由字段。
- 第 6 节回引已有 MoE 文章时使用已写入其 frontmatter 的微信 URL，不使用相对路径或推测 URL。
- 摘要含“前馈网络、SwiGLU、Transformer”三个关键词；结尾含价值承诺、系列导航与一个开放式留言问题。
