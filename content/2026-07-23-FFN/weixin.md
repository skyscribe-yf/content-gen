---
title: "Attention都够了，为什么还要FFN？"
author: "数解AI"
type: "原理篇"
series: "大模型原理"
scheduledPublish: "2026-07-21T08:00:00+08:00"
digest: "Transformer 里，前馈网络（FFN）为什么接在注意力之后？注意力先把上下文汇进每个 token，FFN 再用 SwiGLU 独立扩张、筛选和投影这份表示。用一个可运行实验验证：改动一个 token，不会穿过 FFN 改变另一个。"
keywords: ["前馈网络", "FFN", "SwiGLU"]
cover: 00-cover-ffn.png
---

## 🎯 驱动问题

![](00-cover-ffn.png)

如果 Attention 都够了，Transformer 为什么还要留下一大块前馈网络（Feed-Forward Network，FFN）？更反直觉的是：它不让 token 彼此交流，却常常占去更多参数和计算。

注意力已经把其他 token 的线索汇进当前 token。FFN 不再开圆桌，而是接手这份**带上下文的表示**。

**逐 token 独立计算**，只说 FFN 这一步不再读取别的 token；上下文已经留在前一步更新过的向量里。

如果你熟悉注意力机制，可以直接往下读；如果想回顾“上下文怎样汇入 token”，可回看《注意力机制》（待发布）。这一篇只接着问：拿到上下文之后，每个 token 到底如何处理它？

![](01-roundtable-thinking-room.png)

把一层 Transformer 想成一次工作流程：token 先围坐圆桌，在注意力里听取彼此的线索；散会后，它们回到一间间没有门的思考室。每个人都带着刚收到的上下文，用同样的设备处理自己的笔记。这间思考室，就是 FFN。

## 💡 注意力负责互相看，FFN 负责各自想

设一段文字进入这一层后的表示是矩阵 X。第 i 个 token 是其中一行 xᵢ。

注意力的关键在于：第 i 个输出会根据 xᵢ 与其他 token 的关系，对很多 token 的 Value 做加权汇总。于是“银行”在“河岸”和“贷款”两种上下文里，能从别的 token 那里拿到不同线索。**注意力有跨 token 的混合。**

进入 FFN 的 xᵢ 不是孤立的原始词向量；它已经是注意力读取上下文后的表示。FFN 的独立性只限制它此刻不再读取 xⱼ。

FFN 的写法则很克制：

> **yᵢ ＝ f(xᵢ)**

同一个函数 f 会复用给每一行，但 yᵢ 的计算只读 xᵢ。第 1 个 token 不会在 FFN 内部读取第 2 个 token 的向量，也不会改写它的输出。它们**共享参数**，不等于它们在这一步**互相影响**。

所以 FFN 的“独立”不是“不知道上下文”。xᵢ 已在注意力里混入上下文；FFN 只是不在自己的计算里再开一次圆桌。


## 📐 一次 FFN：先扩张，再开门，再投影

现代大模型常用 SwiGLU 形式的 FFN。为了和后面的实验保持一致，先把它拆成四步：

> **gate ＝ SiLU(xW_gate)**
>
> **up ＝ xW_up**
>
> **hidden ＝ gate ⊙ up**
>
> **y ＝ hiddenW_down**

两条支路都把 d_model 维的输入送往更宽的 d_ff 维空间。向量在这里临时展开出更多可组合的方向；“更丰富”说的是容量，不是每一维都能贴上一个语义标签。

接着，SiLU 生成的 gate 像一排随输入而变的阀门。SiLU 不是只输出 0 或 1；它会连续地缩放每个方向。再把 gate 与 up 逐元素相乘，便得到“这份上下文表示这次该让哪些扩张方向通过、通过多少”的结果。

W_down 随后把较宽的 hidden 投影回 d_model 维，才能与这一层原有的表示相加。

![](02-swiglu-pipeline.png)

FFN 先铺开可选方向，再按输入筛选，最后回到原尺寸。

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

批量计算的两行 y，和把每一行单独送进同一组权重的结果完全相等。两次扰动也通过了：改第 1 个 token，第 2 个输出逐元素不变；反过来同样如此。

固定数值只是为了复现。关键在于扰动一行、观察另一行：FFN 里没有把这种变化跨行传出去的运算。

这只说明 FFN 层不混合 token。前面的注意力会让 xᵢ 随上下文改变，后面的注意力也会继续传递信息。

![](03-fixed-matrix-experiment.png)

## 🌍 真实国产模型的一条旁注

以 2026 年 [DeepSeek-V4-Pro 固定版本的 `config.json`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/raw/b5968e9190ef611bbf34a7229255be88a0e937c1/config.json) 为例，配置写有 `hidden_size: 7168` 与 `hidden_act: "silu"`：真实工程同样要确定表示宽度与非线性。配置是声明，不能单独推出能力因果。

## 🔀 Dense FFN 怎样长成 MoE？

普通的 Dense FFN 很直接：每个 token 都经过同一个“扩张 → 门控 → 投影”模块。

MoE 没有把 FFN 换成完全不同的东西。它多加了一个路由器：面对多个专家 FFN，路由器为当前 token 选出少数几个，再将选中专家的输出汇总。区别是“走同一间思考室”，还是“按题目分配到少数几间专科思考室”；共同点是，专家内部仍是 FFN。

先看懂 dense FFN 的逐 token 变换，才不会把 MoE 的“选专家”误认为“取消 FFN”。真实国产模型如何用路由组织多个 FFN，可回读[《DeepSeek便宜30倍的秘密：MoE混合专家入门》](https://mp.weixin.qq.com/s/QdkD0CR2fD-HfY77-gX3Ug)。

![](04-transformer-preview.png)

## 🧩 输出怎么安全回到 Transformer？

思考室不是终点。FFN 输出会通过残差连接加回这一步的输入：

> **输出 ＝ 输入 ＋ FFN(输入)**

即使 FFN 暂时学不到有用变换，原信息仍有直通路。想看这条路为什么重要，可回看[残差连接：为什么 56 层比 20 层还差](https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg)。归一化负责把数值尺度稳住，下一篇再拆。

一层 Transformer 的节奏很清楚：注意力把上下文写进 token，FFN 各自加工，残差和归一化把结果接回去。

你更想下一篇先拆“归一化为什么能稳住数值”，还是再用一个例子把 MoE 的路由过程走一遍？评论区告诉我。

关注「数解AI」，我们会把 Transformer 从 token 如何进入模型，到每个模块如何计算、如何协作，连成一条能自己推演的线，而不只记住术语。

---

📖 **大模型原理系列**：① [词嵌入](https://mp.weixin.qq.com/s/rDryn1z_hLt7mwi3X8fsxQ)→ ② [位置编码](https://mp.weixin.qq.com/s/4nO2VqQLaYxGdDmtQeypCQ)→ ③ 注意力机制（待发布）→ ④ 前馈网络 FFN（本篇）→ ⑤ 归一化（待发布）→ ⑥ Transformer 全景（待发布）

📖 **[训练回路合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4594958081087864833#wechat_redirect)**：梯度下降 → 损失函数 → 反向传播 → Softmax → 残差连接 → Adam

#FFN #前馈网络 #SwiGLU #大模型原理 #数解AI
