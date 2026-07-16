"""Resume a completed pretraining experiment without reinitializing the model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pretrain_4090


def build_continuation_kwargs(
    *,
    checkpoint_path: Path,
    archive_path: Path,
    output_dir: Path,
    max_minutes: float,
) -> dict[str, object]:
    """Reuse the original experiment configuration with a new time budget."""
    if max_minutes <= 0:
        raise ValueError("max_minutes must be positive")
    resume = pretrain_4090.load_resume_checkpoint(checkpoint_path)
    config = resume["config"]
    if not isinstance(config, dict):
        raise ValueError("resume checkpoint has an invalid config")
    required_keys = (
        "text_field",
        "max_stories",
        "validation_fraction",
        "vocab_size",
        "context_length",
        "hidden_size",
        "heads",
        "layers",
        "batch_size",
        "gradient_accumulation_steps",
        "learning_rate",
        "warmup_steps",
        "decay_steps",
        "eval_every",
        "eval_batches",
        "early_stopping_evaluations",
        "snapshot_steps",
        "snapshot_every_after",
        "snapshot_interval",
        "seed",
    )
    missing = [key for key in required_keys if key not in config]
    if missing:
        raise ValueError(f"resume checkpoint config is missing: {', '.join(missing)}")
    tokenizer_path = checkpoint_path.with_name("tokenizer.json")
    if not tokenizer_path.is_file():
        raise ValueError(f"resume tokenizer does not exist: {tokenizer_path}")

    return {
        "archive_path": archive_path,
        "output_dir": output_dir,
        "text_field": config["text_field"],
        "max_stories": config["max_stories"],
        "validation_fraction": config["validation_fraction"],
        "vocab_size": config["vocab_size"],
        "context_length": config["context_length"],
        "hidden_size": config["hidden_size"],
        "heads": config["heads"],
        "layers": config["layers"],
        "batch_size": config["batch_size"],
        "gradient_accumulation_steps": config["gradient_accumulation_steps"],
        "learning_rate": config["learning_rate"],
        "warmup_steps": config["warmup_steps"],
        "decay_steps": config["decay_steps"],
        "max_minutes": max_minutes,
        "max_steps": None,
        "eval_every": config["eval_every"],
        "eval_batches": config["eval_batches"],
        "early_stopping_evaluations": config["early_stopping_evaluations"],
        "snapshot_steps": tuple(config["snapshot_steps"]),
        "snapshot_every_after": config["snapshot_every_after"],
        "snapshot_interval": config["snapshot_interval"],
        "seed": config["seed"],
        "resume_checkpoint": checkpoint_path,
        "resume_tokenizer": tokenizer_path,
    }


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-minutes", type=float, default=30.0)
    args = parser.parse_args(arguments)
    summary = pretrain_4090.run_gpu_training(
        **build_continuation_kwargs(
            checkpoint_path=args.checkpoint,
            archive_path=args.archive,
            output_dir=args.output_dir,
            max_minutes=args.max_minutes,
        )
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
