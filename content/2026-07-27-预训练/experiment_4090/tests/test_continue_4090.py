from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import continue_4090


def test_continuation_kwargs_reuses_checkpoint_config_and_changes_only_time_budget(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    tokenizer_path = tmp_path / "tokenizer.json"
    tokenizer_path.write_text("{}", encoding="utf-8")
    config = {
        "text_field": "story_zh",
        "max_stories": 500_000,
        "validation_fraction": 0.02,
        "vocab_size": 8_192,
        "context_length": 256,
        "hidden_size": 512,
        "heads": 8,
        "layers": 8,
        "batch_size": 64,
        "gradient_accumulation_steps": 2,
        "learning_rate": 5e-4,
        "warmup_steps": 500,
        "decay_steps": 30_000,
        "max_minutes": 60.0,
        "max_steps": None,
        "eval_every": 100,
        "eval_batches": 16,
        "early_stopping_evaluations": 120,
        "snapshot_steps": (0, 500, 2_000),
        "snapshot_every_after": 5_000,
        "snapshot_interval": 1_000,
        "seed": 20260716,
    }
    torch.save(
        {
            "model_state": {"weight": torch.tensor([1.0])},
            "summary": {"steps": 16_000, "best_step": 15_000, "best_validation_nll": 4.0},
            "config": config,
        },
        checkpoint_path,
    )

    kwargs = continue_4090.build_continuation_kwargs(
        checkpoint_path=checkpoint_path,
        archive_path=tmp_path / "stories.tar.gz",
        output_dir=tmp_path,
        max_minutes=30.0,
    )

    assert kwargs["resume_checkpoint"] == checkpoint_path
    assert kwargs["resume_tokenizer"] == tokenizer_path
    assert kwargs["max_minutes"] == 30.0
    assert kwargs["max_steps"] is None
    assert kwargs["hidden_size"] == 512
    assert kwargs["snapshot_steps"] == (0, 500, 2_000)
