# 大纲：损失面上全是坑，为什么梯度下降还能走到谷底？

- 轨道：数学轨（数学直觉线，非系列续集；合集「AI中的数学」）；独立可读，开头零导航，全文不做「第 N 篇」表述
- 排期：2026-09-24 20:00（门禁不过则顺延）；目录 `content/2026-09-24-nonconvex-saddle/`
- grill 日志：`.grill/2026-09-24-nonconvex-saddle.md`（本文件所有决策的收敛过程）
- 篇幅：作者 2026-09-24 拍板「放宽到 3k」，同日因追加「当年那句说法对不对」一节再放宽到 **≈3.4k**（B.3 推导密度豁免）；本篇执行 = 正文 ≈3.4k 字、含尾部 ≤4k，放长部分**只允许是推导、实验与一手证据引述**，禁止铺垫与元话语
- 配图：封面 21:9 + AI 概念图 3 + 脚本图 3（数字全部落在脚本图；AI 图零文字零数字）

## 交付句（本篇的双半句）

- **转 1（坑稀有）**：你不是掉进坑里出不来——**高维空间里「坑」是稀有事件**。一维只有一个方向，方向往下掉就叫坑；D 维要求 D 个方向全部往上抬才算坑，所以局部极小占临界点的比例约 $2^{-D}$：20 维里约百万分之一，50 维里几乎可以忽略。鞍点才是常态。
- **转 2（噪声是那只手）**：就算站在鞍点/高原上，**迷你批采样自带的噪声就是把你推下去的那只手**——批量越小噪声越大、逃得越快。所以「抖」不是算法的缺陷，是它能训起来的机制本身。
  - ⚠️ **方向条件（作者质疑带出的补丁，必写）**：不是「任何噪声都行」——**只有噪声在负曲率方向上的那部分分量才是那只手**。各向同性噪声是早期证明的技术假设，不是 SGD 的真实性质；SGD 的真实噪声沿负曲率方向的方差正比于该方向曲率、不随维度衰减（Daneshmand ICML 2018）。
- **回扣**：训练卡住不动，先别急着说「掉坑里了」——多半是站在马鞍上；而鞍点从来不是靠「想通」走出去的，是靠噪声推出去的。

⚠️ **事实纪律（本轮红线，成稿逐条遵守）**：

1. 标题「走到谷底」= 训练损失能降下去，**不是「收敛到全局最优」**——正文必须显式澄清（否则标题即夸大）。深度网络训练终点通常是低损失的非全局临界点。
2. 「坑」在正文指**局部极小**（大众用词）；理论陈述必须与 临界点 / 严格鞍点 / 非严格鞍点（平台）严格区分，不得把大众用词当数学定义用。
3. $2^{-D}$ 是**量级估计**（依赖各方向曲率符号近似独立），不是严格等式；正文按量级陈述并标注一手来源。实验数出来以 `results.json` 为准。
4. 实验②的真实机制是「处在**对称临界流形**上、沿打破对称方向的梯度恒为 0」，**不是「梯度全为 0 卡死」**——这是本篇最容易写错的一处。
5. DeepSeek V4.1-Flash 发布时间写 2026（`docs/data-freshness.md` 红线）；不重复 V4.1 KV 系列既有篇目的内容。

## 标题候选（角度已定＝坑型疑问句；检查点作者拍板）

- **T1（作者已选）**：损失面上全是坑，为什么梯度下降还能走到谷底？
- T2（备选，实验数字出来后可用）：高维空间里全是马鞍，坑才是稀有的那个——梯度下降凭什么还能训好？
- T3（备选垫底）：梯度为 0 的地方，为什么九成九不是谷底？

自检（T1）：①大众直觉词「坑」前置 ✓ ②反常识（非凸 = 坑多，为什么还能训好）✓ ③疑问句 ✓ ④小白一眼懂（零前置知识）✓ ⑤关键词含「梯度下降 / 损失面」（Adam 篇 1,109 验证该词吃量）✓ ⑥钩子在前 15 字内 ✓ ⑦非章节标题 ✓ ⑧转得出去（显得内行）✓ ⑨术语零个（「鞍点」不入标题）✓

⚠️ **封面文字 = 最终发布版标题逐字**（标题定稿后再生成封面，不重蹈 09-21 封面与实发标题不一致）；封面版式按 `docs/image-generation.md`「封面标题显眼度规格」：金色发光标题横贯全幅、两行居中、每行字号约画面高 1/9–1/8、整块文字高度 ≤ 画面高 1/4、背景压暗退后、画面禁止任何其他文字。

## 与既有文章的区隔（硬性）

| 已答过的问题 | 出处 | 本篇处理 |
|---|---|---|
| 高维空间的薄球壳、距离失效、「内积才是那把尺子」 | 08-12 高维空间（1,539 读） | **不重推**；只在 §3 用一句「同一个指数律」（薄壳的 $(0.95)^d$ 与本篇的 $2^{-D}$ 同源）并内链一次；不出现「壳」的推导 |
| Hessian / 二阶展开为什么「够用」 | 08-21 高斯为什么二阶就够 | **不重讲二阶近似**；本篇用 Hessian 只为定义曲率符号（极小 vs 鞍点），一句内链 |
| 优化器的自适应步长（Adam 的矩估计）、学习率怎么自动调 | 07-10 优化器（1,109 读） | **不重讲 Adam**；本篇只在工程结论里说「学习率 = 离开鞍点的速度」，不涉及矩估计 |
| Muon 只记一份账（正交化更新） | 08-06 Muon | 不出现 |
| MoE 路由负载均衡 / 专家坍缩 | 09-08 MoE 负载均衡 | **不出现**（机制上最像，明确回避，防自撞） |
| 方差的来源与「时灵时不灵」（偏差-方差） | 09-06 方差 | 不重讲方差分解；噪声只说「来自采样的方差」，推导只到 $\mathrm{Var}\propto 1/B$ |
| 量化误差为什么会互相抵消（中心极限） | 09-09 CLT-FP8 | 不重讲误差相加 |
| 扩散模型的训练目标 / 分数 / 引导 | 09-20~09-22 系列 | 不出现 |

## 开头草样（原声槽 1 + 驱动问题；前 100 字进入实质、零导航）

> 【槽 1 · 你亲手写的原句，逐字进稿，我只修错别字】
>
> （AI 收口句草样，待你确认）我当时的第一反应也是：坏了，掉进局部最优里爬不出来了。后来才弄明白，我那次根本没掉进坑——我是站在一块马鞍上，而高维空间里的「坑」，比我想的稀有得多。

驱动问题：**损失面是非凸的，坑到处都是，为什么梯度下降还能走到底？**

## 结构（6 节；小标题连成故事链）

### 1. 一堂课留下的一个不服气

- **槽 1（作者亲历：当年学吴恩达深度学习课时对「高维鞍点靠随机性被跳出去、所以 SGD 能有效收敛」这句话的质疑）** → 驱动问题：**损失面是非凸的，坑到处都是，梯度下降到底靠什么走到底？**
- 立靶子：非凸确实坑多、梯度下降确实只看局部信息——这两句都对，**错的是由此得出的结论**。
- 澄清标题口径（**红线 1**）：「走到底」= 训练损失能降到足够低，不是「找到全局最优」。
- 收口：「坑」到底是什么，得先说清楚——它不是一个形容词，而是一个关于方向的判据。

### 2. 什么叫「坑」：一维看斜率，高维看 D 个方向

- 一维（公式 ①）：$f'(x)=0$ 有三种结局——谷底、山顶、拐点；只看斜率分不出是哪种。
- 判据要升级到二阶（公式 ②）：$f''(x)>0$ 是谷底，$f''(x)<0$ 是山顶，$f''(x)=0$ 是拐点。
- 高维（公式 ③）：梯度为零的点叫**临界点**；此时要看 Hessian 的 D 个特征值——全正 = 局部极小；有正有负 = **鞍点**；全负 = 极大。
- 人话一句：一维只有一个方向，方向往下掉就叫坑；D 维要求**所有方向都往上抬**才算坑。
- 细分（本节只到这里，不展开）：负曲率有明确大小的叫**严格鞍点**；曲率恰好为 0、梯度也为 0 的叫**非严格鞍点**（平台）——后者是真能困住人的那一种，留到 §4。
- 收口：那么问题变成——在高维空间里，随机撞上一个临界点，「所有方向都往上抬」的概率有多大？

### 3. 维度一高，坑就成了稀有事件

- 把每个方向的曲率符号想成一次近似独立的抛硬币：全正的概率约 $2^{-D}$（**红线 3**：量级估计，非严格等式）。
- 数字表（脚本图 1）：D = 2 / 5 / 10 / 20 / 50 时局部极小占比，以及「负特征值个数」的分布众数（半数的方向在往下掉）。
- 冲击句：20 维里，临界点里只有约百万分之一是坑；50 维里基本可以忽略。**鞍点是常态，坑是稀有事件。**
- **实验①（脚本图 1 的数字源）**：高维随机场上找 ∇f = 0 的点，统计局部极小 / 鞍点比例与负特征值个数分布。数字全部落 `results.json`。
- 与薄球壳同源（**一句内链，不重推**）：$2^{-D}$ 和 $(0.95)^d \to 0$ 是同一个指数律——维度一高，极端事件就变稀有 / 变普遍。
- 收口：既然坑这么少，那卡住的时候到底卡在哪？

### 4. 卡住的时候，你多半是站在马鞍上

- 严格鞍点上的真相：那一点梯度为 0，但**沿负曲率方向稍微动一下，梯度就重新出现**——所以它不是一个「终点」，只是一个走得极慢的地方。
- 慢到什么程度（公式 ④）：离鞍点距离 ε 时，梯度大小正比于 ε；走到曲率量级所需时间约 $\ln(1/\varepsilon)/|\lambda|$——**是慢，不是停**。ε 小到初始化尺度那样，就是「看起来卡死了」。
- 非严格鞍点（平台）：梯度恰好为 0，确定性梯度下降在这里真的走不动——这才是「坑」以外真正能困住人的东西。
- 噪声从哪来（**关键一步**）：不是算法故意加的抖动，是**迷你批抽样自带的方差**（公式 ⑤：$\mathrm{Var} \propto 1/B$，批量越小噪声越大）。
- 一手结论：带噪声的随机梯度能在多项式/对数时间内逃出严格鞍点；确定性梯度下降只保证收敛到临界点（可能停在鞍点上）。
- 收口：噪声这只手能推你，前提是**马鞍得先被摇动**——那就去看一个最真实的鞍点，它就在你的初始化里。

### 5. 真有一个鞍点藏在你的初始化里

- **实验②（脚本图 2/3 的数字源）**：把一个隐藏层的权重**全部初始化成同一个值** → 训练发生了什么。机制（**红线 4**）：此时网络处在**对称临界流形**上——沿「打破对称」的方向梯度恒为 0，于是所有神经元永远同步更新，网络**等效于只有一个神经元**，容量白扔，损失卡在高原。
- 数字：相同初始化 vs 随机初始化 vs 相同初始化 + 噪声的损失曲线与逃逸步数（落 `results.json`）。
- 真实对应（**一手 config**）：各家发布模型的 `config.json` 里必有一个 `initializer_range`——随机初始化不是「习惯」，是防鞍点：DeepSeek V4.1-Flash（2026-09-10 技术报告，552B 骨干 + CED 分阶段激活 prefill 8B / decode 16B，MIT 开源）与 GLM-5.3-Flash（320B 总参 / 18B 激活）的一手数值。
- 理论一手来源：对称/冗余带来的平台（Fukumizu & Amari 2000）、对称初始条件保持对称（Saad & Solla 1995）。
- 收口：把两个实验放一起，答案已经完整了——坑稀有，卡住的真身是鞍点，而打破它的两样东西，正好是两个训练超参。

### 6. 当年那句说法，到底对不对（**作者质疑 + 反例制度化节**）

- 先给结论三行：**定理是真的、条件是苛刻的、反例是真实存在的**。
- 定理侧（一手引述）：严格鞍点 + SGD → 多项式步数收敛到局部极小（Ge et al. 2015，自称首篇非凸 SGD 全局收敛保证）；扰动下降逃逸鞍点的代价只依赖维度的 poly-log、"escape saddle points almost for free"（Jin et al. 2017）；普通 SGD 沿负曲率方向的噪声足够强，不需要额外注入各向同性噪声，收敛率与维度无关（Daneshmand et al. ICML 2018）。
- 条件侧（三条，逐条给）：① 鞍点必须是**严格**的（有负曲率方向）；② 噪声必须在**那个方向上有分量**；③ 随机初始化（Lee et al. 2016 原话 "almost surely with random initialization"）。
- 反例侧（两个）：Swirszcz et al. 2016 构造出反例——真实网络确实会掉进坏局部极小，那些「没有坏局部极小」的结论 "hold under very strong assumptions which are not satisfied by real models"；Kawaguchi 2016 证明存在「**Hessian 没有负特征值的坏鞍点**」（层数 > 3）——恰好对应 §5 实验里那个 1e-17 的平台，逃逸定理在这里一个字都用不上。
- 第三个偷换：「逃出鞍点」≠「找到好解」；「局部极小稀有且接近全局」挂着三个模型假设（变量独立 / 参数冗余 / 均匀性），是假设而非网络的普遍事实。
- 收口（槽 6 原声位置）：所以那句课上的话，当「方向」用没问题，当「保证」用就过头了。

### 7. 所以，卡住时该动哪个旋钮

- 回扣开头（**必须回答驱动问题**）：你那次卡住不是掉进坑，是站在马鞍（或平台）上；而高维空间里，坑本来就稀有。
- 工程结论（可复用）：**批量大小 = 噪声尺度**（B 小 → 噪声大 → 逃得快；B 大 → 噪声小 → 容易停在鞍点/平台）、**学习率 = 离开的速度**。两者是配合关系，不是二选一——把批量和学习率一起放大，往往等于「噪声变小 + 步子变大」，反而更容易卡。
- 一句话总结卡（分享借口）：「如果只转一句话给同事：训练卡住，多半不是掉进坑里，是站在马鞍上等噪声推它一把。」
- 互动问（**30 秒可答**）：训练卡住不动，你会先调学习率还是先动批量大小？
- 点赞 / 收藏 / 关注引导（价值承诺 + 数学直觉合集结构）。

## 原声槽位（6 处；逐槽交互采集，AI 只给位置 + 建议句，作者逐条手打）

| 槽 | 位置 | 作用 | 建议方向（作者改写/手打） |
|---|---|---|---|
| 1 | §1 开头 | 现象钩子（作者当年那堂课的不服气） | 学吴恩达 DL 课时对「高维鞍点靠随机性跳出去」的质疑，以及后来自己训练里的遭遇 |
| 2 | §2 末 | 「坑」的直觉类比 | 拿生活里的坑/马鞍做一句作者口径的类比 |
| 3 | §4 中 | 噪声那只手（含方向条件） | 作者对「噪声反而是好东西」以及「噪声得落在对的方向上」的第一反应 |
| 4 | §5 中 | 对称初始化 | 作者对「全初始化成同一个值、单元间差 1e-17」这个实验结果的直觉评论 |
| 5 | §6 首 | 对「业界不以为然」的立场 | 作者对「课上的说法到底哪儿过头了」的判断 |
| 6 | §7 首 | 工程结论口径 | 作者对「批量 vs 学习率」的实操判断 |

## 实验与数字事实源（已跑完，`run_experiment.py` + `results.json`，seed 20260924）

自检：脚本内置 11 条断言全过（含 D=1 的解析值 1/2、D=2 与独立三维求积对账、对称性不破的三组断言）。

**实验① 临界点的二阶结构（随机对称矩阵，蒙特卡罗）**

| 维度 D | 「所有方向都朝上」的概率 | 平均负特征值个数 / D | 抽样量 |
|---:|---:|---:|---:|
| 1 | **50.0%**（解析值也是 1/2） | 0.500 | 20 万 |
| 2 | **14.6%** | 0.500 | 20 万 |
| 3 | 2.46% | 0.500 | 20 万 |
| 5 | 0.0125%（约八千分之一） | 0.500 | 20 万 |
| 8 | 0（两万次抽样零命中） | 0.500 | 10 万 |
| 10 | 0（六万次抽样零命中） | 0.500 | 6 万 |
| 20 / 50 | 0（各两万 / 四千次抽样零命中） | 0.500 | — |

- **实测衰减：每多一维 ×0.121**（拟合区间 D=1–5）；而「各方向独立抛硬币」的粗估是每维 ×0.5（即 $2^{-D}$）——实测比粗估还狠，$2^{-D}$ 只能当**乐观下限**。
- 典型指数精确钉在 D/2（六位数字均 0.500），指数波动很小（D=10 时标准差 0.68，不到一个方向）。→ 「所有方向都朝上」要偏离均值 D/2 个方向，属极端尾部。
- 口径：这是「临界点的二阶结构」模型（Bray & Dean 的指数分布是同一个量），**不是**「任意损失函数都这样」——正文必须带上模型前提。

**实验② 真实随机场里的临界点普查（不是矩阵模型，是具体函数）**

- 1D 随机场：95 个临界点 = 47 谷底 + 48 山顶 → **谷底占 49.5%**（低维里根本不稀有）。
- 2D 随机场：334 个临界点 = 98 谷底（**29.3%**）+ 156 马鞍（**46.7%**）+ 80 山顶（24.0%）。

**实验③ 对称性鞍点（小 MLP，同样数据、同样步数、同一步长）**

| 设定 | 最终损失 | 隐藏单元间参数最大差异 |
|---|---:|---:|
| 全同初始化 + 全批量梯度 | **1.203** | **1.4e-17**（对称从未破） |
| 随机初始化 | 0.00384 | 0.744 |
| 全同初始化 + 参数级独立噪声 σ=0.01 | **0.000901**（最低） | 0.741 |
| 全同初始化 + 小批量噪声（batch=8） | 0.259 | **5.6e-17（对称照样没破）** |
| 逐点梯度方差 vs 批量 | — | log-log 斜率 **−0.978**（即 Var ∝ 1/B） |

- 两个反差数字：① 全同初始化的损失是随机初始化的 **313 倍**；② 小批量噪声把损失从 1.203 拉到 0.259，但**单元间差异仍是 5.6e-17——它没打破对称，只是在一个被压扁的模型里找了个更好的点**（修正 B 的实验铁证）。
- 工程落点：批量决定噪声尺度（斜率 −0.978 ≈ 1/B），但要打破对称靠的是**参数级彼此独立的随机性**，不是「抖动」本身。

## 配图清单（6 张正文图 + 封面）

| # | 类型 | 内容 | 数字 |
|---|---|---|---|
| 00 | 封面 21:9 | 金色发光标题横贯全幅（标题逐字）、背景压暗（马鞍曲面 + 稀疏散点） | 无 |
| 01 | AI 概念图 | 一维的三种临界点：谷底 / 山顶 / 拐点（视觉化三结局） | 零文字零数字 |
| 02 | AI 概念图 | 高维的马鞍：一个方向往下、一个方向往上（D 维直觉） | 零文字零数字 |
| 03 | AI 概念图 | 初始化里的对称鞍点：一排完全同步的神经元 vs 被噪声打破 | 零文字零数字 |
| 04 | 脚本图 | 局部极小占比 vs 维度 D（断崖下降 + 理论量级线） | 全部数字在图上 |
| 05 | 脚本图 | 负特征值个数分布（临界点里半数的方向在往下掉） | 全部数字在图上 |
| 06 | 脚本图 | 三组初始化的损失曲线（相同 / 随机 / 相同+噪声） | 全部数字在图上 |

## 门禁清单（成稿后逐项执行）

- `docs/article-quality-check.md` 16 项 + 恢复期 B 六条（独立可读 / 认知交付 / 篇幅 / 术语人话 / 开头 100 字白盒 / 文末问题 30 秒可答）
- 公式：mdnice 实渲，`merror` 0、`katex` 0、最长公式不横向滚动（宽度用实渲 SVG 的 `width` 量）
- 加粗失效 0（CommonMark flanking 坑：句末标点移到 `**` 之外）
- 中文入公式 0；全文超 60 字长句 0（原声豁免）；段落 ≤3 句
- 待发布残留 0；mp 链接全溯源（`scripts/check_wechat_links.py`）
- 热门榜：`python3 scripts/hot_articles.py --md --cited <weixin.md>` 生成（行间无空行、行尾两空格），`--self-check` 通过
- 尾部：📖 AI中的数学 合集导航（合集链接 + 箭头链）、话题标签 3–5 个、3 处利他钩子至少命中 2（可复用/可传递/可表态）
- 图片与 `weixin.md` 同级、无 `images/` 前缀；AI 图逐张核验零文字零数字

## 事实核查结果（2026-09-24 完成；全一手来源）

⚠️ 执行方式说明：项目惯例是子代理核查，但子代理通道被本机配置阻断（`~/.pi/agent/settings.json` 所有 agent override 用了已移除字段 `fallbackModels`，`subagent {action:"list"}` 直接报错）。本轮由主会话直接取一手来源核查，证据链如下。

1. **鞍点而非局部极小才是高维优化的主障碍** — Dauphin et al. 2014 (NIPS, arXiv:1406.2572) 摘要原话："it is often thought that a main source of difficulty for these local methods to find the global minimum is the proliferation of local minima with much higher error than the global minimum. Here we argue ... that a deeper and more profound difficulty originates from the **proliferation of saddle points, not local minima**, especially in high dimensional problems of practical interest. Such saddle points are surrounded by **high error plateaus** that can dramatically slow down learning, and give the **illusory impression of the exis[tence of local minima]**"。→ 本篇的核心断言（你以为掉坑里，其实是站在高损失平台上）有直接出处，可逐字引用。
2. **局部极小数量的指数衰减** — Choromanska et al. 2015 (ICLR, arXiv:1412.0233) 摘要原话："the lowest critical values of the random loss function form a layered structure ... lower-bounded by the global minimum. The number of local minima outside that band **diminishes exponentially with the size of the network**" 。⚠️ 注意口径：原文说的是**网络规模**，不是「维度」——正文不得把两者混写成同一句话。
3. **临界点的「指数」分布** — Bray & Dean 2007 (Phys. Rev. Lett. 98, 150201；arXiv:cond-mat/0611023) 摘要原话："We calculate the average number of critical points of a Gaussian field on a high-dimensional space **as a function of their energy and their index**"。→ 支撑「绝大多数临界点是马鞍、典型指数接近 D/2」的定性陈述；$2^{-D}$ 作为「各方向曲率符号近似独立」的**粗估（下限直觉）**出现，正文必须标明是量级估计，实测数由实验①给。
4. **噪声逃逸的代价只有维度的多项式对数** — Jin et al. 2017 (arXiv:1703.00887) 摘要原话："a perturbed form of gradient descent converges to a second-order stationary point in a number iterations which depends **only poly-logarithmically on dimension** (i.e., it is almost 'dimension-free') ... perturbed gradient descent can **escape saddle points almost for free**"。
5. **确定性梯度下降只保证到局部极小 / 临界点** — Lee et al. 2016 (arXiv:1602.04915) 摘要原话："We show that gradient descent converges to a local minimizer, **almost surely with random initialization**"（严格鞍点假设下；随机初始化是关键前提）。
6. **对称 / 冗余直接造出平台** — Fukumizu & Amari 2000 (Neural Networks 13(3):317-327) 摘要原话："It is proved that a critical point of the model with H−1 hidden units always gives **many critical points** of the model with H hidden units. These critical points consist of **many lines in the parameter space**, which can cause **plateaus** in learning of neural networks." → 实验②的理论依据（对称临界流形 + 平台）。
7. **模型一手 config（理论-实践落点）** — HuggingFace `deepseek-ai/DeepSeek-V4.1-Flash/raw/main/config.json`：`text_config.initializer_range = 0.02`（同文件 `n_routed_experts` 384 / `num_experts_per_tok` 6 / `num_hidden_layers` 40 / `max_position_embeddings` 1048576 / `expert_dtype` fp4 / fp8 量化；模型 2026-09-10 上架，技术报告《Pushing the Limits of KV Cache Compression》）。`zai-org/GLM-5.3-Flash/raw/main/config.json`：`text_config.initializer_range = 0.02`、`vision_config.initializer_range = 0.02`。→ 两家旗舰都写 0.02：「随机初始化」不是习惯而是防对称鞍点的实文号。

### 核查带出的两处口径修正（必须落到正文）

- **修正 A（§3）**：$2^{-D}$ 只能作为「独立符号」的粗估出现，不得写成定理；正文的量级陈述改挂在 Bray & Dean 的**指数分布** + 实验①实测数上。
- **修正 B（§4/§5）**：**小批量噪声本身不会打破对称性鞍点**——所有隐藏单元参数逐位相同时，同一个 batch 上它们的梯度也逐位相同（$
abla_{\theta_i}=
abla_{\theta_j}$），对称永远不破。真正能打破它的是**参数级彼此独立的随机性**（或一开始就随机初始化）。这一条很反直觉，是本篇实验②的关键结论，正文必须写准，不得写成「SGD 噪声打破对称」。

- **修正 C（§4 与新增 §6，作者质疑带出）**：「噪声是那只手」必须写成「**噪声在负曲率方向上的分量才是那只手**」——各向同性是早期证明的技术假设，不是 SGD 的真实性质；SGD 真实噪声沿负曲率方向的方差正比于该方向曲率、不随维度衰减。逃逸定理的三个条件（严格鞍点 / 噪声有该方向分量 / 随机初始化）必须在 §6 逐条给出，「逃出鞍点 ≠ 找到好解」也要显式说。

### 作者反向质疑的一手核查（2026-09-24 追加，全一手来源）

11. **Ge, Huang, Jin, Yuan 2015**（arXiv:1503.02101，*Escaping From Saddle Points — Online Stochastic Gradient for Tensor Decomposition*）摘要原话："we identify **strict saddle** property ... stochastic gradient descent converges to a local minimum in a **polynomial number of iterations**. To the best of our knowledge this is **the first work that gives global convergence guarantees for stochastic gradient descent on non-convex functions**"。
12. **Daneshmand, Köhler, Lucchi, Hofmann, ICML 2018**（arXiv:1803.05999，*Escaping Saddles with Stochastic Gradients*）摘要原话："the variance of stochastic gradients **along negative curvature directions** ... stochastic gradients exhibit a **strong component along these directions**. Furthermore ... **contrary to the case of isotropic noise** — this variance is **proportional to the magnitude of the corresponding eigenvalues and not decreasing in the dimensionality** ... explicit, isotropic noise ... **can successfully be replaced by a simple SGD step** ... the **first convergence rate for plain SGD to a second-order stationary point in a number of iterations that is independent of the problem dimension**"。→ 作者记的那句话有直接定理支撑，且比课程措辞更强。
13. **Kawaguchi 2016**（arXiv:1605.07110，*Deep Learning without Poor Local Minima*）摘要原话："there exist **"bad" saddle points (where the Hessian has no negative eigenvalue)** for the deeper networks (with more than three layers)"。→ 退化鞍点（无负曲率），逃逸定理管不着；与实验②的 1e-17 平台同类。
14. **Swirszcz, Czarnecki, Pascanu 2016**（arXiv:1611.06310，*Local minima in training of neural networks*）摘要原话："It is known that such results hold under **very strong assumptions which are not satisfied by real models** ... one can construct **counter-examples** (datasets or initialization schemes) when the network does become **susceptible to bad local minima**"。→ 「业界不以为然」的一手出处。

### 未做与降级

- Ge et al. 2015 已补取（作者质疑带出，用于 §6 的「定理是真的」侧）；Saad & Solla 1995 未取（Fukumizu & Amari 2000 已足够支撑平台机制）。
- 子代理通道待作者处置后恢复（见 `.grill/2026-09-24-nonconvex-saddle.md` 与台账开放问题）。
