# 📐 数学+AI科普 内容生产流水线

## 项目结构

```
weixin-post/
├── README.md                 # 本文件
├── 竞品分析.md                # 竞品分析报告
├── templates/                # 各平台内容模板
│   ├── weixin-article.md     # 公众号文章模板
│   ├── xiaohongshu-info.md   # 小红书信息图提示词模板
│   ├── bilibili-script.md    # B站视频脚本模板
│   └── zhihu-answer.md       # 知乎回答模板
├── manim/                    # Manim 动画模板
│   ├── base_scene.py         # 基础场景模板
│   ├── gradient_descent.py   # 梯度下降示例
│   └── neural_network.py     # 神经网络可视化示例
├── topics/                   # 选题库
│   └── topic-tracker.md      # 选题追踪表
├── content/                  # 已创作内容（按日期组织）
│   └── YYYY-MM-DD-主题名/    # 每期内容文件夹
│       ├── draft.md          # 初稿
│       ├── weixin.md         # 公众号版
│       ├── xiaohongshu/      # 小红书图+文案
│       ├── bilibili/         # B站脚本+分镜
│       └── assets/           # 图片/视频素材
└── scripts/
    └── new-topic.sh          # 新建选题脚手架
```

## 工作流概览

```
选题 → 深度稿(公众号) → 拆解为:
  ├→ 小红书信息图 (6-9张)
  ├→ B站 Manim 动画 (3-5min)
  └→ 知乎回答 (引流)
```

## 一期内容的生产步骤

### Step 1: 选题（5分钟）
- 从 `topics/topic-tracker.md` 选一个选题
- 或热点驱动：新模型/新论文→讲背后数学

### Step 2: 写深度稿（60-90分钟）
- 用 `templates/weixin-article.md` 模板
- 核心原则：**先直觉，再公式，最后代码**
- 控制在 1500-2000 字

### Step 3: 拆解为小红书信息图（30分钟）
- 用 `templates/xiaohongshu-info.md` 中的提示词模板
- 喂给 AI 生图工具，生成 6-9 张 3:4 竖版信息图
- 配 300 字文案 + 标签

### Step 4: 制作 B 站动画（60-120分钟）
- 用 `manim/` 下的模板
- 录制旁白（可 AI 配音）
- 控制在 3-5 分钟

### Step 5: 知乎引流（15分钟）
- 找相关问题，用 `templates/zhihu-answer.md` 模板
- 回答中引导关注公众号

### Step 6: 发布排期
- 公众号：周二/五早8点
- 小红书：周二/四/六晚7-9点
- B站：周六下午3点
- 知乎：发布后找问题回答

## 工具栈

| 用途 | 工具 | 成本 |
|------|------|------|
| 动画制作 | Manim Community | 免费 |
| 信息图生成 | `scripts/xhs_card.py`（本地Pillow） | 免费 |
| 信息图精修 | gpt-image-2（可选，文字渲染更强） | $0.2/张 |
| 文案写作 | Claude/GPT | 订阅制 |
| AI 配音 | 剪映 / Fish Audio | 免费/付费 |
| 视频剪辑 | 剪映 | 免费 |
| 封面设计 | `xhs_card.py` / Canva / gpt-image-2 | 免费/付费 |

## 图片生产方案

### 方案1：本地 Python 生成（推荐起步，免费）

```bash
# 单张卡片
python scripts/xhs_card.py \
  --title "梯度下降的直觉" \
  --subtitle "蒙着眼下山" \
  --items "梯度=坡度方向" "学习率=步子大小" \
  --theme purple --output card.jpg

# 批量生成系列（6-9张轮播）
python scripts/xhs_card.py --config content/example-series.json
```

4种卡片类型：
- `knowledge` — 编号要点列表（最常用）
- `comparison` — 左右对比（概念A vs 概念B）
- `steps` — 步骤教程（01/02/03编号）
- `data` — 大数字冲击（数据可视化）

3套配色：
- `purple` — 深紫+粉红（科技感）
- `dark_blue` — 深蓝+蓝绿（专业感）
- `warm` — 米色+橙色（亲切感）

### 方案2：gpt-image-2（可选，文字渲染95%+准确）

适合需要复杂排版/更多装饰元素的场景。
参考 `templates/xiaohongshu-info.md` 中的提示词模板，配合 API 调用。

### 生产流程

```
选题 → xhs_card.py 出骨架图 → 微调文案 → 发布
       ↑                       ↓
  JSON 配置              可选：gpt-image-2 精修
```
