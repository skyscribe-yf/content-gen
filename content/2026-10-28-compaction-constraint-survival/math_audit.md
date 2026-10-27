# math_audit — C3 安全账（compaction-constraint-survival）

> 2026-10-28 建立。公式逐条列假设与出处；正文每个数字必须能回溯到本文件。本机数据：`scripts/constraint_survival_scan.py`（全量 4,041 会话 / 202 次 compaction 可复现）。

---

## M1 策略保持（Strategy Preservation）

**定义**：安全策略是谓词 $P(X)\in\{0,1\}$，压缩器 $f$。策略保持要求：

$$\forall X:\;P(X)=1\;\Rightarrow\;P(f(X))=1$$

**假设**：P 是完备谓词（安全/违规二值可判）；f 是确定性有损变换。**边界**：形式化模型，真实系统的策略常是概率性/上下文相关的；策略保持是理想性质，不是所有压缩器都必然违反。

**出处**：系列计划 §3.3 形式化；与 Governance Decay 的「constraint survives the summary」判据同构（论文用行为违反率近似 P）。

## M2 拉格朗日：目标函数里没有安全项

**压缩器目标**：

$$\max\;\mathbb E[S(f(X))]-\lambda\,\mathbb P(P(f(X))=0)$$

其中 $S$ = 任务成功度。**默认 $\lambda=0$**：压缩 prompt 与训练目标里只有任务连续性，「丢掉一条安全约束」在优化里是免费的。Governance Decay 摘要原话：compaction "optimizes for task continuity and treats standing policies as low-salience content"（arXiv 2606.22528，已核）。

**假设**：一阶分解——把约束保留当作可加惩罚项；真实压缩器是 prompt 工程 + 可能微调的混合体，λ=0 是「无显式约束保留机制」的近似。**边界**：本文用的 4 个 harness（Pi/Codex/Claude Code/OpenClaw）在压缩 prompt 里显式枚举了约束保留（本机 87.6% 的 summary 自带 Constraints 节实证）——即 λ 已被工业界手工调到非 0，但调的是「任务相关约束」，不是全谱安全策略；这正是 §1 形态分野的机制解释。

## M3 安全税：约束下的压缩率必须让步

$$R_P(D)\ge R(D)$$

在要求策略保持的约束下，可达的率失真（压缩率）不会优于无约束情形——保安全要付出压缩率/成本代价。**正文只作一句「为什么厂商不自动修」的解释，不展开推导**（Cover & Thomas 第 10 章率失真 + 约束优化；系列计划 §3.3）。

## 数字台账

### 本机扫描（constraint_survival_scan.py，可复现）

| 数字 | 值 | 口径 |
|---|---|---|
| 会话文件 | 4,041 | `~/.pi/agent/sessions/**/*.jsonl` 全量 |
| compaction 事件 | 202 | `type=="compaction"` 全量 |
| 约束实例 | 2,556 | 压缩点前最近 80 条 user 消息中，按句切分 + 四类模式匹配（禁止性/授权性/规则性/偏好性），同一压缩内按句去重 |
| Constraints 节覆盖率 | 87.6%（177/202） | summary 含 `## Constraints` 正则；节长中位 589 字符 |
| 规则形态幸存 | 90.8%，丢失 0.3% | n=2,363；结构化（markdown 编号/≥60 字/英文长句）= skill/系统注入 |
| 叮嘱形态幸存 | 56.0%，丢失 24.4% | n=193；口语短句 |
| 分类幸存 | 禁止 78.6% / 授权 93.2% / 规则 90.9% / 偏好 21.4% | n=612/633/1,297/14（偏好 n 小，正文不引用或标注样本量） |
| 丢失实例 | 54 条 | 人工判读：约 23 条去重真实约束，全部一次性叮嘱 |

**已知偏差**：① 幸存判据 = 显著 token 出现在 summary（token = 引号串/路径/标识符/issue 号）；改写（如「题图」→「封面图」）判丢失——改写即约束具体形态丢失，口径成立但偏严。② 约束实例按压缩事件计，同一叮嘱跨多次压缩重复计数（这是「实例」口径，非「去重规矩」口径，正文表述用「实例」）。③ 四类模式有误分类（bug 报告混入），已通过人工判读 54 条丢失实例校正，正文只引判读后结论。④ 202 次 compaction 集中在作者本人的 Pi 使用，不外推为行业结论——行业侧数字全部走论文。

### 论文与一手（已核摘要原文 / commit）

| 数字 | 值 | 出处 |
|---|---|---|
| 违反率跃升 | 0%→30%（最高 59%） | ConstraintRot，7 模型 1,323 episodes，arXiv 2606.22528 摘要 |
| 幸存开关 | 约束幸存违反率 0% / 丢失 38% | 同上摘要原句 |
| 软/硬衰减差 | 8.3× | 同上摘要原句 |
| Pinning 成本 | ~47 token（<0.5% 生产级压缩上下文）→ 违反率 0% | 同上摘要原句 |
| relinking 执行率 | 86.9% vs 清洁对照 17.0% | arXiv 2606.21732 摘要 |
| 防御失守 | 11 种代表性防御无一可靠；KBRA 残留 0.0% | 同上摘要 |
| Codex 修复 | commit #41852（2026-10-27） | openai/codex；压缩移除 `request_user_input` tool call → 可信用户回答从 model-visible history 消失 → Guardian 审查看不到；修法=与保留的 review history 匹配 |

### 正文禁项

- 不把 38% 说成「所有 agent 的失败率」（ConstraintRot 基准设定）；
- 不把 relinking 写成「压缩器是攻击者」（论文定性 confused deputy）；
- 不把 Codex commit 写成「现网正被攻击」（已修复的历史缺陷，且是授权丢失非注入）；
- 不重推 DPI/Fano（C1 已立，本篇一句引用）；
- 本机数字不跨口径混用（实例数 ≠ 去重规矩数）。
