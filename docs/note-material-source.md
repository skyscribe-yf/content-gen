# Obsidian 笔记素材源（选题/大纲阶段必查）

> 2026-10-10 建档。作者的 Obsidian 学习笔记是**文章素材的一等来源**：里面有论文研读、机制拆解，也有**作者自己写的判断与批注（原生观点）**。
> **硬规则：起草选题/大纲前先查本文件 + 到 vault 里翻一遍**，不要在 AI 记忆里凭空造选题。

## 一、vault 位置与访问

| vault | 路径 | 规模 | 可读性 |
|---|---|---|---|
| **主 vault（在用）** | `/home/skyscribe/vaults/papers` | 87 篇，笔记都在 `AI-Chats/concepts/` | ✅ 直接读 |
| ↳ 自动索引 | `/home/skyscribe/vaults/papers/AI-Chats/_INDEX.md` | 日期 + 标题 + `[[wikilink]]` + tags 表 | ✅ **先读这个**，一屏看完全部笔记 |
| **旧 vault（WSL 时代）** | `C:\Users\skysc\Documents\Obsidian Vault`（含 `学习/` 子 vault） | 17 篇 Agent 论文研读 | ⚠️ **需先挂载**（见下） |

### 旧 vault 挂载（NTFS 分区未自动挂载）

```bash
udisksctl mount -b /dev/nvme0n1p3 -o ro   # Windows 分区 → /media/skyscribe/Windows
# 旧 vault 落在 /media/skyscribe/Windows/Users/skysc/Documents/Obsidian Vault/
udisksctl unmount -b /dev/nvme0n1p3       # 用完卸掉
```

- **只读挂载**（`-o ro`），不要写回 Windows 分区。
- 作者机器的分区布局：`nvme0n1p3` = Windows（300G）、`nvme0n1p4` = Data（253G）、`nvme0n1p6/7` = Linux 根与 home。
- ⚠️ `~/.agents/skills/obsidian-vault/SKILL.md` 里写的 `/mnt/d/Obsidian Vault/AI Research/` 是 **WSL 时代的死路径**（`/mnt/d` 现在是空目录），别照抄；真实路径以上表为准。

## 二、笔记分三类，引用前必须分清

`_INDEX.md` 写明这些笔记来自 AI chat 会话（Copilot Coach）——**是混合体，不是纯一手**：

| 类型 | 长什么样 | 用法 |
|---|---|---|
| **① 一手事实** | frontmatter 的 `source:` / `paper_ids:` / 带出处的引用块、原文摘抄（含 `arXiv:xxxx.xxxxx`、GitHub issue 号、官方博客链接） | 直接可追溯；**仍要打开原文复核**（见第四节红线） |
| **② 作者原生观点** | `## 我的判断`、`## 我的理解边界`、`## 苏格拉底问题`、正文里的第一人称批注、`⚠️ 未核实` 标记 | **原声素材，进稿逐字保留**，不得改写/润色（对应 `docs/writing-flow.md` 的原声句规则） |
| **③ AI 归纳** | 电梯演讲、TL;DR、对比表、批判性分析 | 只当线索；进稿前用自己的话重写并核对出处 |

> **选题时的优先动作**：先翻笔记的「我的判断 / 我的理解边界 / 苏格拉底问题」段落——那里是作者已经想清楚、且账号读者最缺的立场，比论文摘要值钱。

## 三、素材盘点（2026-10-10）

### 3.1 Agent 论文研读（旧 vault `学习/`，2026-05-22/23 爆发期，11 篇）

> 这批是全库**密度最高**的 Agent 素材，且 H 组（AI Agent 工程）正是当前流量引擎。

| 笔记 | 行数 | 可转化选题 | 目标组 | 状态 |
|---|---:|---|---|---|
| 记忆诅咒论文深度拆解.md | 537 | **「记忆诅咒」：记得越多，越不合作**（扩记忆→合作退化；18/28 设置合作崩溃；Llama-3.3-70B 信任博弈 −93.1pp；CoT **放大**而非缓解） | H 组 | ❌ 未写 |
| 记忆诅咒HL设计与真实Agent记忆的断裂.md | 369 | **HL 设计与真实 Agent 记忆的断裂**（论文的 HL 是扁平滑窗、每轮仅一个二元动作，跟真实 Agent 记忆不是一回事——哪些结论不能推广） | H 组（方法论批判） | ❌ 未写 |
| 多Agent协作的深层悖论.md | 378 | Memory Curse × RecursiveMAS × OMC × RL Conductor **四篇交叉**（记忆悖论三种解法 / 编排策略光谱 / 多 Agent 必要性实证） | H 组 | ❌ 未写 |
| Agent记忆研究深度拆解.md | 296 | **「Agent 的记忆是备忘录，不是记忆」**（M/S/C/H 四篇：CAS 记忆 ≠ true memory，需规则式权重巩固） | H 组 | ⚠️ 与 10-05 记忆篇**部分重叠**，写前先读那篇防重复 |
| RL驱动的Agent记忆管理研究深度拆解.md | 377 | 记忆管理从「架构设计」转向「策略学习」（用 RL 决定何时读/写/**遗忘**；记忆管理建模成 POMDP） | H 组 | ❌ 未写 |
| Multi-Agent RL Fine-Tuning研究深度拆解.md | 274 | **单 agent RL 的收益在多 agent 交互里被稀释甚至逆转**（MAGRPO / RAGEN / Dr.MAS；信用分配至今未解） | H 组 | ❌ 未写 |
| Multi-Agent LLM最新研究进展.md | 333 | 六大方向**全景**（组织架构 / 协作机制 / 失败归因与自进化 / 记忆与信任 / 内化与蒸馏 / 协议与生态） | H 组 · **收编文候选** | ❌ 未写 |
| RL Conductor论文深度拆解.md | 458 | **用 RL 训一个 7B 的 Conductor，让它自己学会派活**（ICLR 2026，Sakana AI；自动学编排 vs 人工模板；最低 token 使用） | H 组 + K 组（成本） | ❌ 未写 |
| SSL论文深度解读.md | 384 | **技能为什么是 SKILL.md 文本而不是结构**（北大 SSL，调度-结构-逻辑三表示；技能发现 / 风险评估 / 复用三个实验） | H6 技能系统 | ❌ 未写 · **H6 的具体素材** |
| 泛化差距定理的数学严谨性审查.md | 383 | **把一篇论文的定理逐行审一遍**（检索记忆 vs 参数记忆的组合泛化分离定理；指出 Assumption 1 的循环性风险、语境无关性声明存疑） | 数学组 + H 组 | ❌ 未写 |
| Seed Cola DLM × ELF 深度拆解.md | 1084 | **连续潜变量语言建模的两条路径**（字节 Seed Cola DLM 扩散 vs 何凯明 ELF 流匹配；AR 范式三重困境） | G 组 + 数学组 | ❌ 未写 |

### 3.2 高维概率 HDP 系列（主 vault，~50 篇）

> 教材级系统性笔记（高维概率），**与账号「AI 中的数学」支柱直接对口**，是长尾选题的富矿。
> 过滤原则照旧：反常识 + 数字 + 为什么，**必须有 AI 落点**。

| 笔记 | 可转化选题（候选角度） | 状态 |
|---|---|---|
| HDP-3.1-范数集中与薄壳现象 | 「高维空间为什么全是壳」 | ✅ 已写 `2026-08-12-维度诅咒` |
| HDP-3.2-协方差矩阵与PCA | 协方差矩阵 | ✅ 已写 `2026-08-21-多维高斯注解` |
| HDP-2.2-Hoeffding / 2.3-Chernoff / 2.9-Bernstein | **集中不等式**：为什么一百个样本就能估准一个平均值（训练集损失为什么能代表真实分布） | ❌ 未写 |
| HDP-2.4-Median-of-Means | 中位数为什么比平均抗离群（重尾分布下的估计器） | ❌ 未写 |
| HDP-2.6-次高斯分布 Overview（460L）/ 2.6.1-次高斯范数 / 2.7-次高斯和 | **次高斯**：为什么"尾部"决定一切 | ❌ 未写 |
| HDP-2.8-Subexponential分布 | 次指数分布 | ❌ 未写 |
| HDP-4.2-Nets-Covering-Packing（372L） | **ε-net**：要覆盖整个空间，为什么只要几个点（学习理论的地基） | ❌ 未写 |
| HDP-3.5-Grothendieck + 3.5.1-SDP | Grothendieck 不等式（比最大割更深的那个） | ❌ 未写 |
| HDP-3.7-KernelTrick与Grothendieck改进（474L） | **核技巧**：为什么把数据映射到无限维反而更好算 | ❌ 未写 |
| HDP-4.3-Error-Correcting-Codes（302L） | 用球面装箱推**纠错码**上界 | ❌ 未写 |
| HDP-4.4-次高斯随机矩阵上界（282L） | 随机矩阵的谱范数 | ❌ 未写 |
| HDP-4.5-社区检测应用（320L） | SBM + 谱聚类 | ❌ 未写 |
| HDP-3.3.4-凸集均匀分布 / 3.3.5-Frames | 凸集均匀分布 / 框架 | ❌ 未写 |

### 3.3 信息论 / 量化 / 压缩（主 vault，与 D 组、KV 系列接得上）

| 笔记 | 可转化选题 | 状态 |
|---|---|---|
| Johnson-Lindenstrauss变换.md | **JL 引理**：降维为什么几乎不丢距离（**强 AI 落点：embedding 降维**） | ❌ 未写 |
| Shannon率失真理论.md | **率失真**：压缩的极限在哪（**AI 落点：量化、VAE**） | ❌ 未写 |
| 核函数总览与MMD.md | **MMD**：生成模型怎么"量距离" | ❌ 未写 |
| RaBitQ-TurboQuant-深度理解.md（495L） | 向量量化（与 KV cache 量化接） | ❌ 未写 |
| QuIP-QuaRot-LLM量化.md | LLM 权重量化 | ❌ 未写 |
| 相位敏感性-分块KV压缩的周期性弱点.md（218L） | 分块 KV 压缩的相位弱点（平均分会掩盖周期性失误） | ❌ 未写 |

### 3.4 DeepSeek 课程 16 课（主 vault，~25 篇）——**基本已消化**

KV-Cache 地基 / MLA / Decoupled-RoPE / V4-CSA-HCA / Lightning-Indexer / NSA / mHC / MoE-MTP / Muon / FP8 / FP4-QAT / KV-Disk / CP 系列 / 五维并行 / DualPipe / DeepEP 已分别对应到已发文章。

**剩两篇未消化**：

| 笔记 | 可转化选题 | 状态 |
|---|---|---|
| DeepSeek-第8课-DeepSeek-Math.md | DeepSeek 的**数学数据工程**（与 D6 合成数据篇不同层：那篇讲"用 AI 造数据"，这篇讲"数据怎么筛/怎么配比"） | ❌ 未写 |
| DeepSeek-第12课-V4-Technical-Report全景导读.md（206L） | **V4 技术报告收编文**（一篇文章搞懂 V4 全景）——收编轨，吃转发 + 搜一搜长尾 | ❌ 未写 · 收编文候选 |

### 3.5 系统 / 架构 / Agent 工程（主 vault，最近 3 天写的）

| 笔记 | 可转化选题 | 状态 |
|---|---|---|
| Pi-Durable-设计.md（255L） | Pi Durable——已用 | ✅ `2026-10-09-pi-durable` |
| Durable-Agent-失败模式逐场景分析.md（210L） | durable 失败模式逐场景 | ⚠️ 部分已用（见 `content/2026-10-09-pi-durable/`） |
| Pi-vs-OpenCode-vs-DeepSeekHarness-底层设计对比.md（183L） | **三家 harness 底层设计对比**（组合模型 / 会话真相 / 耐久性 / 工具面 / 多表面五轴；pi vs opencode vs dsh；CVE-2026-22812 安全教训） | ❌ 未写 · **强候选** |
| 工具边界契约层-谁给replay-safe背书.md（165L） | **谁给 `replay: "safe"` 背书**（MCP annotations 是 hint 不是 contract；五类背书机制；pi-durable 挡得住「崩溃重放型重复」挡不住「模型重新规划型重复」） | ❌ 未写 · **强候选** |
| Rust是否是AI-Agent时代的最佳语言.md（467L） | Rust 是不是 agent 时代最佳语言（实测 $-成本、编译器战争、DHH/Elixir 对照） | ⚠️ 部分已写（`2026-10-09-dhh-campfire-rust` 同源材料） |

## 四、使用规则（硬性）

1. **选题/大纲阶段必查**：先读 `AI-Chats/_INDEX.md` 扫一遍标题 → 有对口的再读原笔记 → 写进 `docs/content-matrix.md` 对应组的候选表。
2. **一条笔记 ≠ 一篇文章**：笔记是研读记录（含大量 AI 归纳与批判），要按账号公式蒸馏成「反常识 + 数字 + 为什么」，不是搬运。**一篇笔记通常能出 1–3 篇，也可能一篇都出不了。**
3. **作者原生观点逐字保留**：`我的判断` / `我的理解边界` / `苏格拉底问题` / 第一人称批注 → 原声槽素材，逐字入稿（规则同 `docs/writing-flow.md`；禁止 AI 改写或「优化」措辞）。
4. **笔记里的「未核实」必须复核**：笔记自己标了 `未逐段核对`、`二次报道`、`未独立验证` 的地方，**写稿前必须打开一手原文**——笔记是二手的，且 `docs/data-freshness.md` 要求实时验证。
5. **论文 ID 直接复用**：笔记 frontmatter 的 `paper_ids:` / `source:` 就是参考资料出处，可直接进文末参考列表（带日期）。
6. **写完回写**：笔记转化出的文章发布后，在 `docs/content-matrix.md` 对应行标 ✅ + 文章路径，避免重复选题。
7. **不要提交 vault 内容进本仓库**：笔记在项目外，属作者私人资料；正文引用即可，**禁止把 vault 路径/原文整篇搬进 `content/`**（`docs/` 内只留选题映射与出处）。

## 五、来源与坑

- ⚠️ 旧 vault 在未挂载的 NTFS 分区上，**读之前先确认 `ls /media/skyscribe/Windows` 有东西**，不要因为路径不存在就断言"笔记丢了"。
- ⚠️ 全盘搜索 `比价`/`价格` 等关键词找笔记是**无效路径**——笔记标题是论文名/课程名，不是主题词。找笔记请用 `_INDEX.md` 或按 frontmatter 的 `topic:` / `tags:` 检索。
- 笔记的 `个人/` 目录当前为空；`学习/未命名.md` 含**明文 API 密钥**（`sk-X...`），**不要读取、不要引用、不要提交**。
