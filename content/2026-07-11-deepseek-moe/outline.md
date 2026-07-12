---
type: mixed
density: per-section
style: notion
palette: warm
image_count: 6
---

## Illustration 1
**Position**: 💡 直觉解释：医院分诊台
**Purpose**: 对比 Dense（所有科室全看）和 MoE（只挂相关科室）的直觉差异
**Visual Content**: 左：Dense 模型 — 一个病人同时对着 8 个科室窗口，每个窗口都亮着。右：MoE 模型 — 分诊台护士指向 2 个科室，其余 6 个灰色/休眠。底部标注"671B 参数 → 每次只激活 37B"
**Type**: comparison
**Filename**: 01-hospital-triage.png

## Illustration 2
**Position**: 💡 直觉解释：知识存在哪
**Purpose**: 解释注意力层 vs FFN 层的分工 — 注意力管"看"，FFN 管"想"
**Visual Content**: 上半部分：注意力层 — 多个 token 之间画连线（"看上下文"）。下半部分：FFN 层 — 每个 token 激活大量内部神经元节点，标注"巴黎 → 法国首都、埃菲尔铁塔"。中间大字标注 "Attention Is NOT All You Need — 知识存在 FFN 里"
**Type**: infographic
**Filename**: 01b-knowledge-in-ffn.png

## Illustration 3
**Position**: 📐 数学原理：路由器是怎么做决策的
**Purpose**: 展示门控路由的三步流程 — 打分 → 选人 → 加权
**Visual Content**: 左到右流程图。Step 1: token 输入 x → 乘 W_g → softmax → 得分向量 [0.02, 0.15, 0.41, ...]。Step 2: Top-k 筛选 → 只保留第 3 和第 5 个专家（0.41, 0.22）。Step 3: 专家 Expert₃ 和 Expert₅ 各自计算 → 按分数加权求和 → 输出。底部标注"256 个专家，每次只激活 8 个"
**Type**: flowchart
**Filename**: 02-gating-router.png

## Illustration 4
**Position**: 📐 数学原理：256 个专家，谁来管？
**Purpose**: 对比 Auxiliary Loss（收费站）和 Bias Trick（信号灯）
**Visual Content**: 左：收费站 — 每条车道都有收费站，车辆排队交"不均衡税"，标注"α 大 → 污染梯度"。右：智能信号灯 — 路口信号灯根据车流量调整绿灯时间，车内人不被干扰，标注"b_i 只影响选择，不影响权重"。下方标注公式：选择阶段 g_i+b_i → top-k，加权阶段用原始 g_i
**Type**: comparison
**Filename**: 03-bias-trick.png

## Illustration 5
**Position**: 🔧 算法实现
**Purpose**: 展示 MoE 前向传播的数据流 — token 如何经过门控分发到不同专家
**Visual Content**: 从上到下数据流。顶部：一批 token [N, D] 输入。中间分叉：一路走门控（softmax+bias → top-k），一路走专家计算（for each expert → expert(x[tok])）。底部：加权求和 → 输出 [N, D]。关键标注"raw scores 加权，gated scores 选人"
**Type**: flowchart
**Filename**: 04-moe-dataflow.png

## Illustration 6
**Position**: 🌍 实战：DeepSeek 的 MoE 全景
**Purpose**: 展示 V3 到 V4 的参数演进，突出激活比的变化
**Visual Content**: 双栏对比。左栏 DeepSeek-V3（2024.12）：671B 总参数，37B 激活参数，激活比 5.5%，图标较小。右栏 DeepSeek-V4 Pro（2026）：1.6T 总参数，~160B 激活参数，激活比 10%，图标更大。共享专家 1 个（两栏共用）。底部标注"路由专家数不变（256），激活专家数不变（8），专家容量大幅提升"
**Type**: comparison
**Filename**: 05-v3-v4-comparison.png
