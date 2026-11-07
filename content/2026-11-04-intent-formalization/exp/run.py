"""跑四个场景：A1/A2 用正确实现，B1/B2 用带 bug 的实现。"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent
RUNS = ROOT / "runs"

BASE = """下面是一个 Python 项目里的工具函数（parse_duration.py 全文）。请为它补一套单元测试。

硬性要求：
1. 测试文件名 test_parse_duration.py，导入方式必须是 `from parse_duration import parse_duration`
2. 用 pytest 写法，普通 assert 即可，不需要 mock、不需要 fixture
3. {goal}
4. 只输出测试文件的完整内容，放在一个 ```python 代码块里，不要任何解释

parse_duration.py:
```python
{src}
```
"""

GOAL_COVER = "测试要尽量完整，覆盖率尽量高"
GOAL_KILL = (
    "你的目标是让这套测试能抓住真实的错误。假设有人把这段实现改错一行——"
    "改错单位系数、改错边界比较方向、漏掉大小写归一、改错空输入或重复单位的处理——"
    "你的测试应该能发现。写完请自检：逐个列出你预判可能被改错的地方，确认每一处都有测试覆盖"
)

SCENARIOS = {
    "A1": ("src_reference", GOAL_COVER),
    "A2": ("src_reference", GOAL_KILL),
    "B1": ("src_bug_sign", GOAL_COVER),
    "B2": ("src_bug_repeat", GOAL_COVER),
}

MODEL = {"pro": "deepseek/deepseek-v4-pro", "flash": "deepseek/deepseek-v4.1-flash"}


def call_pi(model: str, prompt: str) -> str:
    cmd = [
        "pi", "-p", "--no-session", "--no-context-files", "--no-tools",
        "--no-skills", "--no-prompt-templates",
        "--provider", "commandcode", "--model", model, prompt,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if p.returncode != 0:
        raise SystemExit(f"pi failed rc={p.returncode}: {p.stderr[-500:]}")
    return p.stdout


def extract(out: str) -> str:
    blocks = re.findall(r"```(?:python|py)?\n(.*?)```", out, re.S)
    return (blocks[-1] if blocks else out).strip() + "\n"


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "A1,A2,B1,B2"
    tag = sys.argv[2] if len(sys.argv) > 2 else "pro"
    for name in which.split(","):
        src_dir, goal = SCENARIOS[name]
        src = (ROOT / src_dir / "parse_duration.py").read_text()
        prompt = BASE.format(goal=goal, src=src.rstrip())
        out = call_pi(MODEL[tag], prompt)
        dest = RUNS / f"{name}.{tag}"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "raw.md").write_text(out)
        (dest / "test_parse_duration.py").write_text(extract(out))
        (dest / "SOURCE").write_text(src_dir)
        print(f"{name}.{tag}: {len(out)} chars -> {dest}/test_parse_duration.py")


if __name__ == "__main__":
    main()
