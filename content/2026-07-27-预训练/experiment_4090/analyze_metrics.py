"""Summarize and plot metrics emitted by ``pretrain_4090.py``."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_metrics(metric_path: Path) -> list[dict[str, float | int]]:
    rows = [json.loads(line) for line in metric_path.read_text(encoding="utf-8").splitlines()]
    if not rows:
        raise ValueError("metrics file contains no rows")
    return rows


def summarize_metrics(metric_path: Path) -> dict[str, float | int]:
    rows = read_metrics(metric_path)
    best = min(rows, key=lambda row: row["validation_ppl"])
    return {
        "points": len(rows),
        "first_step": rows[0]["step"],
        "last_step": rows[-1]["step"],
        "first_train_ppl": rows[0]["train_ppl"],
        "last_train_ppl": rows[-1]["train_ppl"],
        "first_validation_ppl": rows[0]["validation_ppl"],
        "last_validation_ppl": rows[-1]["validation_ppl"],
        "best_validation_ppl": best["validation_ppl"],
        "best_validation_step": best["step"],
    }


def save_plot(metric_path: Path, output_path: Path) -> None:
    import matplotlib.pyplot as plt

    rows = read_metrics(metric_path)
    steps = [row["step"] for row in rows]
    figure, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    axis.plot(steps, [row["train_ppl"] for row in rows], label="train PPL")
    axis.plot(steps, [row["validation_ppl"] for row in rows], label="validation PPL")
    axis.set_xlabel("step")
    axis.set_ylabel("perplexity")
    axis.set_yscale("log")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(arguments)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_metrics(args.metrics)
    (args.output_dir / "metrics-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    save_plot(args.metrics, args.output_dir / "loss-curves.png")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
