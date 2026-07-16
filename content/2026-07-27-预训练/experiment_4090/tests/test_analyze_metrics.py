from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import analyze_metrics


def test_summarize_metrics_reports_first_last_and_best_validation_point(tmp_path):
    metric_path = tmp_path / "metrics.jsonl"
    metric_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                {"step": 1, "train_ppl": 100.0, "validation_ppl": 120.0},
                {"step": 2, "train_ppl": 80.0, "validation_ppl": 90.0},
                {"step": 3, "train_ppl": 70.0, "validation_ppl": 95.0},
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_metrics.summarize_metrics(metric_path)

    assert summary["points"] == 3
    assert summary["first_step"] == 1
    assert summary["last_step"] == 3
    assert summary["best_validation_ppl"] == 90.0
    assert summary["best_validation_step"] == 2
