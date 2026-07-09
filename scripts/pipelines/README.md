# 🔄 Pipeline 使用指南

在 pi 中直接调用，一键跑通内容生产流程。

## 快速开始

```bash
make eval          # 跑模型评测，生成报告
make eval BENCH=softmax  # 跑单个benchmark
make price         # 查看API价格对比
make price-update  # 更新价格数据（需手动填入）
make content TOPIC=gradient_descent  # 生成一期完整内容
make xhs TOPIC=gradient_descent      # 只出小红书信息图
make hotspot       # 检查最近热点（新模型/调价）
make status        # 查看所有pipeline状态
```

## Pipeline 详情

### 1. eval — 模型评测

**触发**：新模型发布 / 写融合篇前 / 定期周跑

```bash
make eval                              # 跑全部benchmark
make eval BENCH=softmax                # 跑单个
make eval MODELS="gpt-4o deepseek-r1"  # 指定模型
```

**输出**：`content/eval-reports/YYYY-MM-DD-<bench>.md`

**耗时**：~5-10分钟（取决于模型数量和API速度）

---

### 2. price — API价格监控

**触发**：每周跑一次 / 重大调价新闻后

```bash
make price          # 查看当前价格对比表
make price-update   # 交互式更新价格（引导你填入最新价格）
make price-diff     # 只看最近变动
```

**输出**：终端表格 + `content/price-reports/YYYY-MM-DD.md`

**耗时**：<1秒（本地数据）

---

### 3. content — 内容生成

**触发**：选好题目后一键生成内容骨架

```bash
make content TOPIC=gradient_descent              # 生成完整内容包
make content TOPIC=moe_route TYPE=fusion         # 指定融合篇
make content TOPIC=e1_deepseek_r1 TYPE=eval      # 指定评测篇
```

**输出**：`content/YYYY-MM-DD-<topic>/` 目录，包含：
- `draft.md` — 初稿（基于模板填充）
- `weixin.md` — 公众号版（待你完善）
- `xiaohongshu/` — 小红书图+文案
- `bilibili/` — B站脚本+分镜
- `eval-report.md` — 评测数据（如适用）

**耗时**：<10秒（本地生成骨架）

---

### 4. hotspot — 热点检测

**触发**：每天跑一次 / 准备选题时

```bash
make hotspot        # 检查最近3天热点
```

**输出**：终端列出热点 + 对应选题建议

**耗时**：~30秒（抓取公开信息）

---

### 5. xhs — 小红书出图

**触发**：写完深度稿后出图

```bash
make xhs TOPIC=gradient_descent              # 用xhs_card.py本地出图
make xhs TOPIC=gradient_descent MODE=ai      # 用AI出图（需API key）
```

**输出**：`content/YYYY-MM-DD-<topic>/xiaohongshu/` 目录

**耗时**：本地<5秒，AI出图~2分钟

---

## 在 pi 中调用示例

直接告诉 pi：

> "跑一下softmax的评测"
> "生成梯度下降那期内容"
> "看看现在API价格"
> "检查最近有没有新模型发布"
> "出梯度下降的小红书图"

pi 会调用对应的 make 命令。
