"""
评测 Pipeline — 跑benchmark + 生成报告 + 保存到content目录

封装 eval_benchmark.py，增加：
  - 自动保存到 content/eval-reports/
  - 生成可直接粘贴到文章的Markdown
  - 支持追加"手动标注"段（正确性判断需人工）

用法:
  python3 eval-pipeline.py run                          # 跑全部
  python3 eval-pipeline.py run --bench softmax           # 跑单个
  python3 eval-pipeline.py run --models gpt-4o deepseek-r1  # 指定模型
  python3 eval-pipeline.py annotate <report_path>        # 手动标注正确性
  python3 eval-pipeline.py list                          # 列出已有报告
  python3 eval-pipeline.py latest                        # 查看最新报告
"""
import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

EVAL_SCRIPT = Path(__file__).resolve().parent.parent / "eval_benchmark.py"
REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "eval-reports"


def run(bench: str, models: list[str] | None):
    """跑评测并保存报告"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()

    # 构建命令
    cmd = [sys.executable, str(EVAL_SCRIPT), "--format", "json"]
    if bench == "all":
        cmd.append("--all")
        outfile = REPORTS_DIR / f"{today}-all.json"
    else:
        cmd.extend(["--bench", bench])
        outfile = REPORTS_DIR / f"{today}-{bench}.json"

    if models:
        cmd.extend(["--models", *models])

    cmd.extend(["--output", str(outfile)])

    print(f"📊 跑评测: {bench}")
    print(f"   命令: {' '.join(cmd)}")
    print()

    # 执行
    result = subprocess.run(cmd, cwd=str(EVAL_SCRIPT.parent))
    if result.returncode != 0:
        print(f"❌ 评测失败 (exit code {result.returncode})")
        sys.exit(1)

    # 生成Markdown报告
    if outfile.exists():
        md_file = outfile.with_suffix(".md")
        data = json.loads(outfile.read_text())
        md = _generate_md(data, today)
        md_file.write_text(md)
        print(f"\n✅ 报告已保存:")
        print(f"   JSON: {outfile}")
        print(f"   MD:   {md_file}")
        print(f"\n💡 下一步: python3 eval-pipeline.py annotate {md_file}")
    else:
        print("⚠️ 无输出文件")


def _generate_md(data: list[dict] | dict, report_date: str) -> str:
    """从JSON结果生成Markdown报告"""
    # ponytail: data可能是list或单个dict
    if isinstance(data, dict):
        data = [data]

    lines = [
        f"# 🧪 模型评测报告 ({report_date})",
        f"",
    ]

    for bench in data:
        lines.append(f"## {bench.get('name', bench.get('benchmark', ''))}")
        lines.append(f"")
        lines.append(f"- **数学概念**: {bench.get('math_concept', '')}")
        lines.append(f"- **关键决策点**: {bench.get('key_decision', '')}")
        lines.append(f"- **验证标准**: {bench.get('check', '')}")
        lines.append(f"")

        # 对比表
        lines.append(f"| 模型 | 耗时 | Token(in+out) | 成本 | 状态 | 正确性 |")
        lines.append(f"|------|------|---------------|------|------|--------|")

        for r in bench.get("results", []):
            status = "❌ 错误" if r.get("error") else "✅ 完成"
            tokens = f"{r.get('prompt_tokens', 0)}+{r.get('completion_tokens', 0)}"
            lines.append(
                f"| {r['model']} | {r.get('time', '?')}s | "
                f"{tokens} | "
                f"${r.get('cost', 0):.4f} | {status} | ⬜ 待标注 |"
            )

        # 详细输出
        lines.append(f"")
        lines.append(f"<details>")
        lines.append(f"<summary>📋 详细输出</summary>")
        lines.append(f"")
        for r in bench.get("results", []):
            lines.append(f"### {r['model']}")
            lines.append(f"```python")
            lines.append(r.get("content", ""))
            lines.append(f"```")
            lines.append(f"")
        lines.append(f"</details>")

        # 回扣原理提示
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"**🔄 回扣原理提示**: 实测差异是否印证了数学原理？")
        lines.append(f"- [ ] 标注每个模型的正确性")
        lines.append(f"- [ ] 找出关键差异点")
        lines.append(f"- [ ] 用数学原理解释差异")
        lines.append(f"")

    return "\n".join(lines)


def annotate(report_path: str):
    """交互式标注报告中的正确性"""
    path = Path(report_path)
    if not path.exists():
        print(f"❌ 文件不存在: {path}")
        return

    content = path.read_text()
    print(f"📝 标注: {path.name}\n")

    # 简单替换：⬜ 待标注 → ✅/⚠️/❌
    markers = {
        "1": ("✅ 正确", "✅ 正确"),
        "2": ("⚠️ 部分正确", "⚠️ 部分"),
        "3": ("❌ 错误", "❌ 错误"),
        "s": ("跳过", None),
    }

    lines = content.split("\n")
    new_lines = []
    for line in lines:
        if "⬜ 待标注" in line:
            print(f"\n{line}")
            print("  1=✅正确  2=⚠️部分  3=❌错误  s=跳过")
            choice = input("  选择: ").strip().lower()
            if choice in markers and markers[choice][1]:
                line = line.replace("⬜ 待标注", markers[choice][1])
                print(f"  → {line}")
        new_lines.append(line)

    path.write_text("\n".join(new_lines))
    print(f"\n✅ 标注已保存: {path}")


def list_reports():
    """列出已有报告"""
    if not REPORTS_DIR.exists():
        print("暂无报告")
        return

    reports = sorted(REPORTS_DIR.glob("*.md"))
    if not reports:
        print("暂无报告")
        return

    print(f"\n📋 已有评测报告 ({len(reports)} 份):\n")
    for r in reports:
        size = r.stat().st_size
        print(f"  {r.name}  ({size // 1024}KB)")


def latest():
    """查看最新报告"""
    if not REPORTS_DIR.exists():
        print("暂无报告")
        return

    reports = sorted(REPORTS_DIR.glob("*.md"))
    if not reports:
        print("暂无报告")
        return

    latest_report = reports[-1]
    print(f"\n📄 最新报告: {latest_report.name}\n")
    # 只打印前50行
    lines = latest_report.read_text().split("\n")
    for line in lines[:50]:
        print(line)
    if len(lines) > 50:
        print(f"\n... (共 {len(lines)} 行，完整内容见 {latest_report})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="评测Pipeline")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="跑评测")
    run_p.add_argument("--bench", default="all", help="benchmark名称(all=全部)")
    run_p.add_argument("--models", nargs="+", help="指定模型")

    ann_p = sub.add_parser("annotate", help="标注正确性")
    ann_p.add_argument("report", help="报告文件路径")

    sub.add_parser("list", help="列出已有报告")
    sub.add_parser("latest", help="查看最新报告")

    args = parser.parse_args()

    if args.command == "run":
        run(args.bench, args.models)
    elif args.command == "annotate":
        annotate(args.report)
    elif args.command == "list":
        list_reports()
    elif args.command == "latest":
        latest()
    else:
        parser.print_help()
