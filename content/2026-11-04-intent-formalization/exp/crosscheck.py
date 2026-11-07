"""把 agent 写的测试拿去跑另一个实现，看它们在正确实现上会不会失败。"""
import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile


def run(src: pathlib.Path, test: pathlib.Path):
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        shutil.copy(src, d / "parse_duration.py")
        shutil.copy(test, d / "test_parse_duration.py")
        p = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider", "-rf"],
            cwd=d, capture_output=True, text=True, timeout=180,
        )
        return p.returncode, p.stdout + p.stderr


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True)
    ap.add_argument("--against", required=True, help="实现目录")
    args = ap.parse_args()
    rc, out = run(pathlib.Path(args.against) / "parse_duration.py", pathlib.Path(args.test))
    print(f"rc={rc}")
    print(out[-3000:])


if __name__ == "__main__":
    main()
