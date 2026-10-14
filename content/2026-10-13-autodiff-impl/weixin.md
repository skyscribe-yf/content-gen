---
title: "导数公式不是人写的，除了算特征值这种"
wechatUrl: "https://mp.weixin.qq.com/s/_cNwyI7GiYJXB5zin5rjuw"
author: "数解AI"
date: "2026-10-13"
type: "原理篇"
series: "AI中的数学"
digest: "404 个函数、110 个原语，而一个普通层只用到 6 个。绝大多数公式没人写，是链式法则自己拼的；剩下要人写的，都在硬骨头和黑盒里。关键词：自动微分、JAX、PyTorch。"
cover: "00-cover.png"
keywords: ["自动微分", "JAX", "PyTorch", "导数", "特征值"]
---

`jax.numpy` 对外暴露 404 个可以调用的函数。

但你的模型训练代码里真正用到的，却是那些没人给你写公式的算子：归一化、激活、甚至是你自己随手拼出来的那个除法。

它们全都能求导，而且结果是对的。这又是怎么做到的？

## 一、先看你随手拼的那个算子

### 一个普通层，编译出来只有 6 个原语

这里的「计算图」，指的是编译器把你的 Python 函数展开后得到的一串基本运算：每个节点是一次运算（加一个数、乘一个矩阵），边是数据从哪来到哪去。实测一个「线性 + tanh + 手拼 LayerNorm」的 block，这张图里只有 6 个不同的操作：

```
add, broadcast_in_dim, div, dot_general, reduce_sum, tanh
```

其中 `h / (mean(h) + eps)` 是我自己在代码里拼的，**没为它写过任何求导公式**。

但 `jax.grad` 照样能给它求导，结果与方向差分一致到 1.18e-08。

这正是[反向传播](https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g)那篇里说的链式法则——只是那篇讲的是怎么理解它，这里讲的是机器怎么把它跑起来。

### 组合为什么够用

链式法则不需要框架认识你的函数，它只需要认识最后那几个原子操作。

你把一百个算子拼成一个新算子，导数不用你操心——只要每个原子操作的导数是已知的，中间那些拼装全部自动。

## 二、「原语」到底是什么

### 判定标准只有一条

它在计算图里是不是一个独立的节点。

把函数 trace 成 JAX 的中间表示，每个节点都记着自己属于哪个原语；能用更小的原语拼出来、而且框架愿意拼的，就不是原语。

原语不是「简单的数学函数」，而是框架的 IR 决定不再拆开的那一层，这是工程选择，不是数学概念。

### 同一个函数停在哪一层，各框架并不一样

这是本次实测的粒度表：

| 你写的 | 图里的操作 | 个数 |
|---|---|---|
| `jnp.tanh(x)` | `tanh` | 1 |
| `x @ W` | `dot_general` | 1 |
| `jnp.stack([x, x])` | `stack` | 1 |
| `jnp.mean(x)` | `reduce_sum`、`div` | 2 |
| `jax.nn.softmax(x)` | `exp`、`max`、`reduce_max`、`reduce_sum`、`sub`… | 8 |
| `jnp.linalg.cholesky(A)` | `cholesky` 本身 + 8 个包装与校验节点 | 9 |
| `jnp.var(x)` | `square`、`reduce_sum`、`select_n`… | 9 |
| `jnp.logsumexp(x)` | `exp`、`log`、`max`、`is_finite`… | 13 |
| `jnp.linalg.slogdet(A)` | `lu`、`cond`、`custom_jvp_call`… | 23 |

看 `cholesky` 那一行：9 个节点里 8 个是包装（报错、形状检查、编译边界），**真正的数学原语只有 `cholesky` 一个**。

### 「原语」有两层含义，别混

一层是中间表示层面的：一个节点就是一次原语调用，`jit`、`select_n` 这类包装与校验节点也算。

另一层是求导层面的：只有框架不打算再拆、而且需要一条导数规则的那些才算。**自动微分的规则表是按它们索引的。**

这两个数字放在一起看很有意思：JAX 里登记的前向导数规则有 199 条，而转置规则只有 76 条。相差的那 123 条规则，并不是遗漏了，而是压根儿就不需要实现，看到后面你就会明白为什么。

### 粒度是纯工程选择

`lax.linalg` 里只有 18 个原语，全是「大」算子：`cholesky`、`eig`、`eigh`、`lu`、`qr`、`svd`、`schur`……

框架故意不拆它们。拆开会丢性能、丢数值稳定性，而且用更小的原语**根本表达不出来**。

顺带说一句，这种「该在哪一层记账」的取舍，不只出现在求导表上。[DeepSeek V4.1 四十层网络，为什么不给每层都记账？](https://mp.weixin.qq.com/s/DBI990JLYtbxQGF3LIWbhQ) 讲的是同一类问题——层级粒度定在哪里，是工程判断。

所以粒度是纯工程选择。同一道数学题，两家框架可以停在完全不同的层级上。

![数量漏斗](01-数量漏斗.png)

## 三、代码里那张求导表，其实就是矩阵导数表

先接上前面那篇的落点。前面那篇[训练一步要算几千亿个导数，凭什么不会慢几千亿倍？](https://mp.weixin.qq.com/s/RxJ5LcgX46pwDwS38NR_UQ)讲的是「方向」。

它说的是：反向传播从头到尾都不构造雅可比矩阵，每一层只算一次「向量乘雅可比」，也就是 VJP（vector-Jacobian product）。

拿上游传回来的梯度，乘上这一层的雅可比，就得到要往更上游传的梯度。

框架里登记的那些「导数规则」，登记的正是每一层这个 VJP 怎么算。

那么这些 VJP 公式长什么样？这一节把它们和教科书里的矩阵导数摆在一起对照。

### 布局：先固定一个约定

矩阵微分的布局约定，在代码里变成 numpy 的广播规则：1-D 数组在 `@` 里既当行又当列，导致 VJP 里的 `g @ o.v.T` 维度对不上（我实测里就崩了两次）。

所以第一件事是先固定约定：把向量当列向量。下面都按这个来。

### 微分法：先写 df，再配内积

对任意标量函数 $f(X)$，只要能把微分写成这个样子：

$$df = \operatorname{tr}\!\left(G^\top dX\right)$$

那么 $G$ 就是梯度。因为 $\operatorname{tr}(A^\top B)$ 就是矩阵空间上的标准内积，而梯度的定义正是「满足 $df=\langle G,dX\rangle$ 的那个 $G$」。

要用的工具只有三条：微分的线性与乘积法则（$d(XY)=(dX)Y+X(dY)$）、trace 的转置与轮换，以及最后把它凑成 $\operatorname{tr}(\ast\, dX)$ 的形状。

一个例子走完全程。设 $X$ 可逆。

第一步不是凭空冒出来的。$\det$ 的微分有一条恒等式：

$$d\det X=\det X\cdot\operatorname{tr}\!\left(X^{-1}dX\right)$$

它分三步推出来。**第一步**：$\log$ 的链式法则给出

$$d\log\det X=\frac{d\det X}{\det X}$$

所以问题归结为 $\det X$ 怎么随 $X$ 变。

**第二步**：把 $X+dX$ 拆出因子 $X$，

$$X+dX=X\left(I+X^{-1}dX\right)$$

行列式对乘法是可分的，于是

$$\det(X+dX)=\det X\cdot\det\!\left(I+X^{-1}dX\right)$$

括号里那个 $\det(I+A)$，其中 $A=X^{-1}dX$ 是小量。按特征值的乘积展开：

$$\det(I+A)=\prod_i(1+\lambda_i)=1+\sum_i\lambda_i+\cdots=1+\operatorname{tr}A+\cdots$$

最后一步用了 $\sum_i\lambda_i=\operatorname{tr}A$。

**第三步**：把二阶以上的项丢掉——它们都是 $dX$ 的二次项，一阶微分里不要——就得到那条恒等式：

$$d\det X=\det X\cdot\operatorname{tr}\!\left(X^{-1}dX\right)$$

代回第一步，即

$$d\log\det X=\operatorname{tr}\!\left(X^{-1}dX\right)\;\Longrightarrow\;\frac{\partial\log\det X}{\partial X}=X^{-\top}$$

对比「先把 $\log\det(X+dX)$ 展开、再逐元素求偏导」的写法，微分法只需要一行，而且不会转置错。

### 把两张表并排看

| 前向 | 反向（回传） | 对应的矩阵微分 |
|---|---|---|
| $Z=XY$ | $\bar X=\bar Z Y^\top,\ \bar Y=X^\top \bar Z$ | $dZ=(dX)Y+X(dY)$ |
| $Z=X^{-1}$ | $\bar X=-X^{-\top}\bar Z X^{-\top}$ | $d(X^{-1})=-X^{-1}dX\,X^{-1}$ |
| $Z=\log\det X$ | $\bar X=\bar Z\cdot X^{-\top}$ | $d\log\det X=\operatorname{tr}(X^{-1}dX)$ |
| $Z=\operatorname{softmax}(x)$ | $\bar x=p\odot(\bar z-p^\top\bar z)$ | $J=\operatorname{diag}(p)-pp^\top$ |

第一列是你设计神经网络某一层时用到的那一层的向量操作，具体形式完全依据你的设计而定；中间是框架里登记的反向规则。**它们是同一张表**，只是行列转了一下。

还有一个结构上的细节值得一提：加法在前向是分叉，反向变成求和。这正是「一次拿全梯度」的原因。

### 框架自己也提供手写的那条路，公式一模一样

JAX 的 softmax 有两套实现，用一个开关切换。打开后走的是手写规则，写成 `y * (x_dot - (y * x_dot).sum(...))`——**和上表里那一行是同一个式子**。

（[Softmax 为什么不直接取最大值？](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw) 讲过这个函数为什么会变成现在这个样子，这里只看它的导数长什么样。）

手写的好处其实是可以减少计算量，属于工程上的优化手段；从数学角度看，它和自动拼出来的规则完全等价。

![两张表](03-VJP表就是矩阵导数表.png)

## 四、什么时候真得有人写公式

### 两类算子绕不过去

**第一类：编译器无法自动推导出计算图的。** 自定义 CUDA 内核、融合算子、第三方库调用、黑盒模拟器——就是那种只能靠你告诉它导数长什么样的算子。

PyTorch 的 `derivatives.yaml` 里登记了 688 条算子，其中 **42 条显式标着「尚未实现」**，就是还没人给的。

**第二类：能推出来，但是反向传播计算很昂贵，或者结果非常不稳定。**

`softmax`、`layernorm`、`attention` 的融合反向省的是显存与算力；而 `eig`、`svd`、`solve`、`cholesky` 这类矩阵级算子，伴随公式有实质的数学难度，而且**根本没法靠组合绕开**——你不可能用加减乘除和 `exp` 拼出一个 `eig` 来。

### 手写的代价：得引论文

先补一句 Cholesky 是什么：它把一个对称正定矩阵 $A$ 拆成一个下三角矩阵和它转置的乘积，$A=LL^\top$。

工程上用它解线性方程、算行列式。而「对 Cholesky 求导」，问的是 $L$ 的每个元素怎么随 $A$ 变。

JAX 的 `cholesky` 前向规则源码里，注释直接写着「Forward-mode rule from https://arxiv.org/pdf/1602.07527.pdf」，引的是 Murray 2016 那篇《Differentiation of the Cholesky decomposition》。

规则本体是两次三角求解拼出来的。这不是写代码的人偷懒，而是数学本身有难度。

### 手写的边界：框架自己写在注释里

`eigh` 的源码注释原文是这样的：

> Derivative for eigh in the simplest case of distinct eigenvalues. … The general solution treating the case of degenerate eigenvalues is considerably more complicated.

翻译过来：这条规则只对**互异特征值**成立；重根情形「考虑起来复杂得多」，后面甩了三篇文献。

实测也印证了这句话。重根处：

- `grad(λ_min)` 仍然给 `diag(1,0,0)`——特征值梯度正常；
- **`grad(特征向量)` 全是 NaN**。

无重根时两者都正常。所以这不是实现有 bug，是一条**写明了适用范围的规则**。

### 为什么偏偏是特征值这类算子

回到标题里那半句例外。为什么 `sin`、`exp`、矩阵乘法都能自动拼，而特征分解不行？

先拆一个常见误解。很多人以为特征值对矩阵的导数就是「特征向量乘特征向量」：

$$\frac{\partial \lambda_i}{\partial A} = v_i v_i^\top$$

这个式子**只在矩阵对称、且特征值互异时**才对。它是微扰论的结论，不是定义。

本文实测过：对称矩阵上，自动微分的 `grad(λ_i)` 与 $v_i v_i^\top$ 逐元素一致，而且它**没有除法**——所以特征值本身其实很好说话。

真正难缠的是**特征向量**。它的导数里有一个除法：

$$\frac{\partial v_i}{\partial A}\ \sim\ \frac{1}{\lambda_i-\lambda_j}$$

分母是两个特征值之差。后面所有的麻烦，根子都在这个分母上。

### 脆弱一：重根处特征向量没有定义

重根处特征向量不是唯一确定的——任何一组张成同一个子空间的向量都可以当特征向量。

既然特征向量本身都不唯一，它对矩阵的导数自然无从谈起。**框架给 NaN 不是偷懒，是在说实话：这里本来就没有定义。**

而特征值仍然有定义（它不依赖向量怎么取），所以继续给正常值。这个分裂很能说明问题：同一行代码里，一半有定义，一半没有。

### 脆弱二：间距越小，特征向量的梯度越大

![重根与近重根](04-eigh重根与近重根.png)

实测（对称矩阵 $[[1,\varepsilon],[\varepsilon,1+\text{gap}]]$，$\varepsilon=0.01$）：

| 特征值间距 | $1/(2\Delta)$ | 特征向量梯度最大值 | 比值 |
|---|---|---|---|
| 1.000 | 0.50 | 0.500 | 1.00 |
| 0.102 | 4.90 | 4.784 | 0.98 |
| 0.022 | 22.4 | 17.01 | 0.76 |
| 0.020 | 25.0 | 18.07 | 0.72 |

同一批矩阵上，**特征值梯度的范数始终是 1.000000，一动不动**。

一边随间距缩小而放大，一边纹丝不动。这就是为什么标题把「算特征值」单拎出来：麻烦不在特征值，在特征向量。

### 脆弱三：间距不会缩到零，但那已经够大了

看表格最后两行：把传入的 gap 从 0.010 压到 0.001（缩小十倍），**真实间距只从 0.022 降到 0.020**，几乎不降了。

这不是实现的毛病，是数学本身的性质：扰动会让靠近的特征值**互相排斥**，间距会被顶住，不会一路滑向零。

所以更准确的说法不是「除数趋零、梯度爆炸」，而是：梯度被这个排斥机制顶在一个**很大但有限**的值上（上表里约 18）。

对 float32 来说，这个量级已经足够把下游计算的相对误差吃掉一大截。**真正坑人的是这里，不是教科书里那个无穷大。**

### 脆弱四：写代码的人通常不知道自己的矩阵踩中了哪条

上面几条的共同点是：**前提一般不满足，而你通常不知道。**

特征值靠得很近的矩阵在机器学习里并不罕见——协方差矩阵、注意力矩阵、归一化层的统计量，都容易出近重根。

而一套通用规则得把「特征值交叉」的情形分开讨论，这正是注释里那三篇文献要处理的事。

于是框架的选择就好理解了：**与其给一条可能静默出错的规则，不如只支持一个写明适用范围的版本，剩下的一律报 NaN。**

NaN 虽然难看，但至少它不假装自己是对的。

把这几条合起来看，就明白标题为什么拿「算特征值」当那个例外。

它是那种**知道怎么求导的人不多、又不能靠通用规则拼**的算子——倒不是写不出来，只是没法随手就写。

### 真正需要人写的，是那些奇形怪状的操作

![组合与那少数例外](02-组合与黑盒.png)

加减乘除太朴素了，下面这些才是「原语」这个词真正有意思的地方：

| 操作 | 为什么拆不掉 | 导数规则 | 实测 |
|---|---|---|---|
| `cumsum` | 前缀和是扫描 | 反向 cumsum | 与手写公式逐元素一致 |
| `gather` / `scatter` | 索引与累加语义 | 互为转置；重复索引要散射加 | 索引 `[0,0,2]` 时梯度 = `[2,0,1]` |
| `sort` / `top_k` | 比较与置换，本身不连续 | 几乎处处零梯度；用置换散射 | `top_k(w,2)` 之和的梯度 = `[1,0,1]` |
| 卷积 | 融合内核，拆开性能崩 | **转置卷积 + 翻转核** | 不翻核则输出整体反转 |
| 重计算（checkpoint） | 它是「用重算换内存」的**指令**，不是数学函数 | 规则不是导数，是**重算** | 梯度与不加 checkpoint 差 2.2e-16 |
| `stop_gradient` | 它是「切断」的**指令** | 规则就是返回 0 | — |

有两件事值得单独拎出来说。

一是重计算和 `stop_gradient` 说明「原语」不等于「数学算子」——控制流与内存策略本身也可以是原语。

二是 `sort`、`gather`、`scatter` 把「分叉变加法」从标量推广到了索引：**同一个下标被取多次，反向就要累加。**

### 量化里的梯度，是「约定」最工业化的样子

DeepSeek 在 FP4 量化感知训练里，反向用的是前向那份 FP8 权重，梯度直接回传 FP32 主权重：

$$\frac{\partial \mathcal{L}}{\partial W_{\text{master}}} \approx \frac{\partial \mathcal{L}}{\partial W_{\text{quantized}}}$$

前向让模型感受到低精度误差，反向不让离散量化把梯度链切断。这就是直通估计器。

[FP4 量化：4 位数字怎么做到无损](https://mp.weixin.qq.com/s/Bra0y-wCSeYEW5ABxa3slw) 讲的是这套方案本身，这里想指出的是它跟求导的关系：量化本身不可导，能训下去靠的是一条人为约定的规则。  

到了这一步就很清楚了：`relu'(0)=0`、`abs'(0)=0`、`max` 在并列处的选择、量化里的 straight-through estimator，这些都不是推出来的，是选出来的。做量化、稀疏、离散结构时，梯度从哪来永远是设计决策。

![STE](05-STE前后向.png)

### 但维护成本不在数学

真正的维护成本不在数学，在覆盖与验证：每加一个新内核，要么配规则、要么保证它可组合；规则写错不会报错，只会静默给错梯度。

## 五、谁保证这些公式是对的

### 差分才是裁判

三条路对照着看：手写实现、中心差分、教科书解析式。

**「与解析式对上」这一列全是 0，但它证明的只是两段代码用了同一个公式**——说明实现没写错，不说明公式对。

真正能当裁判的是差分那一列，因为差分不认识解析式，它只是自己去试。

### 所以两边都把数值检查挂在持续集成上

PyTorch 有 `gradcheck`，JAX 有 `check_grads`。把「公式对不对」从一道数学题变成一道测试题，这是唯一能规模化的办法。

![三路裁判](06-三路裁判.png)

### 一个真实的坑：默认精度坑了我一次

JAX 默认 float32。我第一次跑 `check_grads(order=2)` 就挂在 rtol=0.002 上（相对差 0.0094），这不是自动微分错了，是 float32 的极限。开 `jax_enable_x64` 后全部降到 1e-16 量级。

二阶导尤其敏感：差分和乘法都会放大相对误差。

这类「明明算对了、结果还是错」的经验，在[误差不是会互相抵消吗？量化模型为什么还是掉点？](https://mp.weixin.qq.com/s/hYKy3dyHXEQkwoN7YmdREA) 里也出现过——偏差不会自己抵消，只会一层层累积。

## 六、所以那些公式是谁写的

回到开头那三个数字：404 个可调用，110 个原语，而一个普通层只用到 6 个。

上一篇[训练一步要算几千亿个导数，凭什么不会慢几千亿倍？](https://mp.weixin.qq.com/s/RxJ5LcgX46pwDwS38NR_UQ)讲的是「方向」——为什么反向一次就能拿全梯度。这一篇讲的是「公式」——那些规则从哪来。

- **绝大部分没人写**——是链式法则在最后那几个原子操作上自己拼出来的。
- **少数必须人写的**，都是前面说的两类：编译器无法自动推导出计算图的，和数学上真的难、组合不出来的。

你不需要为每个函数准备公式，只需要为每个「黑盒」准备公式；黑盒的数量由内核生态决定，不由 API 数量决定。

## 七、一个还没被回答的问题

写到这里还有一个我自己没想明白的地方。

矩阵微分本身有一套「把矩阵导数压成一个大矩阵」的做法，用 vec 和 Kronecker 积硬把它拉平。而现代自动微分走的是完全相反的路：**从不构造那个大矩阵，只做一次向量回传。**

这两条路线在教学上应该是顺序关系，还是替代关系？我倾向后者，但没有找到把两者并列比较的权威文献。

---

两篇合起来看，一件事讲「方向」，一件事讲「公式」——`backward()` 那一行背后的全部，大概就是这些了。

那么回到这个问题：你有没有被自动微分那些晦涩的实现绊住过，或者认真想过它到底是怎么做到的？

如果这篇让你第一次看清那些公式的来历，点个赞 👍、收藏 ⭐ 备用。关注「数解AI」，AI 原理和工程，慢慢拆。

📖 **[AI中的数学合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4655868530679185411#wechat_redirect)**：本篇是「矩阵微分与自动微分」这一支的第 2 篇。同一条线上还有 [反向传播](https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g)、[Softmax](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw)。

🔥 **热门文章**：

[KV缓存存进SSD：慢50倍的硬盘，为什么反而更快？](https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA)  
[高维空间为什么全是壳？内积才是那把尺子](https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q)  
[高斯为什么二阶就够？非线性去哪了](https://mp.weixin.qq.com/s/gs_3y7JXuBLlzR5w6jW6fQ)  
[学习率怎么自动调？Adam 优化器拆给你看](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)  
[DeepSeek-V4为何不用MLA？](https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ)  
[随机变量为什么不是变量？它其实是个函数](https://mp.weixin.qq.com/s/5BxjOUblW64DXNffHc2sxQ)  
[反向传播是什么？AI怎么知道自己错在哪](https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g)  
[DeepSeek V4.1 四十层网络，为什么不给每层都记账？](https://mp.weixin.qq.com/s/DBI990JLYtbxQGF3LIWbhQ)  
[Softmax为什么不直接取最大值？](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw)  
[FP4量化：4位数字怎么做到无损](https://mp.weixin.qq.com/s/Bra0y-wCSeYEW5ABxa3slw)  
[误差不是会互相抵消吗？量化模型为什么还是掉点？](https://mp.weixin.qq.com/s/hYKy3dyHXEQkwoN7YmdREA)  

**参考资料与数字溯源**

1. Wikipedia《Automatic differentiation》—— 原语与 tape、正向一次一列 / 反向一次一行、最优 Jacobian 累积是 NP-complete
2. JAX《The Autodiff Cookbook》—— VJP 定义、约 3 倍算力开销是单次调用的价、内存随计算深度增长、`custom_jvp` 要求规则对切向量线性
3. JAX 源码 `jax._src.lax.linalg`：`_cholesky_jvp_rule`（注释直引 arXiv:1602.07527，Murray 2016）、`_eigh_jvp_rule`（互异特征值适用范围的注释原文与所引三篇文献）
4. Petersen & Pedersen《The Matrix Cookbook》§1–§2 —— 微分法所用恒等式目录
5. Parr & Howard《The Matrix Calculus You Need For Deep Learning》，arXiv:1802.01528
6. PyTorch《Autograd mechanics》（2.14）—— 计算图、版本计数、不光滑点的六条取值规则、Wirtinger 微积分
7. PyTorch `tools/autograd/derivatives.yaml`（main 分支）—— 688 条算子登记，其中 42 条标 `not_implemented`
8. `micrograd/engine.py` —— 深度优先拓扑序 + `self.grad +=` 的累加写法
9. DeepSeek-V4 技术报告 FP4 量化感知训练一节 —— 反向等价于直通估计器，梯度回传 FP32 主权重
10. 本文全部内省与实测数字由本机脚本跑出：Python 3.12.3 / jax 0.11.2（`rule_count.py` / `primitive_anatomy.py` / `exotic_prims.py` / `conv_adj.py`），脚本在 `~/scripts/matrix-calculus-ad/`

#自动微分 #JAX #PyTorch #梯度 #数解AI
