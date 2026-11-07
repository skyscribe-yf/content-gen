"""变异体评分：给一份实现的源码 + 一份测试文件，数出多少个变异体被杀死。"""
import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

MUTANTS = [
    ("M01", "天的系数写成 8640", '"d": 86400', '"d": 8640'),
    ("M02", "小时差一秒", '"h": 3600', '"h": 3601'),
    ("M03", "分钟的系数写成 6", '"m": 60', '"m": 6'),
    ("M04", "秒的系数写成 0", '"s": 1', '"s": 0'),
    ("M05", "去掉大小写不敏感", 're.compile(r"(\\d+)([dhms])", re.IGNORECASE)', 're.compile(r"(\\d+)([dhms])")'),
    ("M06", "空串返回 0 而不是报错", '    if not s:\n        raise ValueError("empty duration")', '    if not s:\n        return 0'),
    ("M07", "只取最后一段（覆盖而非累加）", "total += int(num) * _UNITS[u]", "total = int(num) * _UNITS[u]"),
    ("M08", "重复单位不再报错", '        if u in seen:\n            raise ValueError("repeated unit")\n', ""),
    ("M09", "长度校验放宽（多字符也放行）", 'if len(consumed) != len(s.replace(" ", ""))', 'if len(consumed) > len(s.replace(" ", ""))'),
    ("M10", "返回浮点而不是整数", "    return total", "    return float(total)"),
    ("M11", "所有单位都按秒算", "_UNITS[u]", '_UNITS["s"]'),
    ("M12", "每段数值加一", "int(num) * _UNITS[u]", "(int(num) + 1) * _UNITS[u]"),
    ("M13", "只去掉右侧空白", "s = text.strip()", "s = text.rstrip()"),
    ("M14", "没有有效片段时返回 0", 'raise ValueError("no valid tokens")', "return 0"),
    ("M15", "单位大小写不再归一", "u = unit.lower()", "u = unit"),
]

RUNNER = [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"]


def run_once(src_file: pathlib.Path, test_file: pathlib.Path) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        shutil.copy(src_file, d / "parse_duration.py")
        shutil.copy(test_file, d / "test_parse_duration.py")
        p = subprocess.run(RUNNER, cwd=d, capture_output=True, text=True, timeout=180)
        return p.returncode, (p.stdout + p.stderr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="实现目录，内含 parse_duration.py")
    ap.add_argument("--test", required=True, help="测试文件")
    ap.add_argument("--dump", default=None, help="把变异体落盘到该目录")
    args = ap.parse_args()

    src_dir = pathlib.Path(args.src)
    src_file = src_dir / "parse_duration.py"
    test_file = pathlib.Path(args.test)
    base = src_file.read_text()

    rc, out = run_once(src_file, test_file)
    print(f"BASELINE rc={rc}")
    if rc != 0:
        print(out[-3000:])

    killed, survived = [], []
    for mid, desc, old, new in MUTANTS:
        if base.count(old) != 1:
            raise SystemExit(f"{mid} 锚点匹配 {base.count(old)} 次，需恰好 1 次：{desc}")
        mutated = base.replace(old, new)
        with tempfile.TemporaryDirectory() as tmp:
            mf = pathlib.Path(tmp) / "parse_duration.py"
            mf.write_text(mutated)
            if args.dump:
                dd = pathlib.Path(args.dump) / mid
                dd.mkdir(parents=True, exist_ok=True)
                (dd / "parse_duration.py").write_text(mutated)
                (dd / "DESC.txt").write_text(desc)
            rc, _ = run_once(mf, test_file)
        (killed if rc != 0 else survived).append(mid)

    print(f"KILLED {len(killed)}/{len(MUTANTS)}: {' '.join(killed)}")
    print(f"SURVIVED {len(survived)}/{len(MUTANTS)}: {' '.join(survived)}")


if __name__ == "__main__":
    main()
