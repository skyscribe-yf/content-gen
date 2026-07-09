"""
内容生成 Pipeline — 从选题到多平台内容骨架

用法:
  python3 content-pipeline.py create --topic gradient_descent
  python3 content-pipeline.py create --topic moe_route --type fusion
  python3 content-pipeline.py create --topic e1_deepseek_r1 --type eval
  python3 content-pipeline.py list-topics
  python3 content-pipeline.py list-content
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TOPICS_FILE = ROOT / "topics" / "topic-tracker.md"
TEMPLATES_DIR = ROOT / "templates"
CONTENT_DIR = ROOT / "content"
MANIM_DIR = ROOT / "manim"

# ── 选题数据库（与topic-tracker.md同步） ──

TOPICS = {
    # 原理篇
    "gradient_descent": {
        "title": "梯度下降：蒙着眼下山",
        "series": "深度学习基础",
        "type": "principle",
        "math_concept": "梯度=最速下降方向",
        "algorithm": "GD/SGD/Adam",
        "analogy": "蒙着眼下山，每一步往最陡的方向走",
    },
    "linear_algebra": {
        "title": "线性代数：向量是方向，矩阵是变换",
        "series": "线性代数直觉",
        "type": "principle",
        "math_concept": "线性变换",
        "algorithm": "矩阵乘法/特征分解",
        "analogy": "向量是箭头，矩阵是变形器",
    },
    "attention": {
        "title": "Transformer注意力：谁在听谁说话",
        "series": "大模型原理",
        "type": "principle",
        "math_concept": "加权求和+缩放点积",
        "algorithm": "注意力矩阵计算",
        "analogy": "开会时你只关注跟自己相关的人",
    },
    "probability": {
        "title": "概率论：不确定性就是信息",
        "series": "概率论直觉",
        "type": "principle",
        "math_concept": "概率分布",
        "algorithm": "采样算法",
        "analogy": "不确定性不是无知，是还没收到的信息",
    },
    "backprop": {
        "title": "反向传播：功劳怎么分",
        "series": "深度学习基础",
        "type": "principle",
        "math_concept": "链式法则",
        "algorithm": "自动微分",
        "analogy": "公司出了问题，从CEO一层层追责到基层",
    },
    "loss_function": {
        "title": "损失函数：打分标准决定学习方向",
        "series": "深度学习基础",
        "type": "principle",
        "math_concept": "交叉熵/MSE",
        "algorithm": "梯度计算",
        "analogy": "考试评分标准决定了你怎么复习",
    },
    "softmax": {
        "title": "Softmax：温和的投票",
        "series": "深度学习基础",
        "type": "principle",
        "math_concept": "指数归一化",
        "algorithm": "数值稳定实现",
        "analogy": "把任意分数变成温和的概率投票",
    },
    "convolution": {
        "title": "卷积：用放大镜看图",
        "series": "计算机视觉",
        "type": "principle",
        "math_concept": "卷积运算",
        "algorithm": "卷积前向传播",
        "analogy": "拿放大镜在图上滑动，每处提取特征",
    },
    "diffusion": {
        "title": "扩散模型：从噪声中还原真相",
        "series": "生成式AI",
        "type": "principle",
        "math_concept": "随机微分方程",
        "algorithm": "DDPM/DDIM采样",
        "analogy": "把模糊的老照片一步步修复清晰",
    },
    "bayes": {
        "title": "贝叶斯定理：看到新证据后改变想法",
        "series": "概率论直觉",
        "type": "principle",
        "math_concept": "后验概率",
        "algorithm": "贝叶斯推断",
        "analogy": "先有偏见，看到证据后修正偏见",
    },
    "embedding": {
        "title": "嵌入：把意思变成数字",
        "series": "大模型原理",
        "type": "principle",
        "math_concept": "向量空间映射",
        "algorithm": "Embedding查找表",
        "analogy": "给每个词发一张身份证，相近的词住隔壁",
    },
    "entropy": {
        "title": "信息熵：不确定性有多大",
        "series": "信息论直觉",
        "type": "principle",
        "math_concept": "信息熵",
        "algorithm": "交叉熵计算",
        "analogy": "越意外的事，信息量越大",
    },
    "chain_rule": {
        "title": "链式法则：复合变化的一根绳子",
        "series": "微积分直觉",
        "type": "principle",
        "math_concept": "链式法则",
        "algorithm": "计算图构建",
        "analogy": "拔一根绳子，整条链都会动",
    },
    "cross_entropy": {
        "title": "交叉熵：两个世界的差距",
        "series": "信息论直觉",
        "type": "principle",
        "math_concept": "KL散度",
        "algorithm": "KL散度计算",
        "analogy": "你的认知和真相差多远",
    },
    "residual": {
        "title": "残差连接：走捷径",
        "series": "深度学习进阶",
        "type": "principle",
        "math_concept": "梯度流",
        "algorithm": "Skip connection",
        "analogy": "不绕远路，直接抄近道",
    },
    # 融合篇
    "moe_route": {
        "title": "为什么DeepSeek比GPT便宜10倍？",
        "series": "AI算法实测",
        "type": "fusion",
        "math_concept": "MoE稀疏激活",
        "algorithm": "Top-K路由",
        "analogy": "公司不需要每次开会都请所有顾问",
        "eval_design": "4模型跑MoE推理对比",
        "hotspot": "DeepSeek/Mixtral",
    },
    "attention_decay": {
        "title": "AI的注意力会走神吗？",
        "series": "AI算法实测",
        "type": "fusion",
        "math_concept": "注意力衰减",
        "algorithm": "长上下文注意力计算",
        "analogy": "书太长，读到后面忘了前面",
        "eval_design": "长文本问答衰减实测",
        "hotspot": "100K上下文模型",
    },
    "diffusion_steps": {
        "title": "AI画图为什么需要1000步？",
        "series": "AI算法实测",
        "type": "fusion",
        "math_concept": "扩散过程",
        "algorithm": "DDPM/DDIM采样",
        "analogy": "修复照片，修1000次比修10次清晰",
        "eval_design": "不同步数出图质量对比",
        "hotspot": "新图像模型",
    },
    "rlhf": {
        "title": "AI怎么学会说人话？",
        "series": "AI算法实测",
        "type": "fusion",
        "math_concept": "策略梯度",
        "algorithm": "PPO/GRPO",
        "analogy": "训练小狗，做对了给奖励",
        "eval_design": "RLHF前后输出对比",
        "hotspot": "新RLHF模型",
    },
    "temperature": {
        "title": "为什么AI会一本正经胡说？",
        "series": "AI算法实测",
        "type": "fusion",
        "math_concept": "概率采样",
        "algorithm": "Temperature/Top-p",
        "analogy": "温度高=大胆瞎说，温度低=保守复读",
        "eval_design": "不同温度输出对比",
        "hotspot": "幻觉问题",
    },
    "cot": {
        "title": "AI做数学题为什么总算错？",
        "series": "AI算法实测",
        "type": "fusion",
        "math_concept": "符号推理",
        "algorithm": "CoT/思维链",
        "analogy": "一步一步想比直接猜答案靠谱",
        "eval_design": "数学推理benchmark",
        "hotspot": "o1/R1推理模型",
    },
    "multitask": {
        "title": "一个模型怎么同时会写诗和写代码？",
        "series": "AI算法实测",
        "type": "fusion",
        "math_concept": "多任务学习",
        "algorithm": "LoRA/Adapter",
        "analogy": "一个人考了驾照又考了律师证",
        "eval_design": "微调前后能力对比",
        "hotspot": "开源微调",
    },
    "kv_cache": {
        "title": "AI的记忆有多大？",
        "series": "AI算法实测",
        "type": "fusion",
        "math_concept": "KV缓存",
        "algorithm": "注意力缓存机制",
        "analogy": "记住前面说的话，不用每次重新读",
        "eval_design": "不同缓存策略速度对比",
        "hotspot": "长上下文优化",
    },
}


def _get_template(type_name: str) -> str:
    """读取对应模板"""
    template_map = {
        "principle": "weixin-article.md",
        "fusion": "weixin-article.md",
        "eval": "weixin-article.md",
    }
    path = TEMPLATES_DIR / template_map.get(type_name, "weixin-article.md")
    if path.exists():
        return path.read_text()
    return ""


def _generate_draft(topic: dict, type_name: str) -> str:
    """根据选题信息生成初稿骨架"""
    title = topic["title"]
    analogy = topic["analogy"]
    math_concept = topic["math_concept"]
    algorithm = topic["algorithm"]
    series = topic["series"]

    if type_name == "principle":
        draft = f"""# {title}

## 🎯 驱动问题

为什么{analogy}？答案藏在{math_concept}里。

## 💡 直觉解释

{analogy}。

<!-- 用Manim动画截图/信息图强化 -->
<!-- 点出关键insight -->

## 📐 数学原理

{math_concept}的形式化：

<!-- 核心公式 + 一句话解释 -->
<!-- 标出算法实现的关键点 -->

## 🔧 算法实现

```python
# {algorithm}的最小实现
# 代码结构对应数学公式

# TODO: 填写核心代码（不超过40行）
```

## 🌍 应用场景

- 应用1
- 应用2
- 应用3

## 📌 一句话总结

{title.split('：')[0] if '：' in title else title}的本质是{analogy}，数学上是{math_concept}。

---

> 系列：{series}
> 类型：原理篇
"""

    elif type_name == "fusion":
        eval_design = topic.get("eval_design", "")
        hotspot = topic.get("hotspot", "")
        draft = f"""# {title}

## 🎯 驱动问题

{hotspot}——{analogy}？这背后是{math_concept}在起作用。

## 💡 直觉解释

{analogy}。

## 📐 数学原理

{math_concept}：

<!-- 核心公式 + 算法关键点 -->

## 🔧 算法实现

```python
# {algorithm}的最小实现
# 关键决策点：[待标注，实测会验证]

# TODO: 填写核心代码
```

## 🧪 模型实测

{eval_design}

| 模型 | 正确性 | 算法复杂度 | 关键差异 | API成本 |
|------|--------|-----------|---------|---------|
| GPT-4o | | | | |
| Claude | | | | |
| DeepSeek | | | | |
| Gemini | | | | |

<!-- 跑 eval_benchmark.py 填入数据 -->

## 🔄 回扣原理

<!-- 实测差异 → 数学解释 → 回答驱动问题 -->

## 📌 一句话总结

{title.split('？')[0] if '？' in title else title}？因为{math_concept}，实测告诉我们[关键发现]。

---

> 系列：{series}
> 类型：融合篇
> 热点：{hotspot}
"""

    else:  # eval
        draft = f"""# {title}

## 🎯 一句话结论

<!-- 50字内给出结论 -->

## 📊 核心数据

| 模型 | 价格(input) | 价格(output) | 上下文 | 备注 |
|------|------------|-------------|--------|------|
| | | | | |

<!-- 从 price-pipeline.py 获取 -->

## 🧪 实测案例

### 案例1：{algorithm}

| 模型 | 结果 | 耗时 | 成本 |
|------|------|------|------|
| | | | |

### 案例2：
<!-- TODO -->

### 案例3：
<!-- TODO -->

## 🔄 原理回扣

<!-- 一句话：为什么XX翻车/胜出？→ {math_concept} -->

## 🔗 完整原理

→ [{series}原理详解](链接)

---

> 类型：评测篇
> 触发：热点当天
"""

    return draft


def _generate_xhs_config(topic: dict, type_name: str) -> dict:
    """生成小红书信息图配置"""
    title = topic["title"]
    analogy = topic["analogy"]
    math_concept = topic["math_concept"]
    algorithm = topic["algorithm"]

    if type_name == "principle":
        cards = [
            {"type": "knowledge", "title": title, "subtitle": analogy,
             "items": [f"直觉：{analogy}", f"数学：{math_concept}", f"算法：{algorithm}"],
             "filename": "01-cover.jpg"},
            {"type": "knowledge", "title": "直觉理解", "subtitle": analogy,
             "items": ["要点1", "要点2", "要点3"],
             "filename": "02-intuition.jpg"},
            {"type": "knowledge", "title": "数学原理", "subtitle": math_concept,
             "items": ["公式1 + 解释", "公式2 + 解释"],
             "filename": "03-math.jpg"},
            {"type": "steps", "title": "算法实现", "subtitle": algorithm,
             "items": ["步骤1", "步骤2", "步骤3"],
             "filename": "04-algorithm.jpg"},
            {"type": "knowledge", "title": "应用场景",
             "items": ["场景1", "场景2", "场景3"],
             "filename": "05-applications.jpg"},
            {"type": "knowledge", "title": "总结",
             "items": [f"{title} = {analogy} + {math_concept}"],
             "filename": "06-summary.jpg"},
        ]
    elif type_name == "fusion":
        cards = [
            {"type": "knowledge", "title": title, "subtitle": analogy,
             "items": [f"直觉：{analogy}", f"算法：{algorithm}", "实测：谁做得好？"],
             "filename": "01-cover.jpg"},
            {"type": "knowledge", "title": "直觉理解", "subtitle": analogy,
             "items": ["要点1", "要点2"],
             "filename": "02-intuition.jpg"},
            {"type": "knowledge", "title": "数学原理", "subtitle": math_concept,
             "items": ["核心公式", "关键项解释"],
             "filename": "03-math.jpg"},
            {"type": "steps", "title": "算法实现", "subtitle": algorithm,
             "items": ["步骤1", "步骤2", "关键决策点"],
             "filename": "04-algorithm.jpg"},
            {"type": "comparison", "title": "模型实测对比",
             "concept_a": "GPT-4o", "concept_b": "DeepSeek",
             "points_a": ["特征1", "特征2"], "points_b": ["特征1", "特征2"],
             "filename": "05-eval.jpg"},
            {"type": "knowledge", "title": "回扣原理",
             "items": ["实测发现1", "数学解释1", "结论"],
             "filename": "06-loopback.jpg"},
        ]
    else:  # eval
        cards = [
            {"type": "data", "title": title, "big_number": "10x",
             "data_source": "价格对比", "sub_data": ["GPT: $X", "DeepSeek: $Y"],
             "filename": "01-data.jpg"},
            {"type": "comparison", "title": "能力对比",
             "concept_a": "GPT-4o", "concept_b": "DeepSeek",
             "points_a": ["✅ 正确", "快"], "points_b": ["✅ 正确", "便宜"],
             "filename": "02-compare.jpg"},
            {"type": "knowledge", "title": "关键发现",
             "items": ["发现1", "发现2", "原理回扣"],
             "filename": "03-findings.jpg"},
        ]

    return {
        "series_title": title,
        "theme": "purple",
        "output_dir": "",  # 运行时填充
        "cards": cards,
    }


def _generate_bilibili_outline(topic: dict, type_name: str) -> str:
    """生成B站脚本大纲"""
    title = topic["title"]
    analogy = topic["analogy"]
    math_concept = topic["math_concept"]
    algorithm = topic["algorithm"]

    if type_name == "principle":
        return f"""# B站脚本：{title}

## 时间线

| 时间 | 内容 | 视觉 |
|------|------|------|
| 0:00-0:15 | 驱动问题 | 标题动画 |
| 0:15-1:00 | 直觉：{analogy} | Manim动画 |
| 1:00-2:30 | 数学：{math_concept} | 公式动画 |
| 2:30-3:30 | 算法：{algorithm} | 代码动画 |
| 3:30-3:50 | 实测预告 | 过渡 |
| 3:50-4:30 | 应用场景 | 图片轮播 |
| 4:30-5:00 | 回扣+总结 | 闭环动画 |

## 旁白草稿

### 开头
{analogy}——这背后是{math_concept}。

### 直觉
<!-- TODO: 3-4句话类比 -->

### 数学
<!-- TODO: 逐步推导 -->

### 算法
<!-- TODO: 代码讲解 -->

### 总结
一句话：{title} = {analogy} + {math_concept}。
"""

    elif type_name == "fusion":
        return f"""# B站脚本：{title}

## 时间线

| 时间 | 内容 | 视觉 |
|------|------|------|
| 0:00-0:15 | 驱动问题 | 热点截图 |
| 0:15-1:15 | 直觉+数学 | Manim动画 |
| 1:15-2:15 | 算法实现 | 代码动画 |
| 2:15-3:45 | 模型实测 | 分屏对比 |
| 3:45-4:30 | 回扣原理 | 闭环动画 |
| 4:30-5:00 | 总结+引导 | 下期预告 |

## 旁白草稿

### 开头
{topic.get('hotspot', '')}——{analogy}？

### 实测段
<!-- TODO: 4个模型输出对比 -->

### 回扣
<!-- TODO: 实测差异 → 数学解释 -->
"""

    else:  # eval
        return f"""# B站脚本：{title}（评测快报）

## 时间线（2-3分钟）

| 时间 | 内容 | 视觉 |
|------|------|------|
| 0:00-0:10 | 开头 | 模型名+核心数据 |
| 0:10-1:30 | 实测对比 | 分屏 |
| 1:30-2:00 | 原理回扣 | 一句话 |
| 2:00-2:30 | 引导 | 下期预告 |

## 旁白草稿

<!-- TODO: 快速对比讲解 -->
"""


def create(topic_name: str, type_name: str, report_date: str):
    """创建一期完整内容包"""
    if topic_name not in TOPICS:
        print(f"❌ 未知选题: {topic_name}")
        print(f"可用选题: {', '.join(sorted(TOPICS.keys()))}")
        return

    topic = TOPICS[topic_name]
    # 如果命令行没指定type，用选题自带的type
    if type_name == "principle" and topic.get("type") != "principle":
        type_name = topic.get("type", "principle")

    # 创建目录
    dir_name = f"{report_date}-{topic_name}"
    content_dir = CONTENT_DIR / dir_name
    xhs_dir = content_dir / "xiaohongshu"
    bili_dir = content_dir / "bilibili"
    assets_dir = content_dir / "assets"

    for d in [xhs_dir, bili_dir, assets_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 生成各文件
    # 1. 初稿
    draft = _generate_draft(topic, type_name)
    (content_dir / "draft.md").write_text(draft)

    # 2. 公众号版（初稿基础上加发布格式）
    (content_dir / "weixin.md").write_text(draft)

    # 3. 小红书配置
    xhs_config = _generate_xhs_config(topic, type_name)
    xhs_config["output_dir"] = str(xhs_dir)
    (xhs_dir / "cards.json").write_text(
        json.dumps(xhs_config, ensure_ascii=False, indent=2)
    )

    # 4. B站脚本大纲
    bili_outline = _generate_bilibili_outline(topic, type_name)
    (bili_dir / "script.md").write_text(bili_outline)

    # 5. Manim场景骨架
    manim_template = f"""\"\"\"
Manim场景：{topic['title']}
系列：{topic['series']}
\"\"\"
from manim import *
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from base_scene import BaseScene


class {topic_name.replace('_', '').title()}Scene(BaseScene):
    \"\"\"{topic['title']}——{topic['analogy']}\"\"\"

    def construct(self):
        # 1. 驱动问题
        self.show_title("{topic['title'].split('：')[0] if '：' in topic['title'] else topic['title']}", 
                        "{topic['analogy']}")

        # 2. 直觉
        self.show_intuition("{topic['analogy']}")

        # 3. 数学原理
        # self.show_formula(r"...", "解释")

        # 4. 算法可视化
        # TODO: 用Manim动画展示{topic['algorithm']}

        # 5. 实测（融合篇）
        # TODO: 分屏展示模型输出

        # 6. 回扣
        # self.show_intuition("实测验证了...")
"""
    (bili_dir / "manim_scene.py").write_text(manim_template)

    # 输出摘要
    print(f"\n✅ 内容包已创建: {content_dir}/")
    print(f"")
    print(f"  📝 draft.md          — 初稿骨架")
    print(f"  📱 weixin.md         — 公众号版（待完善）")
    print(f"  🖼️  xiaohongshu/     — 小红书配置")
    print(f"     cards.json        — 信息图配置（make xhs TOPIC={topic_name} 出图）")
    print(f"  🎬 bilibili/         — B站素材")
    print(f"     script.md         — 脚本大纲")
    print(f"     manim_scene.py    — Manim场景骨架")
    print(f"  📦 assets/           — 素材目录")
    print(f"")
    print(f"💡 下一步:")
    print(f"  1. 完善 draft.md（填入具体内容）")
    print(f"  2. 跑评测: make eval BENCH={topic_name}")
    print(f"  3. 出小红书图: make xhs TOPIC={topic_name}")
    print(f"  4. 制作Manim动画: 编辑 bilibili/manim_scene.py")


def list_topics():
    """列出所有可用选题"""
    print(f"\n📋 可用选题\n")

    by_type = {"principle": [], "fusion": []}
    for name, topic in TOPICS.items():
        by_type.get(topic.get("type", "principle"), by_type["principle"]).append((name, topic))

    for type_name, label in [("principle", "📖 原理篇"), ("fusion", "🔗 融合篇")]:
        items = by_type.get(type_name, [])
        if items:
            print(f"\n{label}:")
            for name, topic in items:
                print(f"  {name:<25s} {topic['title']}")


def list_content():
    """列出已创建的内容"""
    if not CONTENT_DIR.exists():
        print("暂无内容")
        return

    dirs = sorted([d for d in CONTENT_DIR.iterdir() if d.is_dir() and d.name[0].isdigit()])
    if not dirs:
        print("暂无内容")
        return

    print(f"\n📦 已创建内容 ({len(dirs)} 期)\n")
    for d in dirs:
        files = list(d.rglob("*"))
        file_count = len([f for f in files if f.is_file()])
        print(f"  {d.name}/  ({file_count} 文件)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="内容生成Pipeline")
    sub = parser.add_subparsers(dest="command")

    create_p = sub.add_parser("create", help="创建内容包")
    create_p.add_argument("--topic", required=True, help="选题名称")
    create_p.add_argument("--type", default="principle",
                          choices=["principle", "fusion", "eval"],
                          help="内容类型")
    create_p.add_argument("--date", default=date.today().isoformat(), help="日期")

    sub.add_parser("list-topics", help="列出可用选题")
    sub.add_parser("list-content", help="列出已创建内容")

    args = parser.parse_args()

    if args.command == "create":
        create(args.topic, args.type, args.date)
    elif args.command == "list-topics":
        list_topics()
    elif args.command == "list-content":
        list_content()
    else:
        parser.print_help()
