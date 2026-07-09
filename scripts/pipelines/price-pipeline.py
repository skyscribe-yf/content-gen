"""
API 价格监控 Pipeline

用法:
  python3 price-pipeline.py show          # 显示当前价格对比表
  python3 price-pipeline.py diff          # 显示最近变动
  python3 price-pipeline.py update        # 交互式更新价格
  python3 price-pipeline.py report        # 生成Markdown报告到content/
  python3 price-pipeline.py set <model_id> <input> <output>  # 直接设置价格

数据源: scripts/pipelines/prices.json（手动维护）
价格单位: USD per 1M tokens
"""
import json
import sys
from datetime import date
from pathlib import Path

PRICES_PATH = Path(__file__).parent / "prices.json"
HISTORY_PATH = Path(__file__).parent / "prices_history.json"
CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "price-reports"


def _load_prices() -> dict:
    return json.loads(PRICES_PATH.read_text())


def _save_prices(data: dict):
    PRICES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _load_history() -> list:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text())
    return []


def _save_history(history: list):
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2))


def _snapshot_current() -> dict:
    """拍一份当前价格的快照，用于历史对比"""
    data = _load_prices()
    return {
        "date": data["updated"],
        "models": {m["id"]: {"input": m["input"], "output": m["output"]}
                   for m in data["models"]}
    }


def show():
    """显示价格对比表"""
    data = _load_prices()
    models = data["models"]

    # 按input价格排序
    models.sort(key=lambda m: m["input"])

    print(f"\n💰 API 价格对比（更新于 {data['updated']}）")
    print(f"   单位: USD / 1M tokens\n")

    # 表头
    print(f"{'模型':<20s} {'提供商':<10s} {'输入':>8s} {'输出':>8s} {'输出/输入':>8s} {'上下文':>8s} {'备注'}")
    print("─" * 85)

    for m in models:
        ratio = f"{m['output']/m['input']:.1f}x" if m['input'] > 0 else "-"
        note = m.get('note', '')
        print(f"{m['id']:<20s} {m['provider']:<10s} "
              f"${m['input']:>6.2f}  ${m['output']:>6.2f}  "
              f"{ratio:>7s}  {m['context']:>7s}  {note}")

    # 性价比排行
    print(f"\n🏆 性价比排行（input价格最低）:")
    for i, m in enumerate(models[:5], 1):
        print(f"  {i}. {m['id']} — ${m['input']}/1M input")

    # 最贵排行
    print(f"\n💸 最贵排行（output价格最高）:")
    by_output = sorted(models, key=lambda m: m['output'], reverse=True)
    for i, m in enumerate(by_output[:5], 1):
        print(f"  {i}. {m['id']} — ${m['output']}/1M output")


def diff():
    """显示最近价格变动"""
    history = _load_history()
    if len(history) < 2:
        print("暂无历史数据，至少需要两次快照。运行 price-update 保存当前快照。")
        return

    prev = history[-2]["models"]
    curr = history[-1]["models"]

    print(f"\n📊 价格变动：{history[-2]['date']} → {history[-1]['date']}\n")

    changes = []
    for mid, prices in curr.items():
        if mid in prev:
            pi_diff = prices["input"] - prev[mid]["input"]
            po_diff = prices["output"] - prev[mid]["output"]
            if abs(pi_diff) > 0.001 or abs(po_diff) > 0.001:
                changes.append((mid, pi_diff, po_diff, prices, prev[mid]))

    if not changes:
        print("✅ 无变动")
        return

    for mid, pi_d, po_d, curr_p, prev_p in changes:
        pi_pct = (pi_d / prev_p["input"] * 100) if prev_p["input"] else 0
        po_pct = (po_d / prev_p["output"] * 100) if prev_p["output"] else 0
        pi_arrow = "📈" if pi_d > 0 else "📉"
        po_arrow = "📈" if po_d > 0 else "📉"
        print(f"  {mid}:")
        print(f"    input:  ${prev_p['input']:.2f} → ${curr_p['input']:.2f} {pi_arrow} {pi_pct:+.1f}%")
        print(f"    output: ${prev_p['output']:.2f} → ${curr_p['output']:.2f} {po_arrow} {po_pct:+.1f}%")

    # 生成选题建议
    print(f"\n🎯 选题建议:")
    for mid, pi_d, po_d, _, _ in changes:
        if pi_d < 0 or po_d < 0:
            print(f"  → {mid} 降价了！适合写评测快报 + 成本原理分析")
        else:
            print(f"  → {mid} 涨价了！适合写替代方案对比")


def update():
    """交互式更新价格"""
    data = _load_prices()

    # 先保存历史快照
    history = _load_history()
    history.append(_snapshot_current())
    _save_history(history)

    print("📝 更新API价格（直接回车跳过，保持原值）\n")

    for m in data["models"]:
        print(f"\n── {m['id']} ({m['provider']}) ──")
        print(f"  当前: input=${m['input']}, output=${m['output']}")

        new_input = input(f"  新input价格 [{m['input']}]: ").strip()
        new_output = input(f"  新output价格 [{m['output']}]: ").strip()

        if new_input:
            try:
                m["input"] = float(new_input)
            except ValueError:
                print("  ⚠️ 无效数字，跳过")
        if new_output:
            try:
                m["output"] = float(new_output)
            except ValueError:
                print("  ⚠️ 无效数字，跳过")

    data["updated"] = str(date.today())
    _save_prices(data)
    print(f"\n✅ 价格已更新 ({data['updated']})")


def set_price(model_id: str, input_price: float, output_price: float):
    """直接设置某个模型的价格"""
    data = _load_prices()

    # 保存历史
    history = _load_history()
    history.append(_snapshot_current())
    _save_history(history)

    for m in data["models"]:
        if m["id"] == model_id:
            m["input"] = input_price
            m["output"] = output_price
            data["updated"] = str(date.today())
            _save_prices(data)
            print(f"✅ {model_id}: input=${input_price}, output=${output_price}")
            return

    print(f"❌ 未找到模型: {model_id}")
    print(f"可用: {', '.join(m['id'] for m in data['models'])}")


def report():
    """生成Markdown价格报告"""
    data = _load_prices()
    models = sorted(data["models"], key=lambda m: m["input"])

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    out = CONTENT_DIR / f"{date.today()}-price-report.md"

    lines = [
        f"# 💰 API 价格对比 ({data['updated']})",
        f"",
        f"单位: USD / 1M tokens",
        f"",
        f"| 模型 | 提供商 | 输入 | 输出 | 上下文 | 备注 |",
        f"|------|--------|------|------|--------|------|",
    ]

    for m in models:
        note = m.get("note", "")
        lines.append(
            f"| {m['id']} | {m['provider']} | "
            f"${m['input']:.2f} | ${m['output']:.2f} | "
            f"{m['context']} | {note} |"
        )

    # 性价比分析
    lines.append("")
    lines.append("## 🏆 性价比排行")
    lines.append("")
    for i, m in enumerate(models[:5], 1):
        lines.append(f"{i}. **{m['id']}** — ${m['input']}/1M input ({m['provider']})")

    # 变动检测
    history = _load_history()
    if len(history) >= 2:
        prev = history[-2]["models"]
        curr = history[-1]["models"]
        changes = []
        for mid, prices in curr.items():
            if mid in prev:
                pi_d = prices["input"] - prev[mid]["input"]
                po_d = prices["output"] - prev[mid]["output"]
                if abs(pi_d) > 0.001 or abs(po_d) > 0.001:
                    changes.append((mid, pi_d, po_d))

        if changes:
            lines.append("")
            lines.append("## 📊 最近变动")
            lines.append("")
            for mid, pi_d, po_d in changes:
                direction = "📉 降价" if pi_d < 0 or po_d < 0 else "📈 涨价"
                lines.append(f"- **{mid}**: {direction} (input {pi_d:+.2f}, output {po_d:+.2f})")

    out.write_text("\n".join(lines))
    print(f"✅ 报告已保存: {out}")


if __name__ == "__main__":
    cmds = {
        "show": show,
        "diff": diff,
        "update": update,
        "report": report,
    }

    if len(sys.argv) < 2:
        show()
        sys.exit()

    cmd = sys.argv[1]

    if cmd == "set":
        if len(sys.argv) != 5:
            print("用法: price-pipeline.py set <model_id> <input_price> <output_price>")
            sys.exit(1)
        set_price(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
    elif cmd in cmds:
        cmds[cmd]()
    else:
        print(f"未知命令: {cmd}")
        print(f"可用: {', '.join(cmds.keys())}, set")
