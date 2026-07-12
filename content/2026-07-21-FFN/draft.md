---
title: "前馈网络怎么工作？注意力之后还要想一遍"
author: "数解AI"
type: "原理篇"
series: "大模型原理"
scheduledPublish: "2026-07-21T08:00:00+08:00"
digest: "前馈网络、SwiGLU、Transformer：注意力让 token 交流，FFN 再让每个 token 独立扩张、筛选和投影。用一个可运行实验验证：改动一个 token，不会穿过 FFN 改变另一个。"
keywords: ["前馈网络", "FFN", "SwiGLU"]
cover: 00-cover-ffn.png
---

## 🎯 驱动问题

![](00-cover-ffn.png)

Transformer 最著名的论文，名字叫《Attention Is All You Need》：**注意力就是全部所需。**

可你打开一个 Transformer block，会发现注意力后面还跟着一大块前馈网络（Feed-Forward Network，FFN）。它常常占去更多参数和计算。既然注意力都“够了”，这一步为什么没有被删掉？

答案藏在两种完全不同的工作里：注意力让 token **相互交换信息**；FFN 则让交换过信息的每一个 token，拿着同一套工具，**各自再想一遍**。

所以论文标题里的 “all”，不是说一个 block 里只剩注意力；它强调的是 Transformer 的主干不再依赖循环网络或卷积网络。标准 Transformer 仍把注意力子层和 FFN 子层并排保留，因为“交流”和“独立加工”解决的不是同一件事。

![](01-roundtable-thinking-room.png)

把一层 Transformer 想成一次工作流程：token 先围坐圆桌，在注意力里听取彼此的线索；散会后，它们回到一间间没有门的思考室。每个人都带着刚收到的上下文，用同样的设备处理自己的笔记。这间思考室，就是 FFN。

## 💡 注意力负责互相看，FFN 负责各自想

设一段文字进入这一层后的表示是矩阵 X。第 i 个 token 是其中一行 xᵢ。

注意力的关键在于：第 i 个输出会根据 xᵢ 与其他 token 的关系，对很多 token 的 Value 做加权汇总。于是“银行”在“河岸”和“贷款”两种上下文里，能从别的 token 那里拿到不同线索。**注意力有跨 token 的混合。**

FFN 的写法则很克制：

> **yᵢ ＝ f(xᵢ)**

同一个函数 f 会复用给每一行，但 yᵢ 的计算只读 xᵢ。第 1 个 token 不会在 FFN 内部读取第 2 个 token 的向量，也不会改写它的输出。它们**共享参数**，不等于它们在这一步**互相影响**。

这也澄清一个容易混淆的点：说 FFN “独立”并不是说它不知道上下文。进入 FFN 的 xᵢ，早已在上一小步的注意力中混入了上下文；FFN 只是不会在自己的计算里再开一次圆桌。

## 📐 一次 FFN：先扩张，再开门，再投影

现代大模型常用 SwiGLU 形式的 FFN。为了和后面的实验保持一致，先把它拆成四步：

> **gate ＝ SiLU(xW_gate)**
>
> **up ＝ xW_up**
>
> **hidden ＝ gate ⊙ up**
>
> **y ＝ hiddenW_down**

第一步和第二步都把 d_model 维的输入送往更宽的 d_ff 维空间。可以把它理解成：原来只有几条观察角度，现在临时展开出更多可组合的特征方向。这里的“更丰富”是容量上的描述，并不意味着某一维必然对应某个可命名的语义。

接着，SiLU 生成的 gate 像一排随输入而变的阀门。SiLU 不是只输出 0 或 1；它会连续地缩放每个方向。再把 gate 与 up 逐元素相乘，便得到“这次输入该让哪些扩张方向通过、通过多少”的结果。

最后，W_down 把较宽的 hidden 投影回 d_model 维。只有回到原来的宽度，FFN 的输出才方便与这一层原有的表示相加。

![](02-swiglu-pipeline.png)

一句话记忆：**扩张提供可选项，门控按输入筛选，投影把结果带回原尺寸。**

## 🔬 两枚 token 会在 FFN 里偷偷互相影响吗？

“每行独立”听起来像定义。我们不靠口头保证，直接用一个 2 维、固定权重的 SwiGLU 网络测一次。下面是本篇实际运行过的完整 `experiment.py`，没有省略任何计算：

```python
import numpy as np


def silu(z: np.ndarray) -> np.ndarray:
    return z / (1 + np.exp(-z))


# A SwiGLU feed-forward network (FFN) operates independently on each token.
# x has shape [tokens, d_model]; hidden has shape [tokens, d_ff].
x = np.array([[1.0, -0.5], [0.2, 1.0]])
w_gate = np.array([[1.0, -1.0, 0.5], [0.5, 1.0, -1.0]])
w_up = np.array([[0.8, 0.4, 1.2], [-0.3, 0.9, 0.2]])
w_down = np.array([[0.6, -0.2], [0.1, 0.7], [0.5, 0.3]])

gate = silu(x @ w_gate)
up = x @ w_up
hidden = gate * up
y = hidden @ w_down

for index, row in enumerate(x):
    standalone_y = (silu(row @ w_gate) * (row @ w_up)) @ w_down
    np.testing.assert_array_equal(y[index], standalone_y)

# Perturbing one token cannot change the FFN output for the other token.
perturbed_x0 = x.copy()
perturbed_x0[0] += np.array([0.3, -0.4])
perturbed_y0 = (silu(perturbed_x0 @ w_gate) * (perturbed_x0 @ w_up)) @ w_down
np.testing.assert_array_equal(perturbed_y0[1], y[1])

perturbed_x1 = x.copy()
perturbed_x1[1] += np.array([-0.4, 0.3])
perturbed_y1 = (silu(perturbed_x1 @ w_gate) * (perturbed_x1 @ w_up)) @ w_down
np.testing.assert_array_equal(perturbed_y1[0], y[0])

for name, value in (("x", x), ("gate", gate), ("up", up), ("hidden", hidden), ("y", y)):
    print(f"{name} = {np.array2string(value, precision=3, suppress_small=True, floatmode='fixed')}")
```

这次运行选取的实际输出如下：

```text
x = [[ 1.000 -0.500]
 [ 0.200  1.000]]
gate = [[ 0.509 -0.274  0.731]
 [ 0.468  0.552 -0.260]]
up = [[ 0.950 -0.050  1.100]
 [-0.140  0.980  0.440]]
hidden = [[ 0.484  0.014  0.804]
 [-0.065  0.541 -0.114]]
y = [[ 0.694  0.154]
 [-0.042  0.357]]
```

批量计算得到的 y 的两行，和把每一行单独送进同一组权重后得到的结果完全相等。更关键的是，代码又做了两次扰动：改动第 1 个 token 后，第 2 个输出逐元素完全不变；改动第 2 个 token 后，第 1 个输出也完全不变。

这些固定数值只是为了让计算可复现，不是模型从数据中学到的规律。真正有力的检查是“扰动一个输入，观察另一个输出”：在这个 FFN 内，没有任何跨行运算把变化传过去。

当然，结论的边界也要画清：它只证明这个 FFN 层不混合 token。若前面的注意力已经让两个 token 相互读取，xᵢ 本身仍会随上下文改变；后一层注意力也仍可能把信息再次传开。

![](03-fixed-matrix-experiment.png)

## 🌍 2026 年国产模型里的线索：从配置能知道什么？

教学用的 2 维矩阵很小，真实模型当然大得多。以 2026 年 [DeepSeek-V4-Pro 固定版本的 `config.json`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/raw/b5968e9190ef611bbf34a7229255be88a0e937c1/config.json) 为例，配置声明了相关字段：`hidden_size: 7168`、`hidden_act: "silu"`、`moe_intermediate_size: 3072`、`n_routed_experts: 384`、`n_shared_experts: 1`、`num_experts_per_tok: 6`。

这几项能支持哪些说法？`hidden_size` 给出 token 主表示的宽度；`hidden_act: "silu"` 是激活函数设置；其余字段是配置声明的 MoE 路由专家数、每个 token 选择的专家数、共享专家数和专家中间维度。它们说明真实工程同样需要处理 FFN 的宽度、激活与稀疏调度，只是容量和调度方式更复杂。

但请把证据边界卡在这里：**仅凭 config.json，不能证明哪些层实际使用 MoE，不能还原专家内部或完整前向计算图，也不能证明知识具体存在哪里，更不能推出某项能力由某个 FFN 字段造成。** 配置是声明，不是运行轨迹，更不是因果实验。

## 🔀 Dense FFN 怎样长成 MoE？

普通的 Dense FFN 很直接：每个 token 都经过同一个“扩张 → 门控 → 投影”模块。

MoE 没有把 FFN 换成完全不同的东西。它多加了一个路由器：面对多个专家 FFN，路由器为当前 token 选出少数几个，再将选中专家的输出汇总。区别是“走同一间思考室”，还是“按题目分配到少数几间专科思考室”；共同点是，专家内部仍是 FFN。

所以先把 dense FFN 的逐 token 变换看懂，读 MoE 才不会把“选专家”误认为“取消 FFN”。关于路由、共享专家和稀疏计算，可回读《DeepSeek MoE：为什么大模型不必每次全员上班》（待发布）。

![](04-transformer-preview.png)

## 🧩 输出怎么安全回到 Transformer？

思考室不是终点。FFN 输出会通过残差连接加回这一步的输入：

> **输出 ＝ 输入 ＋ FFN(输入)**

这意味着 FFN 即使暂时学不到有用变换，原信息也有一条直通路可以保留。关于这条“别把原话丢掉”的路线，可以回看[残差连接：为什么 56 层比 20 层还差](https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg)。

而相加前后，归一化会帮助数值尺度保持稳定。它是 Transformer 拼图里的下一块；这一篇先不展开 Pre-Norm、Post-Norm 与训练细节，下一篇我们专门拆归一化。

回头看整层的节奏，就是：**圆桌交流 → 独立思考 → 保留原话，并整理尺度。** 注意力解决“该听谁”，FFN 解决“听完后如何逐个加工”。《Attention Is All You Need》没有让 FFN 多余，反而让它的分工更清楚。

你更想下一篇先拆“归一化为什么能稳住数值”，还是再用一个例子把 MoE 的路由过程走一遍？评论区告诉我。

关注「数解AI」，我们会把 Transformer 从 token 如何进入模型，到每个模块如何计算、如何协作，连成一条能自己推演的线，而不只记住术语。

---

📖 **大模型原理系列**：① 词嵌入（待发布）→ ② 位置编码（待发布）→ ③ 注意力机制（待发布）→ ④ 前馈网络 FFN（本篇）→ ⑤ 归一化（待发布）→ ⑥ Transformer 全景（待发布）

📖 **深度学习基础回读**：① [梯度下降：蒙着眼下山](https://mp.weixin.qq.com/s/V6mGvCVFpTvmC51pNtxiTw) → ② [损失函数：打分标准决定学习方向](https://mp.weixin.qq.com/s/zIWqYqYVzEaF1e8P6fcTfw) → ③ [反向传播：AI 怎么知道自己错在哪](https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g) → ④ [Softmax 为什么不直接取最大值？](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw) → ⑤ [残差连接：为什么 56 层比 20 层还差](https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg) → ⑥ [优化器：为什么 Adam 比 SGD 更会走路](https://mp.weixin.qq.com/s/8TlJTXs0rZRYK2N3FUgqOA)
