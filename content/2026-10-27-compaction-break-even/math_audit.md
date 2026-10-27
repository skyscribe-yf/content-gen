# math_audit — 上下文压缩的钱账（C2）

> 2026-10-27。正文每个数字的出处与口径，逐条可回溯。数据事实源：`compaction_controlled.json`（脚本 `scripts/compaction_stats.py` 可复现）+ 官方价目页（2026-10-26/27 核，发布前重开复核一次）。

## 1. 公式台账

### M1 每轮成本模型（一阶 token 口径）

- 压缩前每轮：上下文 $T$ 几乎全命中缓存 → 成本 $\approx \rho T$（输入价 $c_{in}$ 为单位 1）
- 压缩后第 1 轮：前缀改变 → 缓存全灭 → 全价 $T'$（缓存写价 ≈ 输入价或更高，全价口径已覆盖）
- 压缩后稳定轮：$\approx \rho T'$
- 每轮节省：$\rho T - \rho T' = (T-T')\rho$
- 一次性代价：压缩调用 $\kappa T$ + 首轮差价 $T'(1-\rho)$

### M2 回本轮数

$$N^* = \frac{\kappa T + T'(1-\rho)}{(T-T')\rho}$$

推导：一次性代价 ÷ 每轮节省。性质：$\rho$ 在分母 → $N^* \propto 1/\rho$（正文核心句）。

**假设与边界**（正文已声明「一阶近似」）：不含输出 token；不含阶梯计价/峰谷切换；未来轮数 = 会话内剩余 assistant 消息数（代理指标）；多数样本压缩调用未单列计费（$C_{comp}=0$ 口径偏保守，N\* 被低估）。

## 2. 机器数字台账（✅ = compaction_stats.py，2026-10-26 扫描）

| 正文数字 | 值 | 口径 |
|---|---|---|
| 压缩总次数 | 202 | 全量 compaction 事件 |
| 干净窗口 | 51 | 同 provider+model、前后各 5 轮 |
| 可回本检验 | 49 | $T>T'$ |
| 降幅 | 267,916→60,889（聚合 77%；逐样本中位 75%） | 标题 77% 由此 |
| 压缩前每轮 | input 1,006 / 命中 99.6% / $0.0818 | 前 5 轮中位 |
| 压缩后第 1 轮 | input 34,543 / 命中 48.5% / $0.1083 | ✅ |
| 第 3/5 轮 | $0.0198 / 命中 98.3% | ✅ |
| 成本比 | 中位 1.35× / P90 13.4× / 最大 31× | 后 1 轮÷前末轮，n=45 有费用 |
| what-if N\* | ρ=0.20→1.6 轮/100%；0.10→3.5/96%；0.02→19.3/84% | 49 样本逐一重算 |
| C>0 子集 | n=12，ρ=0.02→53.6 轮/92% | 压缩调用有计费 |
| GPT-5.x 拟合 ρ | 0.1000（R²=1.000，n>1.6 万行） | ainaiba/fenno 账单 |
| GPT-5.x 实测回本 | 15/15（ainaiba/gpt-5.5） | 真实账单 |
| fenno 短会话 | N\*=6 vs 未来 27 轮 → 67% | n=3 子集 |
| 会话寿命 | 压缩后未来轮中位 99 | 51 窗口 |

## 3. 官方价目（2026-10-27 核；发布前重开复核）

| 家 | 缓存命中 | 输入 | 输出 | ρ |
|---|---|---|---|---|
| DeepSeek V4.1-Flash（deepseek-flash-1017） | 0.02/0.04 元（空闲/高峰） | 1/2 元 | 4/8 元 | **0.02（两时段同）** |
| DeepSeek V4-Pro | 0.15/0.30 | 4.5/9.0 | 13.5/27 | 0.033 |
| GLM-5.3-Flash（Z.ai 官方，美元） | $0.03 | $0.15 | $0.50 | **0.20** |
| OpenAI | 输入价 10% | — | — | 0.10 |

- DeepSeek 峰谷：2026-08-17 起，工作日 9–12/14–18 为高峰，空闲为高峰半价；**折扣系数 ρ 两时段同为 0.02**（0.02/1 = 0.04/2）。
- ⚠️ **2026-10-27 价目修正**：GLM-5.3-Flash 曾误采第三方人民币转售价（输入 0.8 / 缓存命中 0.23 元 → ρ≈0.29），已改用 **Z.ai 官方价 $0.15/$0.50/$0.03 → ρ=0.20**（lmspeed 2026-10-16 核验镜像，源为 Z.ai 定价页）；what-if 相应更新：ρ=0.20 → N\* 中位 1.6 轮 / 100% 回本，ρ 比值 14 倍 → **10 倍**（0.20/0.02）。

## 4. harness 事实（§4）

- Anthropic `clear_at_least`：官方文档原文 "Ensures a minimum number of tokens is cleared each time the strategy activates. If the API can't clear at least the specified amount, the strategy will not be applied." + "This helps determine if context clearing is worth breaking your prompt cache." + "Invalidates cached prompt prefixes when content is cleared. To account for this, clear enough tokens to make the cache invalidation worthwhile."（platform.claude.com context-editing 页，2026-10-27 核）✅
- Codex：`model_auto_compact_token_limit`（官方 docs/config.md，触发自动压缩阈值）、per-tool `output_token_limit`（v0.60.0 起默认输出上限 10k，Issue #7867）✅
- OpenCode 历史教训：早期每轮 prune 工具结果击穿缓存，**后来已改**——正文只写历史。来源：作者观察 + 社区讨论；**不写成现状**。

## 5. 数据排除记录（内部口径，不进发布稿）

- **讯飞（xunfei / xunfei-ex）**：作者 2026-10-26 拍板「数字也不要算」，全量排除（78 个窗口）——不报 cacheRead、cost=0，且把聚合中位数拉低、命中率压平。
- **ollama-cloud**：作者 2026-10-26 拍板「计费不准」，钱账排除（34 个窗口）。
- **commandcode**：ρ 拟合 >1（≈10.25）计价异常，排除（5 个窗口）。
- **opencode-go 网关拟合**（V4-Pro 0.003 / glm-5.2 0.186）：作者 2026-10-27 指令「V4-Pro 网关的例子去掉」，论证走官方价；网关拟合仅作交叉验证存档（series-plan §4.4），不进正文。

## 6. 禁项自检（已过 quality_check.py）

- N\* 不写成账单预测 ✅（正文有「一阶近似」「方向判断」边界句）
- 16% 不脱离「DeepSeek 官方价 + 我的会话寿命」口径 ✅
- 排除 provider 名零出现 ✅（参考资料只写「已剔除计费口径不可信与无计费的样本」）
- 旧口径数字（170 轮 / 20% 回本 / 68%）零出现 ✅
