---
type: mixed
density: balanced
style: editorial-flat-vector
palette: warm-technical
image_count: 5
language: zh
backend: zairouter
---

## Illustration 1

**Position**: 开头衔接段之后 / 全系列训练回路
**Purpose**: 让读者看到 RLVR 是后训练链条中的奖励设计转折，而不是孤立算法。
**Visual Content**: 预训练 → SFT → RLHF → PPO → GRPO → RLVR；前三段偏表示与指令，后三段偏反馈与策略更新，RLVR 节点高亮。
**Type Application**: 横向流程与阶段分组。
**Filename**: `01-training-route.png`

## Illustration 2

**Position**: 第二节最小数学闭环之后
**Purpose**: 直观区分“奖励来源”和“策略更新”两个维度。
**Visual Content**: 问题 → policy 生成答案/轨迹 → 编译/测试/沙箱 verifier → 奖励 → PPO/GRPO 更新；用两种颜色区分 verifier 与 optimizer。
**Type Application**: 左到右流程图，两个模块区用虚线分隔。
**Filename**: `02-rlvr-loop.png`

## Illustration 3

**Position**: 第三节 L0 案例之后
**Purpose**: 解释 coding → Agent 的反直觉迁移。
**Visual Content**: 理解任务 → 读取状态 → 改代码 → 执行测试 → 观察报错 → 修正 → 通过；底部用一条轨迹奖励箭头连接所有动作。
**Type Application**: 循环流程图，终点奖励向整条轨迹回传。
**Filename**: `03-coding-to-agent.png`

## Illustration 4

**Position**: 第四节防线表格之后
**Purpose**: 让 Reward hacking 的三层风险可视化。
**Visual Content**: 真实目标 → 代理指标 → verifier → 环境权限四层；三条红色风险路径分别指向指标表面、环境漏洞、奖励篡改，旁边对应沙箱、隐藏测试、独立审计等防线。
**Type Application**: 分层框架图，风险用珊瑚色，防线用绿色。
**Filename**: `04-reward-hacking-boundary.png`

## Illustration 5

**Position**: 第五节结果奖励与过程奖励表格之后
**Purpose**: 对比结果验证和过程验证，说明密集奖励不自动等于可靠奖励。
**Visual Content**: 左侧“结果验证”：终点答案/测试通过，信号清晰但稀疏；右侧“过程验证”：中间状态/工具调用/子目标，信号更密但 verifier 成本和攻击面更高。
**Type Application**: 左右对比图，中间用“可靠性 × 密度 × 攻击面”三角关系连接。
**Filename**: `05-outcome-process-verification.png`
