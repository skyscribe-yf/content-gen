---
title: "FP8训练：残缺数字怎么练出顶级模型"
author: "数解AI"
date: "2026-08-08"
type: "解密篇"
series: "DeepSeek 技术解密"
keywords: ["FP8 训练", "混合精度", "E4M3", "量化", "outlier", "在线量化", "DeepSeek-V3", "DeepSeek-V4"]
illustration_type: "infographic / comparison / framework"
illustration_density: "per-section"
illustration_style: "notion editorial"
illustration_palette: "warm graphite with cyan accents"
illustration_backend: "zairouter / gpt-image-2"
illustration_count: 5
---

# FP8训练：残缺数字怎么练出顶级模型

## 文章定位

- 本篇是 DeepSeek 技术解密系列的新一篇，主线是 **V3 的 FP8 混合精度工程探索**（DeepSeek-V3 Technical Report §3.3 + 附录 B）；V4 作为「继承 + 升级」证据（FP8 Dispatch + BF16 Combine、KV 混合存储、FP4 QAT 复用 FP8 框架）。
- 兑现 mHC 篇（08-07）文末预告：「下一篇拆 FP8 训练怎么用残缺数字练出顶级模型」——标题与预告原文同频。
- 兑现 Muon 篇（08-06）两处 FP8 伏笔：① Newton-Schulz 迭代在 BF16 精度下数值稳定，与 FP8 低精度路径兼容；② MoE 梯度用随机舍入压到 BF16 再跨 rank 同步，通信量减半——两处都在本篇「低精度通信/低精度优化器状态」语境下回响。
- 主线冲突：**残缺数字的工程美学**——FP8 只有 8 位（1 符号 + 4 指数 + 3 尾数），动态范围窄、精度糙，outlier 随时毁掉整块量化；DeepSeek 凭什么敢用，而且全链路只用 E4M3？
- 数学深度：双深潜。① **一个 outlier 毁掉整张图**——per-tensor vs per-group 量化误差的定量对比（scale 被 outlier 挤压，正常值精度雪崩）；② **在线量化**——Amax 在线估计 vs delayed 历史推断，量化网格跟着数据实时缩放。
- 实验：Outlier 量化误差对比（128×128 张量注入 outlier，per-tensor vs per-group 1×128 相对误差表 + E4M3 量化台阶可视化），标注「机制演示，不是官方性能基准」。
- 下一篇预告：FP4 QAT（08-09，专家权重再省一半）。

## 核心结论

1. 1.6T 参数的 V4-Pro 在 BF16 下总显存 10+ TB，远超单卡；FP8 让 GEMM 存储和计算各减半，且 H 系列 Tensor Core 原生支持——**省内存省带宽是硬刚需，不是可选项**。
2. FP8 的算术：E4M3（1+4+3）动态范围窄（约 ±240~448）但精度高；E5M2（1+5+2）范围宽（约 ±57344）但精度糙。尾数 = 区间内台阶数，指数 = 能到多高。
3. **深潜①**：per-tensor 量化用一个全局 scale，一个 outlier 就把正常值的量化台阶全部挤压，相对误差雪崩；per-group（激活 1×128 tile / 权重 128×128 block）让 outlier 只毁自己所在的组。
4. **深潜②**：delayed quantization 用历史 max 推断 scale，分布漂移时失配；online quantization 用当前块的 Amax 实时算 scale——量化网格跟着数据走，无需 loss scaling。
5. **E4M3 全用**：DeepSeek 特意不用「Fprop E4M3 / 反传 E5M2」的 hybrid 方案（NVIDIA 等 prior work 的做法），全链路只用 E4M3——靠 fine-grained 量化撑动态范围，用「组内共享指数」的思路化解范围窄的问题。
6. **H800 陷阱**：H800 的 FP8 GEMM 累加精度只有约 14 bit（远低于 FP32），内积维度 K 大时误差累积；DeepSeek 用 N_C=128 间隔把部分和提升到 CUDA cores 做 FP32 累加。
7. **三重保险**：FP32 master weights（防量化漂移）+ FP32 累加（高精度求和）+ 选择性高精度（embedding/output head/MoE gating/normalization/attention 保持 BF16）——「该省的省，不该省的绝不省」。
8. **0.25% 实证**：FP8 vs BF16 对照实验（16B/1.33T tokens + 230B/0.9T tokens），相对误差 < 0.25%，loss 曲线几乎重合。
9. V4 继承：FP8 Dispatch + BF16 Combine（MoE 通信）、KV 混合存储（RoPE 维 BF16 + 其余 FP8，缓存近减半）、FP4 QAT 无损反量化「复用现有 FP8 训练框架不加修改」——FP8 是 V4 训练体系的底座。

## 标题与摘要

### 标题

**FP8训练：残缺数字怎么练出顶级模型**

（教程攻略型 ⭐⭐⭐⭐：术语「FP8训练」前置，搜一搜命中长尾词；「残缺数字」承接 mHC 预告原文；17 字 ≤ 22；单术语 FP8）

### 摘要

FP8 训练的每个数字只有 8 位——1 个符号位、4 个指数位、3 个尾数位，被戏称为「残缺数字」。1.6T 参数的模型在 BF16 下要占 10TB+ 显存，不用 FP8 根本装不下。可 8 位数字精度够吗？一个 outlier 就可能毁掉整块量化，H800 的 FP8 累加还只有 14 位精度。DeepSeek 用三招化解：分组量化、在线缩放、E4M3 全链路统一格式，把 FP8 训练的差距压到 0.25% 以内。（含 2 个搜索关键词：FP8 训练、混合精度）

## 正文结构

### 0. 开头：十个数字凑不出一个精确值（约 250 字）

开场画面：把 1 到 10 之间的每个数都记在 3 个「台阶」上——8.6 只能写成 9，4.2 只能写成 4。8 位浮点数就是这种「残缺算术」：每个数字都带着 ±6% 左右的舍入误差。可 DeepSeek 偏偏用这种残缺数字练出了 1.6T 参数的顶级模型。悬念：残缺数字怎么扛住万亿级训练？

### 1. 回应弧线：mHC 篇的预告，今天兑现（约 300 字）

- 引 mHC 篇结尾预告原文：「下一篇拆 FP8 训练怎么用残缺数字练出顶级模型。」
- 校准 1（机制归属）：FP8 训练的机制细节几乎全部来自 **V3 技术报告**（arXiv:2412.19437 §3.3 + 附录 B）——V4 报告只顺带提 FP8（FP8 FLOPs 度量、FP4 QAT 复用 FP8 框架）；V4 是继承者，不是发明者。诚实标注。
- 校准 2（上篇衔接）：Muon 篇提到 Newton-Schulz 在 BF16 下数值稳定、MoE 梯度随机舍入压 BF16 通信减半——这两处今天都会在「低精度存储与通信」里回响。
- 本篇回答：8 位数字怎么表示、误差从哪来、DeepSeek 用什么工程手段把误差压到 0.25%。

### 2. FP8 的算术：8 位能装下什么（约 450 字）

- 浮点表示：符号 1 位 + 指数 4 位 + 尾数 3 位（E4M3）；对比 BF16（1+8+7）、FP32（1+8+23）。
- 两种 FP8 格式：E4M3（动态范围约 ±240~448，3 位尾数精度高）/ E5M2（约 ±57344，2 位尾数粗糙）。表：| 格式 | 指数/尾数 | 动态范围 | 精度 | 谁用 |
- 直觉：尾数 = 区间内台阶数（E4M3 每区间 8 个台阶，E5M2 只有 4 个）；指数 = 数轴能伸多高。
- 量化就是「找最近的台阶」：$Q(x) = \text{round}(x / s) \cdot s$，scale $s$ 决定台阶间距。
- 关键认识：**台阶数是死的（8 或 4），scale 是活的**——scale 定得好，残缺数字也能逼近精确值。这就引出量化粒度（第 3 节）。

### 3. 深潜①：一个 outlier 毁掉整张图（约 600 字，数学深潜①）

- per-tensor：整块张量共用一个 scale，$s = \max|x| / X_{\max}$。
- 场景：一个 outlier（比如 200）混进大多在 ±1 附近的权重——scale 被 outlier 拉到 200/448≈0.45，正常值 ±1 只占 2 个台阶，精度全毁。
- 定量：相对误差公式（给推导）：

$$\text{MRE} = \frac{\|Q(x) - x\|_2}{\|x\|_2}$$

- 数字示例：正常值 ±1 的量化误差从 ~0.6% 飙到 ~30%（举例，experiment.py 验证后定稿）；outlier 只占 1/16384 个元素，却毁掉整块。
- per-group 解药：激活按 1×128 tile（per token per 128 channels）、权重按 128×128 block 分组，每组独立 scale——outlier 只毁自己所在的组，其余组毫发无损。
- 深潜②预告：分组粒度还带来第二个红利——scale 是实时算的，不依赖历史，这就是在线量化（第 4 节）。

### 4. 深潜②：量化网格跟着数据走（约 550 字，数学深潜②）

- 传统做法（NVIDIA delayed quantization）：用历史迭代的 max 推断当前 scale——分布漂移时 scale 失配，误差累积。
- DeepSeek 的 online quantization：对每个 1×128 tile / 128×128 block 实时算 Amax，当场定 scale、当场量化。
- 对比表：| 维度 | delayed | online |
- 几何直觉：量化网格是活的——数据分布变宽，网格自动拉开；变窄，网格自动收紧。像相机自动曝光。
- 澄清：这不是「loss scaling」——loss scaling 是梯度缩放防下溢（NVIDIA 体系）；DeepSeek 用在线 Amax 估算，**不需要 loss scaling**（校准第 9 课笔记的误记）。
- 代价：online 量化要在 HBM 里读一遍算 Amax 再写回，多一次内存往返——论文 §3.5.2 建议未来芯片把 FP8 cast 和 TMA 融合成一次操作（硬件建议，一笔带过）。

### 5. E4M3 全用：把 E5M2 丢进历史（约 450 字）

- prior work（NVIDIA/微软等）惯例：Fprop 用 E4M3（要精度）、反传用 E5M2（梯度范围大）——hybrid 双格式。
- DeepSeek 反其道：**全链路只用 E4M3**。为什么敢？因为 fine-grained 量化让每个小分组共享指数位，动态范围的短板被分组缩放补上了。
- 表：| 方案 | 前向 | 反传 | 理由 |
- 单格式的红利：实现简单、不用来回转换、硬件路径统一（只有一种 FP8 格式，Tensor Core 利用率高）。
- 校准：第 9 课笔记写「E4M3 前向 / E5M2 反向」是错的——那是 NVIDIA 的做法，DeepSeek 特意不用。（正文不点名笔记，只写事实：V3 报告明确「we adopt the E4M3 format on all tensors」）

### 6. H800 的 14 位累加陷阱（约 500 字）

- 想当然：FP8 乘法 + FP32 累加 = 安全。实测打脸：H800 的 FP8 GEMM 内部累加**只保留约 14 位**（远低于 FP32 的 24 位尾数），K 维度大时误差累积（K=4096 时初步实验可见明显退化）。
- 解法：N_C=128 间隔（等价 4 个 WGMMA），把部分和从 Tensor Cores 拷贝到 CUDA cores，乘上缩放因子后用 FP32 寄存器累加。
- 直觉：Tensor Core 快但「记性差」，CUDA core 慢但「记得准」——128 拍一结算，快与准折中。
- 为什么是 128：论文实验结论，4 个 WGMMA 是「精度显著提升且开销可忽略」的最小间隔。
- 校准：第 9 课笔记写「H100」——V3 报告明确是 **H800**（H800 FP8 GEMM 累加 14 bit 是报告的观测对象）。

### 7. 三重保险：该省的省，不该省的绝不省（约 450 字）

- 三层保险表：| 保护层 | 机制 | 防什么 |
  - master weights FP32：优化器维护的权重永远是精确版，量化漂移不累积
  - FP32 累加：GEMM 内部（经 N_C=128 提升）高精度求和
  - 选择性高精度：embedding、output head、MoE gating、normalization、attention 保持 BF16/FP32——这些算子对精度敏感或计算占比小，省了不划算
- 该省的：Linear（GEMM）占计算 ~80% → FP8；激活缓存 FP8（attention 后 Linear 的输入激活用自定义 E5M6 格式、SwiGLU 输入 FP8 缓存 + 反传重算）——低精度存储省内存。
- 补充：低精度通信（MoE up-projection 前激活量化 FP8 再 dispatch，All-to-All 减半）——衔接 Muon 篇「MoE 梯度随机舍入 BF16」。
- 哲学总结：FP8 不是「全面降精度」，是「精度按敏感度分层」——敏感算子一个都不能省，算力大户一个都不放过。

### 8. 0.25% 的实证：残缺数字没有拖后腿（约 400 字）

- V3 附录 B 对照实验：两个尺度（16B 总参 / 1.33T tokens；230B 总参 / 0.9T tokens），FP8 vs BF16 loss 曲线几乎重合，**相对误差 < 0.25%**。
- 强调口径：这是 DeepSeek 自家对照实验（自家框架、自家实现），不是第三方基准——但作为「FP8 可行」的机制演示足够有力。
- 为什么 0.25% 可行：随机舍入的无偏性（量化误差是零均值噪声，大数定律下互相抵消，只减速不偏航）+ 三重保险兜底。
- 校准：第 9 课笔记写「<0.1%（V4）/ <0.5%（V3）」——V3 原文是 **< 0.25%**，以此为准。

### 9. V4 继承：FP8 成了底座（约 450 字 + 1 表）

- V4 报告证据（逐项核对原文）：
  - FP8 FLOPs 度量：1M 上下文下 V4-Pro 单 token 计算量仅 V3.2 的 27%（以 FP8 FLOPs 计）——FP8 是官方口径的计算单位
  - MoE 通信：FP8 Dispatch + BF16 Combine（V3 低精度通信的延续）
  - KV 混合存储：RoPE 维 BF16 + 其余 FP8，缓存近减半（衔接 K=V 篇）
  - FP4 QAT：「FP4→FP8 无损反量化（E4M3 比 E2M1 多 2 个指数位）……整个 QAT 管线直接复用现有 FP8 训练框架，不加任何修改」——FP8 框架是 V4 训练体系的底座
- 表：V4 全链路拼图：mHC（结构层）+ Muon（优化器）+ FP8（数值层）+ FP4（后训练压缩）。
- 结尾预告：FP8 省了一半，FP4 再省一半——下篇拆 **FP4 量化感知训练**（专家权重 + CSA indexer QK path 全 FP4，指数位再砍 2 个，怎么保持 99.7% recall？）

### 10. 回扣与结尾（约 250 字）

回扣开头：十个数字凑不出一个精确值——可当每个数字的误差都是零均值噪声时，万亿次计算里它们互相抵消，只留下 0.25% 的差距。残缺数字的美学不是「每个数字都准」，而是「整体误差可控」。8 位数字练出顶级模型，靠的不是奇迹，是把该省的省、不该省的绝不省的工程判断。

下一篇预告：FP4——指数位再砍 2 个，8 位变 4 位，专家权重再省一半。

开放式问题：如果每个数字都能省一半位宽，你觉得下一个该被「省」的组件是什么？评论区聊聊你的取舍。

## 配图计划

1. `00-cover.png`：封面标题「FP8训练：残缺数字怎么练出顶级模型」；画面：一排 8 个小格子（1 符号 + 4 指数 + 3 尾数）组成一个「残缺数字」，旁边一支精确的数字被「台阶」取代，暗示量化——残缺数字照样拼出完整模型；不出现未经核验的数字。
2. `01-fp8-format.png`：E4M3 vs E5M2 表示数轴对比（两条数轴，E4M3 台阶多但短，E5M2 台阶少但长）；对应第 2 节。
3. `02-outlier-scale.png`：一个 outlier 毁掉整张图（per-tensor 单 scale 被 outlier 拉高、正常值挤压 vs per-group 只毁局部）；对应第 3 节。
4. `03-online-quant.png`：online vs delayed 量化网格对比（网格跟着数据分布实时缩放 vs 历史 scale 失配）；对应第 4 节。
5. `04-triple-insurance.png`：三重保险图（master FP32 / FP32 累加 / 选择性高精度，三层盾牌）+ 0.25% 大数字；对应第 7/8 节。

## 来源与核验口径

- [DeepSeek-V3 Technical Report, arXiv:2412.19437](https://arxiv.org/abs/2412.19437)（2024.12）：§3.3 FP8 训练（混合精度框架、fine-grained 量化、N_C=128 累加提升、E4M3 全用、online quantization、低精度存储与通信）、§3.5 硬件建议、附录 B 对照实验（16B/230B 两尺度，相对误差 < 0.25%）、H800 14-bit 累加——全部已逐项核对原文。
- [DeepSeek-V4 Technical Report, arXiv:2606.19348](https://arxiv.org/abs/2606.19348)（2026）：FP8 FLOPs 度量（27%）、FP8 Dispatch + BF16 Combine、KV 混合存储（RoPE BF16 + 其余 FP8）、FP4 QAT 复用 FP8 框架（§5.2.1）。
- IEEE FP8 格式规范：E4M3/E5M2 动态范围数值（写作时按规范定稿：E4M3 max=448 / 受限集 240，E5M2 max=57344）。
- Obsidian 笔记《DeepSeek 第 9 课 · FP8 训练》（2026-04-25）：框架参考；**6 处与原文出入已校准**（E4M3 全用、1×128/128×128 粒度、online quantization、H800、0.25%），正文以论文原文为准。
- mHC 篇（08-07）文末预告原文 + Muon 篇（08-06）两处 FP8 伏笔：弧线兑现对象。
- 实验：`experiment.py` 自包含 NumPy 实现（outlier 量化误差对比），仅机制演示。

## 自检清单

- [ ] 标题 ≤22 字（17 字）、单术语 FP8、关键词前置、过 6 条自检；「残缺数字」「练出顶级模型」与 mHC 预告原文同频。
- [ ] 开头有回应弧线小节，引用 mHC 预告原文，校准机制归属（V3 发明、V4 继承）。
- [ ] 主线始终围绕「残缺数字怎么扛住训练」展开，不散。
- [ ] 数学深潜①（outlier 量化误差）有完整推导 + 数字示例；深潜②（online vs delayed）有对比表 + 几何直觉。
- [ ] 公式 6-10 组，独立公式 `$$...$$`、内联 `$...$`。
- [ ] 0.25% 实验数据标注「DeepSeek 自家对照实验，非第三方基准」；16B/230B 口径明确。
- [ ] 实验标注「机制演示，不是官方性能基准」。
- [ ] 文末有 3-5 个话题标签、合集导航、FP4 预告、开放式问题、关注引导。
- [ ] E4M3/E5M2 动态范围数值按 IEEE 规范定稿并标注。
- [ ] FP4 QAT 只作预告不展开（独立主题 08-09）。
- [ ] 正文禁词：无「钩子」「伏笔」。
