"""
模型评测脚本骨架 —— 数学×算法×评测 闭环验证

用途：让多个模型实现同一个AI算法，对比正确性、复杂度、成本
输出：JSON结果 + Markdown对比表（可直接粘贴到文章）

环境变量（从项目根 .env 读取）：
  OPENAI_API_KEY       — OpenAI (GPT-4o等)
  OPENAI_BASE_URL      — 可选，自定义endpoint
  DEEPSEEK_API_KEY     — DeepSeek
  DEEPSEEK_BASE_URL    — 默认 https://api.deepseek.com
  ANTHROPIC_API_KEY    — Claude（通过兼容接口）

用法：
  # 跑单个benchmark
  python eval_benchmark.py --bench gradient_descent

  # 跑全部
  python eval_benchmark.py --all

  # 只跑指定模型
  python eval_benchmark.py --bench softmax --models gpt-4o deepseek-r1

  # 输出Markdown表格
  python eval_benchmark.py --bench moe_route --format md
"""
import argparse
import asyncio
import json
import os
import time
from pathlib import Path

try:
    from openai import AsyncOpenAI
except ImportError:
    import sys
    sys.exit("需要 openai: pip install openai")


# ── .env 加载 ──

def _load_dotenv():
    start = Path(__file__).resolve().parent
    for d in [start, *start.parents]:
        env_path = d / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))
            return

_load_dotenv()


# ── 模型配置 ──

MODELS = {
    "gpt-4o": {
        "client": lambda: AsyncOpenAI(),
        "model": "gpt-4o",
        "price_per_1k": 0.0025,  # input, 粗略
    },
    "gpt-4o-mini": {
        "client": lambda: AsyncOpenAI(),
        "model": "gpt-4o-mini",
        "price_per_1k": 0.00015,
    },
    "deepseek-r1": {
        "client": lambda: AsyncOpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        ),
        "model": "deepseek-reasoner",
        "price_per_1k": 0.00055,
    },
    "deepseek-v3": {
        "client": lambda: AsyncOpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        ),
        "model": "deepseek-chat",
        "price_per_1k": 0.00027,
    },
    "claude-sonnet": {
        "client": lambda: AsyncOpenAI(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
        ),
        "model": "claude-3-5-sonnet-20241022",
        "price_per_1k": 0.003,
    },
}


# ── Benchmark 定义 ──
# 每个benchmark = 一个AI算法实现任务
# prompt设计原则：让模型实现算法，不告诉它关键决策点，看它自己能不能做对

BENCHMARKS = {
    "gradient_descent": {
        "name": "梯度下降",
        "series": "深度学习基础",
        "math_concept": "梯度=最速下降方向",
        "prompt": """用Python实现梯度下降算法，要求：
1. 目标函数 f(x) = x² + 2x + 1
2. 从 x=3 开始
3. 学习率 0.1
4. 迭代20步
5. 打印每步的x值和f(x)
只输出代码，不要解释。""",
        "check": "验证最终x是否接近-1.0（理论极小值点）",
        "key_decision": "学习率选择、停止条件、数值稳定",
    },
    "softmax": {
        "name": "Softmax",
        "series": "深度学习基础",
        "math_concept": "指数归一化",
        "prompt": """用Python实现softmax函数，要求：
1. 输入是一个numpy数组
2. 处理大数值的数值稳定性问题
3. 输出概率之和应为1.0
4. 用以下输入测试：[1.0, 2.0, 3.0] 和 [1000.0, 1001.0, 1002.0]
只输出代码和测试结果。""",
        "check": "第二个测试用例是否正确处理（数值稳定性）",
        "key_decision": "是否减去max再做exp",
    },
    "attention": {
        "name": "注意力机制",
        "series": "大模型原理",
        "math_concept": "加权求和+缩放点积",
        "prompt": """用Python实现Scaled Dot-Product Attention，要求：
1. 输入 Q, K, V 矩阵（numpy）
2. attention = softmax(QK^T / sqrt(d_k)) V
3. d_k 是K的维度
4. 用随机矩阵测试：seq_len=4, d_k=8, d_v=6
只输出代码和测试结果。""",
        "check": "是否除以sqrt(d_k)缩放、输出维度是否正确",
        "key_decision": "缩放因子、矩阵乘法顺序",
    },
    "moe_route": {
        "name": "MoE路由",
        "series": "大模型原理",
        "math_concept": "稀疏激活+top-k选择",
        "prompt": """用Python实现MoE（Mixture of Experts）的路由算法，要求：
1. 4个expert，每个是一个简单的线性层
2. 门控函数：计算输入与每个expert的亲和度分数
3. Top-2路由：只激活分数最高的2个expert
4. 输出 = 加权求和（权重=softmax后的top-2分数）
5. 用随机输入测试
只输出代码和测试结果。""",
        "check": "是否只激活top-k（不是全量）、权重是否归一化",
        "key_decision": "top-k选择 vs 全量计算、负载均衡",
    },
    "cross_entropy": {
        "name": "交叉熵",
        "series": "信息论直觉",
        "math_concept": "两个分布的差距",
        "prompt": """用Python实现交叉熵损失函数，要求：
1. 输入：预测概率分布p和真实分布q（one-hot）
2. H(q, p) = -Σ q_i * log(p_i)
3. 处理log(0)的数值问题（加epsilon）
4. 测试：正确预测 vs 错误预测的损失对比
只输出代码和测试结果。""",
        "check": "是否加epsilon防log(0)、正确预测时损失是否接近0",
        "key_decision": "epsilon处理、数值稳定",
    },
    "beam_search": {
        "name": "Beam Search",
        "series": "大模型原理",
        "math_concept": "贪心搜索的折中",
        "prompt": """用Python实现Beam Search解码，要求：
1. 假设词表大小=5，序列长度=4
2. beam_width=2
3. 每步用随机概率模拟模型输出
4. 返回得分最高的2条序列
只输出代码和结果。""",
        "check": "是否保留beam_width个候选、得分计算是否正确",
        "key_decision": "候选保留策略、得分归一化",
    },
}


# ── 评测执行 ──

async def run_one(model_name: str, prompt: str) -> dict:
    """让一个模型跑一个benchmark"""
    cfg = MODELS[model_name]
    client = cfg["client"]()
    t0 = time.time()
    try:
        resp = await client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,  # 确定性输出，便于对比
            max_tokens=2048,
        )
        elapsed = time.time() - t0
        content = resp.choices[0].message.content
        tokens = resp.usage
        cost = (tokens.prompt_tokens * cfg["price_per_1k"] / 1000
                + tokens.completion_tokens * cfg["price_per_1k"] * 2 / 1000)

        return {
            "model": model_name,
            "content": content,
            "time": round(elapsed, 1),
            "prompt_tokens": tokens.prompt_tokens,
            "completion_tokens": tokens.completion_tokens,
            "cost": round(cost, 4),
            "error": None,
        }
    except Exception as e:
        return {
            "model": model_name,
            "content": "",
            "time": round(time.time() - t0, 1),
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cost": 0,
            "error": str(e),
        }


async def run_benchmark(bench_name: str, model_names: list[str]) -> dict:
    """跑一个benchmark的所有模型"""
    bench = BENCHMARKS[bench_name]
    print(f"\n{'='*60}")
    print(f"📊 {bench['name']}（{bench['series']}）")
    print(f"   数学概念：{bench['math_concept']}")
    print(f"   关键决策点：{bench['key_decision']}")
    print(f"{'='*60}")

    tasks = [run_one(m, bench["prompt"]) for m in model_names]
    results = await asyncio.gather(*tasks)

    return {
        "benchmark": bench_name,
        "name": bench["name"],
        "math_concept": bench["math_concept"],
        "key_decision": bench["key_decision"],
        "check": bench["check"],
        "results": results,
    }


# ── 输出格式 ──

def format_md(bench_result: dict) -> str:
    """生成Markdown对比表，可直接粘贴到文章"""
    b = bench_result
    lines = [
        f"### 🧪 {b['name']}实测",
        f"",
        f"**数学概念**：{b['math_concept']}",
        f"**关键决策点**：{b['key_decision']}",
        f"**验证标准**：{b['check']}",
        f"",
        f"| 模型 | 耗时 | Token数 | 成本 | 状态 |",
        f"|------|------|---------|------|------|",
    ]

    for r in b["results"]:
        status = "❌ 错误" if r["error"] else "✅ 完成"
        lines.append(
            f"| {r['model']} | {r['time']}s | "
            f"{r['prompt_tokens']}+{r['completion_tokens']} | "
            f"${r['cost']} | {status} |"
        )

    lines.append("")
    lines.append("<!-- 详细输出见下方，手动标注正确性后删除此注释 -->")
    for r in b["results"]:
        lines.append(f"\n#### {r['model']}")
        lines.append(f"```python\n{r['content']}\n```")

    return "\n".join(lines)


def format_json(all_results: list[dict]) -> str:
    """JSON格式，供后续分析"""
    return json.dumps(all_results, ensure_ascii=False, indent=2)


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(description="模型评测：AI算法实现对比")
    parser.add_argument("--bench", help="单个benchmark名称")
    parser.add_argument("--all", action="store_true", help="跑全部benchmark")
    parser.add_argument("--models", nargs="+", default=list(MODELS.keys()),
                        help="指定模型（默认全部）")
    parser.add_argument("--format", default="md", choices=["md", "json"],
                        help="输出格式")
    parser.add_argument("--output", help="输出文件路径")
    args = parser.parse_args()

    if not args.bench and not args.all:
        parser.print_help()
        print("\n可用benchmark:", ", ".join(BENCHMARKS.keys()))
        return

    bench_names = list(BENCHMARKS.keys()) if args.all else [args.bench]
    for name in bench_names:
        if name not in BENCHMARKS:
            print(f"❌ 未知benchmark: {name}")
            print("可用:", ", ".join(BENCHMARKS.keys()))
            return

    # 过滤可用模型
    available = []
    for m in args.models:
        if m not in MODELS:
            print(f"⚠️ 未知模型: {m}，跳过")
            continue
        # 检查API key
        cfg = MODELS[m]
        try:
            client = cfg["client"]()
            available.append(m)
        except Exception:
            print(f"⚠️ {m} API key未配置，跳过")

    if not available:
        print("❌ 没有可用的模型，请检查 .env 中的 API key")
        return

    print(f"📋 将评测 {len(bench_names)} 个benchmark × {len(available)} 个模型")

    all_results = []
    for name in bench_names:
        result = asyncio.run(run_benchmark(name, available))
        all_results.append(result)

        # 实时输出
        if args.format == "md":
            print(format_md(result))
        else:
            for r in result["results"]:
                print(f"  {r['model']}: {r['time']}s, ${r['cost']}, "
                      f"{'❌ '+r['error'] if r['error'] else '✅'}")

    # 保存
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "md":
            out.write_text("\n\n---\n\n".join(format_md(r) for r in all_results))
        else:
            out.write_text(format_json(all_results))
        print(f"\n💾 已保存到 {args.output}")


if __name__ == "__main__":
    main()
