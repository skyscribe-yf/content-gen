# 预训练实验：文章佐证材料索引

本目录只保留写作与复现所需的证据，不包含原始语料和模型 checkpoint。

## 可直接引用的结果

- 设备：NVIDIA GeForce RTX 4090 D，24,564 MiB 显存，驱动 570.124.04。
- 软件：Python 3.11.15、PyTorch 2.7.0+cu126、CUDA 12.6、tokenizers 0.23.1。
- 语料：50 万篇中文故事；训练集 490,011 篇，固定验证集 9,989 篇；读取字段 `story_zh`。
- 数据版本：`98547ad8ca1205e2e5ce564343cb78f972f72ffa`。
- 语料 SHA-256：`05e04c04f33b05dd23e16c5ce8a702559153ade4b2da7763a235e60056a4a9fb`。
- 模型：33,739,776 参数，8,192 词表，256 token 上下文。
- 训练：两段合计 90 分钟纯训练时间；24,112 个优化步；约 790,102,016 个训练 token。
- 最佳固定验证 PPL：50.7278，step 24,100。

## 时间轴说明

续训进程的 `elapsed_seconds` 从零重新计时，不能与首段直接相加。写文章时应使用 `evidence/metrics-combined-training-time.csv` 中的 `combined_training_elapsed_seconds`：

- 首段：0–60 分钟。
- 续训：60–90 分钟。
- 不包括 BPE/数据编码和 checkpoint 重载时间。

## 文件导航

- `artifacts/loss-curves.png`：按全局 step 绘制的训练/验证 PPL。
- `artifacts/evidence/loss-curves-combined-training-time.png`：按合并训练时间绘制的曲线，文章优先使用。
- `artifacts/metrics.jsonl`：242 个全量指标点。
- `artifacts/evidence/metrics-combined-training-time.csv`：适合表格/绘图的合并时间轴数据。
- `artifacts/generations.jsonl`：23 个里程碑、92 条固定提示词生成记录；可比较从随机词片段到叙事模板与复读的变化。
- `artifacts/summary.json`、`artifacts/summary-60m.json`：两阶段摘要。
- `artifacts/evidence/initial-run-config.json`、`continuation-run-config.json`：精确超参数。
- `artifacts/evidence/gpu.csv`、`nvidia-smi-full.txt`、`software.json`、`system-info.txt`、`pip-freeze.txt`：硬件与软件佐证。
- `artifacts/evidence/TinyStories_all_data_zh.tar.gz.sha256`：原始语料校验和；语料本体未下载。
- `logs/`：正式首段、续训及其 90 秒监控日志。
- `runtime-scripts/`：实际执行的训练、续训、指标分析与续训启动脚本。
