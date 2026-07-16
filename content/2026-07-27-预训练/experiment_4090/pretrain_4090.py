"""Reusable components for the one-hour pretraining demonstration."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import tarfile
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from torch import nn


def load_stories_from_tar(
    archive_path: Path, *, max_stories: int, text_field: str
) -> list[str]:
    """Read non-empty story records from JSONL/JSON members in a gzip tar archive."""
    if max_stories < 1:
        raise ValueError("max_stories must be positive")
    if not text_field:
        raise ValueError("text_field must not be empty")

    stories: list[str] = []
    with tarfile.open(archive_path, mode="r:gz") as archive:
        found_json_member = False
        for member in archive:
            if not member.isfile() or Path(member.name).suffix not in {".json", ".jsonl"}:
                continue
            found_json_member = True
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            if member.name.endswith(".jsonl"):
                records = (
                    json.loads(line)
                    for raw_line in extracted
                    if (line := raw_line.decode("utf-8").strip())
                )
            else:
                decoded = json.load(extracted)
                records = decoded.get("data", []) if isinstance(decoded, dict) else decoded

            for record in records:
                text = record.get(text_field) if isinstance(record, dict) else None
                if isinstance(text, str) and text.strip():
                    stories.append(text.strip())
                if len(stories) >= max_stories:
                    return stories
        if not found_json_member:
            raise ValueError("archive contains no JSON or JSONL member")
    return stories


def build_character_vocabulary(
    stories: list[str], *, max_vocab_size: int
) -> dict[str, int]:
    """Build a small explicit [PAD]/[UNK] character vocabulary for CPU validation."""
    if max_vocab_size < 4:
        raise ValueError("max_vocab_size must be at least 4")
    counts = Counter(character for story in stories for character in story)
    vocabulary = {"[PAD]": 0, "[UNK]": 1}
    for character, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[
        : max_vocab_size - len(vocabulary)
    ]:
        vocabulary[character] = len(vocabulary)
    return vocabulary


def encode_character_stories(
    stories: list[str], vocabulary: dict[str, int]
) -> list[list[int]]:
    """Encode stories without silently aliasing unseen characters to a frequent token."""
    unknown_id = vocabulary["[UNK]"]
    return [[vocabulary.get(character, unknown_id) for character in story] for story in stories]


def build_byte_level_bpe_tokenizer(stories: list[str], *, vocab_size: int):
    """Train the experiment's 8K-style BPE with explicit padding and unknown IDs."""
    if vocab_size < 4:
        raise ValueError("vocab_size must be at least 4")
    try:
        from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
    except ImportError as error:
        raise RuntimeError("install tokenizers before preparing the GPU experiment") from error

    tokenizer = Tokenizer(models.BPE(unk_token="[UNK]", byte_fallback=True))
    byte_level = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.pre_tokenizer = byte_level
    tokenizer.decoder = decoders.ByteLevel()
    tokenizer.train_from_iterator(
        stories,
        trainer=trainers.BpeTrainer(
            vocab_size=vocab_size,
            min_frequency=2,
            special_tokens=["[PAD]", "[UNK]"],
            initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        ),
    )
    return tokenizer


def split_stories(
    stories: list[str], *, validation_fraction: float = 0.02
) -> tuple[list[str], list[str]]:
    """Split whole stories deterministically without train/validation overlap."""
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")

    train: list[str] = []
    validation: list[str] = []
    threshold = int(validation_fraction * (1 << 64))

    for story in stories:
        bucket = int.from_bytes(
            hashlib.sha256(story.encode("utf-8")).digest()[:8], "big"
        )
        (validation if bucket < threshold else train).append(story)

    return train, validation


def make_windows(
    tokenized_stories: list[list[int]], *, context_length: int
) -> list[tuple[list[int], int]]:
    """Create next-token examples without allowing contexts to cross stories."""
    if context_length < 1:
        raise ValueError("context_length must be positive")

    windows: list[tuple[list[int], int]] = []
    for story in tokenized_stories:
        for target_index in range(context_length, len(story)):
            context = story[target_index - context_length : target_index]
            windows.append((context, story[target_index]))

    return windows


def sample_token_batch(
    tokenized_stories: list[list[int]],
    *,
    context_length: int,
    batch_size: int,
    generator: torch.Generator,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Sample next-token contexts without ever concatenating two stories."""
    eligible = [story for story in tokenized_stories if len(story) > context_length]
    if not eligible:
        raise ValueError("no story is long enough for the configured context length")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    contexts: list[list[int]] = []
    targets: list[int] = []
    story_indices = torch.randint(len(eligible), (batch_size,), generator=generator)
    for story_index in story_indices.tolist():
        story = eligible[story_index]
        target_index = int(
            torch.randint(
                context_length, len(story), (1,), generator=generator
            ).item()
        )
        contexts.append(story[target_index - context_length : target_index])
        targets.append(story[target_index])
    return (
        torch.tensor(contexts, dtype=torch.long, device=device),
        torch.tensor(targets, dtype=torch.long, device=device),
    )


def make_fixed_token_batches(
    tokenized_stories: list[list[int]],
    *,
    context_length: int,
    batch_size: int,
    batches: int,
    seed: int,
    device: torch.device,
) -> list[tuple[torch.Tensor, torch.Tensor]]:
    """Materialize one deterministic validation sample for every evaluation point."""
    if batches < 1:
        raise ValueError("batches must be positive")
    generator = torch.Generator().manual_seed(seed)
    return [
        sample_token_batch(
            tokenized_stories,
            context_length=context_length,
            batch_size=batch_size,
            generator=generator,
            device=device,
        )
        for _ in range(batches)
    ]


def wall_clock_cosine_learning_rate(
    initial_learning_rate: float, elapsed_seconds: float, total_seconds: float
) -> float:
    """Cosine decay based on the actual time budget, not an unknown step count."""
    if initial_learning_rate <= 0 or total_seconds <= 0:
        raise ValueError("learning rate and total seconds must be positive")
    progress = min(1.0, max(0.0, elapsed_seconds / total_seconds))
    minimum_learning_rate = initial_learning_rate / 20
    return minimum_learning_rate + (initial_learning_rate - minimum_learning_rate) * (
        1 + math.cos(math.pi * progress)
    ) / 2


def should_stop_early(non_improving_evaluations: int, *, patience_evaluations: int) -> bool:
    """Return whether a validation-based early-stopping patience has been exhausted."""
    if patience_evaluations < 0:
        raise ValueError("patience_evaluations must not be negative")
    return patience_evaluations > 0 and non_improving_evaluations >= patience_evaluations


def should_capture_snapshot(
    step: int,
    selected_steps: tuple[int, ...],
    *,
    every_after: int,
    interval: int,
) -> bool:
    """Capture named early milestones, then a regular late-training cadence."""
    if step < 0 or every_after < 0 or interval < 1:
        raise ValueError("step/every_after must be non-negative and interval positive")
    return step in selected_steps or (
        step >= every_after and (step - every_after) % interval == 0
    )


def warmup_cosine_learning_rate(
    initial_learning_rate: float,
    optimizer_step: int,
    warmup_steps: int,
    decay_steps: int,
) -> float:
    """Linear warmup followed by cosine decay over calibrated optimizer steps."""
    if initial_learning_rate <= 0 or optimizer_step < 1 or warmup_steps < 1:
        raise ValueError("learning rate, optimizer_step, and warmup_steps must be positive")
    if decay_steps <= warmup_steps:
        raise ValueError("decay_steps must exceed warmup_steps")
    if optimizer_step <= warmup_steps:
        return initial_learning_rate * optimizer_step / warmup_steps
    progress = min(1.0, (optimizer_step - warmup_steps) / (decay_steps - warmup_steps))
    minimum_learning_rate = initial_learning_rate / 20
    return minimum_learning_rate + (initial_learning_rate - minimum_learning_rate) * (
        1 + math.cos(math.pi * progress)
    ) / 2


class CausalTransformer(nn.Module):
    """A compact causal language model for the controlled experiment."""

    def __init__(
        self,
        *,
        vocab_size: int,
        context_length: int,
        hidden_size: int,
        heads: int,
        layers: int,
    ) -> None:
        super().__init__()
        self.context_length = context_length
        self.token_embedding = nn.Embedding(vocab_size, hidden_size)
        self.position_embedding = nn.Embedding(context_length, hidden_size)
        block = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=heads,
            dim_feedforward=hidden_size * 4,
            batch_first=True,
            activation="gelu",
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(block, num_layers=layers)
        self.normalization = nn.LayerNorm(hidden_size)
        self.language_model_head = nn.Linear(hidden_size, vocab_size, bias=False)

    def forward(
        self, token_ids: torch.Tensor, *, padding_mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        batch_size, sequence_length = token_ids.shape
        if sequence_length > self.context_length:
            raise ValueError("token_ids exceed the configured context_length")

        positions = torch.arange(sequence_length, device=token_ids.device)
        hidden = self.token_embedding(token_ids) + self.position_embedding(positions)
        causal_mask = torch.triu(
            torch.ones(sequence_length, sequence_length, device=token_ids.device, dtype=torch.bool),
            diagonal=1,
        )
        hidden = self.transformer(
            hidden, mask=causal_mask, src_key_padding_mask=padding_mask
        )
        return self.language_model_head(self.normalization(hidden))


@torch.no_grad()
def generate(
    model: CausalTransformer,
    prompt_ids: list[int],
    *,
    max_new_tokens: int,
    pad_token_id: int,
    temperature: float,
    forbidden_token_ids: set[int] | None = None,
) -> list[int]:
    """Autoregressively generate from the real (never left-padded) context."""
    if not prompt_ids:
        raise ValueError("prompt_ids must not be empty")
    if max_new_tokens < 0:
        raise ValueError("max_new_tokens must not be negative")
    if temperature < 0:
        raise ValueError("temperature must not be negative")
    forbidden_token_ids = forbidden_token_ids or set()
    if len(forbidden_token_ids) >= model.language_model_head.out_features:
        raise ValueError("at least one token must remain available for generation")

    was_training = model.training
    model.eval()
    generated = list(prompt_ids)
    device = next(model.parameters()).device

    for _ in range(max_new_tokens):
        context = generated[-model.context_length :]
        logits = model(
            torch.tensor([context], dtype=torch.long, device=device)
        )[0, -1]
        if forbidden_token_ids:
            logits = logits.clone()
            logits[list(forbidden_token_ids)] = -torch.inf

        if temperature == 0:
            next_id = int(logits.argmax().item())
        else:
            probabilities = torch.softmax(logits / temperature, dim=-1)
            next_id = int(torch.multinomial(probabilities, 1).item())
        generated.append(next_id)

    if was_training:
        model.train()
    return generated


def save_milestone_artifacts(
    *,
    model: CausalTransformer,
    tokenizer,
    validation_tokens: list[list[int]],
    output_dir: Path,
    step: int,
    validation_nll: float | None,
    seed: int,
    prefix_tokens: int,
    max_new_tokens: int,
    prefixes_per_snapshot: int,
) -> Path:
    """Save one portable model snapshot plus fixed validation continuations."""
    if step < 0 or prefix_tokens < 1 or max_new_tokens < 1:
        raise ValueError("step must be non-negative; token counts must be positive")
    if prefixes_per_snapshot < 1:
        raise ValueError("prefixes_per_snapshot must be positive")
    selected_prefixes = [
        tokens[:prefix_tokens]
        for tokens in validation_tokens[:prefixes_per_snapshot]
        if tokens[:prefix_tokens]
    ]
    if not selected_prefixes:
        raise ValueError("validation_tokens contains no usable generation prefix")

    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoints_dir / f"step-{step:06d}.pt"
    torch.save(
        {
            "model_state": {
                name: tensor.detach().cpu() for name, tensor in model.state_dict().items()
            },
            "tokenizer": tokenizer.to_str(),
            "step": step,
            "validation_nll": validation_nll,
        },
        checkpoint_path,
    )

    pad_token_id = tokenizer.token_to_id("[PAD]")
    unknown_token_id = tokenizer.token_to_id("[UNK]")
    if pad_token_id is None:
        raise ValueError("tokenizer is missing [PAD]")
    forbidden_token_ids = {
        token_id for token_id in (pad_token_id, unknown_token_id) if token_id is not None
    }
    device = next(model.parameters()).device
    cuda_devices = [device.index or 0] if device.type == "cuda" else []
    generation_path = output_dir / "generations.jsonl"
    with generation_path.open("a", encoding="utf-8") as generation_file:
        for prefix_index, prefix in enumerate(selected_prefixes):
            for mode, temperature in (("greedy", 0.0), ("sample", 0.7)):
                sampling_seed = seed + step * 100 + prefix_index
                with torch.random.fork_rng(devices=cuda_devices):
                    if mode == "sample":
                        torch.manual_seed(sampling_seed)
                        if device.type == "cuda":
                            torch.cuda.manual_seed_all(sampling_seed)
                    generated_ids = generate(
                        model,
                        prefix,
                        max_new_tokens=max_new_tokens,
                        pad_token_id=pad_token_id,
                        temperature=temperature,
                        forbidden_token_ids=forbidden_token_ids,
                    )
                prefix_text = tokenizer.decode(prefix, skip_special_tokens=True)
                completion_text = tokenizer.decode(
                    generated_ids[len(prefix) :], skip_special_tokens=True
                )
                row = {
                    "step": step,
                    "validation_nll": validation_nll,
                    "prefix_index": prefix_index,
                    "mode": mode,
                    "temperature": temperature,
                    "sampling_seed": sampling_seed if mode == "sample" else None,
                    "prefix": prefix_text,
                    "completion": completion_text,
                    "full_text": prefix_text + completion_text,
                }
                generation_file.write(json.dumps(row, ensure_ascii=False) + "\n")
    return checkpoint_path


def load_resume_checkpoint(checkpoint_path: Path) -> dict[str, object]:
    """Load the persistent state needed to continue a completed training run."""
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("model_state"), dict):
        raise ValueError("resume checkpoint is missing model_state")
    summary = payload.get("summary")
    if not isinstance(summary, dict) or not isinstance(summary.get("steps"), int):
        raise ValueError("resume checkpoint is missing summary.steps")
    config = payload.get("config")
    if not isinstance(config, dict):
        raise ValueError("resume checkpoint is missing config")
    best_nll = summary.get("best_validation_nll", math.inf)
    if not isinstance(best_nll, (int, float)):
        raise ValueError("resume checkpoint has an invalid best_validation_nll")
    best_step = summary.get("best_step", 0)
    if not isinstance(best_step, int):
        raise ValueError("resume checkpoint has an invalid best_step")
    return {
        "model_state": payload["model_state"],
        "completed_steps": summary["steps"],
        "best_step": best_step,
        "best_validation_nll": float(best_nll),
        "config": config,
        "optimizer_state": payload.get("optimizer_state"),
        "train_generator_state": payload.get("train_generator_state"),
        "cpu_rng_state": payload.get("cpu_rng_state"),
        "cuda_rng_state": payload.get("cuda_rng_state"),
    }


def train_step(
    model: CausalTransformer,
    optimizer: torch.optim.Optimizer,
    contexts: torch.Tensor,
    targets: torch.Tensor,
) -> float:
    """Run one next-token update and return batch mean negative log-likelihood."""
    model.train()
    logits = model(contexts)[:, -1]
    loss = F.cross_entropy(logits, targets)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()
    return float(loss.detach().item())


@torch.no_grad()
def evaluate_nll(
    model: CausalTransformer, contexts: torch.Tensor, targets: torch.Tensor
) -> float:
    """Return next-token negative log-likelihood without updating parameters."""
    was_training = model.training
    model.eval()
    loss = F.cross_entropy(model(contexts)[:, -1], targets)
    if was_training:
        model.train()
    return float(loss.item())


def run_cpu_smoke_test(output_dir: Path) -> dict[str, object]:
    """Exercise data windows, training, validation, generation, and metric logging."""
    torch.set_num_threads(1)
    torch.manual_seed(11)
    output_dir.mkdir(parents=True, exist_ok=True)
    train_windows = make_windows(
        [[1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]], context_length=4
    )
    validation_windows = make_windows([[7, 8, 9, 10, 11, 12]], context_length=4)

    train_contexts = torch.tensor([context for context, _ in train_windows])
    train_targets = torch.tensor([target for _, target in train_windows])
    validation_contexts = torch.tensor([context for context, _ in validation_windows])
    validation_targets = torch.tensor([target for _, target in validation_windows])

    model = CausalTransformer(
        vocab_size=16, context_length=4, hidden_size=16, heads=4, layers=1
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
    metric_path = output_dir / "metrics.jsonl"

    with metric_path.open("w", encoding="utf-8") as metrics_file:
        for step in range(1, 4):
            train_nll = train_step(model, optimizer, train_contexts, train_targets)
            validation_nll = evaluate_nll(
                model, validation_contexts, validation_targets
            )
            metrics_file.write(
                json.dumps(
                    {
                        "step": step,
                        "train_nll": train_nll,
                        "validation_nll": validation_nll,
                    }
                )
                + "\n"
            )

    greedy_ids = generate(
        model, [1, 2, 3], max_new_tokens=4, pad_token_id=0, temperature=0.0
    )
    return {
        "device": "cpu",
        "cpu_threads": torch.get_num_threads(),
        "greedy_ids": greedy_ids,
    }


def run_real_cpu_smoke(
    archive_path: Path,
    output_dir: Path,
    *,
    text_field: str,
    max_stories: int,
    validation_fraction: float,
    steps: int,
) -> dict[str, object]:
    """Run a deliberately tiny real-corpus CPU preflight, then stop.

    This is not the 4090 experiment.  It verifies archive parsing, whole-story
    splitting, independent validation, metrics, checkpointing, and decoding.
    """
    if steps < 1:
        raise ValueError("steps must be positive")

    torch.set_num_threads(1)
    torch.manual_seed(17)
    output_dir.mkdir(parents=True, exist_ok=True)
    stories = load_stories_from_tar(
        archive_path, max_stories=max_stories, text_field=text_field
    )
    train_stories, validation_stories = split_stories(
        stories, validation_fraction=validation_fraction
    )
    if not train_stories or not validation_stories:
        raise ValueError("smoke split produced an empty train or validation set")

    tokenizer = build_byte_level_bpe_tokenizer(train_stories, vocab_size=512)
    train_token_stories = [encoding.ids for encoding in tokenizer.encode_batch(train_stories)]
    validation_token_stories = [
        encoding.ids for encoding in tokenizer.encode_batch(validation_stories)
    ]
    longest_shared_story = min(
        max(map(len, train_token_stories)), max(map(len, validation_token_stories))
    )
    context_length = min(16, longest_shared_story - 1)
    if context_length < 1:
        raise ValueError("stories are too short for the smoke-test tokenizer")
    train_windows = make_windows(
        train_token_stories,
        context_length=context_length,
    )
    validation_windows = make_windows(
        validation_token_stories,
        context_length=context_length,
    )
    if not train_windows or not validation_windows:
        raise ValueError("stories are too short for the smoke-test context length")

    model = CausalTransformer(
        vocab_size=tokenizer.get_vocab_size(),
        context_length=context_length,
        hidden_size=64,
        heads=4,
        layers=2,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003)
    validation_contexts = torch.tensor(
        [context for context, _ in validation_windows[:256]], dtype=torch.long
    )
    validation_targets = torch.tensor(
        [target for _, target in validation_windows[:256]], dtype=torch.long
    )
    metric_path = output_dir / "metrics.jsonl"

    with metric_path.open("w", encoding="utf-8") as metrics_file:
        for step in range(1, steps + 1):
            batch = [
                train_windows[index % len(train_windows)]
                for index in range((step - 1) * 16, step * 16)
            ]
            train_contexts = torch.tensor(
                [context for context, _ in batch], dtype=torch.long
            )
            train_targets = torch.tensor([target for _, target in batch], dtype=torch.long)
            train_nll = train_step(model, optimizer, train_contexts, train_targets)
            validation_nll = evaluate_nll(
                model, validation_contexts, validation_targets
            )
            metrics_file.write(
                json.dumps(
                    {
                        "step": step,
                        "train_nll": train_nll,
                        "train_ppl": math.exp(train_nll),
                        "validation_nll": validation_nll,
                        "validation_ppl": math.exp(validation_nll),
                    }
                )
                + "\n"
            )

    encoded_prefix = tokenizer.encode(validation_stories[0]).ids
    generated_ids = generate(
        model,
        encoded_prefix[:8],
        max_new_tokens=16,
        pad_token_id=tokenizer.token_to_id("[PAD]"),
        temperature=0.0,
        forbidden_token_ids={tokenizer.token_to_id("[PAD]"), tokenizer.token_to_id("[UNK]")},
    )
    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    checkpoint_path = output_dir / "checkpoint.pt"
    torch.save(
        {
            "model_state": model.state_dict(),
            "tokenizer": tokenizer.to_str(),
            "context_length": context_length,
            "seed": 17,
        },
        checkpoint_path,
    )
    summary = {
        "device": "cpu",
        "cpu_threads": torch.get_num_threads(),
        "stories_loaded": len(stories),
        "train_stories": len(train_stories),
        "validation_stories": len(validation_stories),
        "vocabulary_size": tokenizer.get_vocab_size(),
        "steps": steps,
        "generated_text": generated_text,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def run_gpu_training(
    archive_path: Path,
    output_dir: Path,
    *,
    text_field: str,
    max_stories: int,
    validation_fraction: float,
    vocab_size: int,
    context_length: int,
    hidden_size: int,
    heads: int,
    layers: int,
    batch_size: int,
    gradient_accumulation_steps: int,
    learning_rate: float,
    warmup_steps: int,
    decay_steps: int,
    max_minutes: float,
    max_steps: int | None,
    eval_every: int,
    eval_batches: int,
    early_stopping_evaluations: int,
    snapshot_steps: tuple[int, ...],
    snapshot_every_after: int,
    snapshot_interval: int,
    resume_checkpoint: Path | None,
    resume_tokenizer: Path | None,
    seed: int,
) -> dict[str, object]:
    """Run the bounded 4090 experiment, writing all evidence to ``output_dir``."""
    if not torch.cuda.is_available():
        raise RuntimeError("gpu-train requires a visible CUDA GPU; use real-cpu-smoke otherwise")
    if max_minutes <= 0 or eval_every < 1 or eval_batches < 1:
        raise ValueError("max_minutes, eval_every, and eval_batches must be positive")
    if gradient_accumulation_steps < 1:
        raise ValueError("gradient_accumulation_steps must be positive")
    if warmup_steps < 1 or decay_steps <= warmup_steps:
        raise ValueError("decay_steps must exceed positive warmup_steps")
    if early_stopping_evaluations < 0:
        raise ValueError("early_stopping_evaluations must not be negative")
    if any(step < 0 for step in snapshot_steps):
        raise ValueError("snapshot_steps must be non-negative")
    if any(step and step % eval_every for step in snapshot_steps):
        raise ValueError("non-zero snapshot_steps must be divisible by eval_every")
    if snapshot_every_after < 0 or snapshot_interval < 1:
        raise ValueError("snapshot cadence must be non-negative with a positive interval")
    if snapshot_every_after % eval_every or snapshot_interval % eval_every:
        raise ValueError("snapshot cadence must be divisible by eval_every")

    device = torch.device("cuda")
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    resume = load_resume_checkpoint(resume_checkpoint) if resume_checkpoint else None
    stories = load_stories_from_tar(
        archive_path, max_stories=max_stories, text_field=text_field
    )
    train_stories, validation_stories = split_stories(
        stories, validation_fraction=validation_fraction
    )
    if not train_stories or not validation_stories:
        raise ValueError("split produced an empty train or validation set")

    if resume is None:
        tokenizer = build_byte_level_bpe_tokenizer(train_stories, vocab_size=vocab_size)
        tokenizer.save(str(output_dir / "tokenizer.json"))
    else:
        if resume_tokenizer is None:
            resume_tokenizer = resume_checkpoint.with_name("tokenizer.json")
        try:
            from tokenizers import Tokenizer
        except ImportError as error:
            raise RuntimeError("install tokenizers before resuming the GPU experiment") from error
        tokenizer = Tokenizer.from_file(str(resume_tokenizer))
        if tokenizer.get_vocab_size() != vocab_size:
            raise ValueError("resume tokenizer vocabulary size does not match the run config")
    train_tokens = [encoding.ids for encoding in tokenizer.encode_batch(train_stories)]
    validation_tokens = [
        encoding.ids for encoding in tokenizer.encode_batch(validation_stories)
    ]
    if not any(len(story) > context_length for story in train_tokens):
        raise ValueError("training stories are too short for the configured context length")
    if not any(len(story) > context_length for story in validation_tokens):
        raise ValueError("validation stories are too short for the configured context length")

    model = CausalTransformer(
        vocab_size=tokenizer.get_vocab_size(),
        context_length=context_length,
        hidden_size=hidden_size,
        heads=heads,
        layers=layers,
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        betas=(0.9, 0.95),
        weight_decay=0.1,
    )
    initial_step = 0
    best_validation_nll = math.inf
    best_step = 0
    optimizer_state_restored = False
    train_generator = torch.Generator()
    if resume is None:
        train_generator.manual_seed(seed)
    else:
        model.load_state_dict(resume["model_state"])
        initial_step = int(resume["completed_steps"])
        best_validation_nll = float(resume["best_validation_nll"])
        best_step = int(resume["best_step"])
        optimizer_state = resume["optimizer_state"]
        if isinstance(optimizer_state, dict):
            optimizer.load_state_dict(optimizer_state)
            optimizer_state_restored = True
        generator_state = resume["train_generator_state"]
        if isinstance(generator_state, torch.Tensor):
            train_generator.set_state(generator_state)
        else:
            train_generator.manual_seed(seed + initial_step)
    fixed_validation_batches = make_fixed_token_batches(
        validation_tokens,
        context_length=context_length,
        batch_size=batch_size,
        batches=eval_batches,
        seed=seed + 1,
        device=device,
    )
    started_at = time.perf_counter()
    total_seconds = max_minutes * 60
    deadline = started_at + total_seconds
    metric_path = output_dir / "metrics.jsonl"
    step = initial_step
    non_improving_evaluations = 0
    stopped_early = False

    def validation_nll() -> float:
        model.eval()
        losses: list[float] = []
        with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            for contexts, targets in fixed_validation_batches:
                losses.append(float(F.cross_entropy(model(contexts)[:, -1], targets).item()))
        return sum(losses) / len(losses)

    if resume is not None:
        cpu_rng_state = resume["cpu_rng_state"]
        cuda_rng_state = resume["cuda_rng_state"]
        if isinstance(cpu_rng_state, torch.Tensor):
            torch.set_rng_state(cpu_rng_state)
        if isinstance(cuda_rng_state, list) and all(
            isinstance(state, torch.Tensor) for state in cuda_rng_state
        ):
            torch.cuda.set_rng_state_all(cuda_rng_state)

    if resume is None and should_capture_snapshot(
        0,
        snapshot_steps,
        every_after=snapshot_every_after,
        interval=snapshot_interval,
    ):
        save_milestone_artifacts(
            model=model,
            tokenizer=tokenizer,
            validation_tokens=validation_tokens,
            output_dir=output_dir,
            step=0,
            validation_nll=None,
            seed=seed,
            prefix_tokens=32,
            max_new_tokens=128,
            prefixes_per_snapshot=2,
        )

    with metric_path.open("a" if resume is not None else "w", encoding="utf-8") as metrics_file:
        while time.perf_counter() < deadline and (max_steps is None or step < max_steps):
            step += 1
            model.train()
            current_learning_rate = warmup_cosine_learning_rate(
                learning_rate, step, warmup_steps, decay_steps
            )
            for parameter_group in optimizer.param_groups:
                parameter_group["lr"] = current_learning_rate
            optimizer.zero_grad(set_to_none=True)
            train_loss_value = 0.0
            for _ in range(gradient_accumulation_steps):
                contexts, targets = sample_token_batch(
                    train_tokens,
                    context_length=context_length,
                    batch_size=batch_size,
                    generator=train_generator,
                    device=device,
                )
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    train_loss = F.cross_entropy(model(contexts)[:, -1], targets)
                train_loss_value += float(train_loss.detach().item())
                (train_loss / gradient_accumulation_steps).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            if step == 1 or step % eval_every == 0 or (max_steps is not None and step == max_steps):
                valid_nll = validation_nll()
                elapsed = time.perf_counter() - started_at
                row = {
                    "step": step,
                    "elapsed_seconds": elapsed,
                    "train_nll": train_loss_value / gradient_accumulation_steps,
                    "train_ppl": math.exp(train_loss_value / gradient_accumulation_steps),
                    "validation_nll": valid_nll,
                    "validation_ppl": math.exp(valid_nll),
                    "learning_rate": optimizer.param_groups[0]["lr"],
                    "tokens_per_second": (step - initial_step)
                    * batch_size
                    * context_length
                    * gradient_accumulation_steps
                    / elapsed,
                }
                metrics_file.write(json.dumps(row) + "\n")
                metrics_file.flush()
                if valid_nll < best_validation_nll:
                    best_validation_nll = valid_nll
                    best_step = step
                    non_improving_evaluations = 0
                    torch.save(
                        {
                            "model_state": model.state_dict(),
                            "tokenizer": tokenizer.to_str(),
                            "step": step,
                            "validation_nll": valid_nll,
                        },
                        output_dir / "best-checkpoint.pt",
                    )
                else:
                    non_improving_evaluations += 1
                if should_capture_snapshot(
                    step,
                    snapshot_steps,
                    every_after=snapshot_every_after,
                    interval=snapshot_interval,
                ):
                    save_milestone_artifacts(
                        model=model,
                        tokenizer=tokenizer,
                        validation_tokens=validation_tokens,
                        output_dir=output_dir,
                        step=step,
                        validation_nll=valid_nll,
                        seed=seed,
                        prefix_tokens=32,
                        max_new_tokens=128,
                        prefixes_per_snapshot=2,
                    )
                if should_stop_early(
                    non_improving_evaluations,
                    patience_evaluations=early_stopping_evaluations,
                ):
                    stopped_early = True
                    break

    prefix = validation_tokens[0][: min(32, len(validation_tokens[0]))]
    generated_ids = generate(
        model,
        prefix,
        max_new_tokens=128,
        pad_token_id=tokenizer.token_to_id("[PAD]"),
        temperature=0.0,
        forbidden_token_ids={tokenizer.token_to_id("[PAD]"), tokenizer.token_to_id("[UNK]")},
    )
    summary = {
        "device": torch.cuda.get_device_name(device),
        "torch_cuda": torch.version.cuda,
        "seed": seed,
        "stories_loaded": len(stories),
        "train_stories": len(train_stories),
        "validation_stories": len(validation_stories),
        "vocabulary_size": tokenizer.get_vocab_size(),
        "steps": step,
        "initial_step": initial_step,
        "resumed_from": str(resume_checkpoint) if resume_checkpoint else None,
        "optimizer_state_restored": optimizer_state_restored,
        "best_step": best_step,
        "best_validation_nll": best_validation_nll,
        "best_validation_ppl": math.exp(best_validation_nll),
        "stopped_early": stopped_early,
        "peak_memory_bytes": torch.cuda.max_memory_allocated(device),
        "generated_greedy": tokenizer.decode(generated_ids, skip_special_tokens=True),
    }
    run_config = {
        "text_field": text_field,
        "max_stories": max_stories,
        "validation_fraction": validation_fraction,
        "vocab_size": vocab_size,
        "context_length": context_length,
        "hidden_size": hidden_size,
        "heads": heads,
        "layers": layers,
        "batch_size": batch_size,
        "gradient_accumulation_steps": gradient_accumulation_steps,
        "learning_rate": learning_rate,
        "warmup_steps": warmup_steps,
        "decay_steps": decay_steps,
        "max_minutes": max_minutes,
        "max_steps": max_steps,
        "eval_every": eval_every,
        "eval_batches": eval_batches,
        "early_stopping_evaluations": early_stopping_evaluations,
        "snapshot_steps": snapshot_steps,
        "snapshot_every_after": snapshot_every_after,
        "snapshot_interval": snapshot_interval,
        "resume_checkpoint": str(resume_checkpoint) if resume_checkpoint else None,
        "seed": seed,
    }
    torch.save(
        {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "train_generator_state": train_generator.get_state(),
            "cpu_rng_state": torch.get_rng_state(),
            "cuda_rng_state": torch.cuda.get_rng_state_all(),
            "summary": summary,
            "config": run_config,
        },
        output_dir / "checkpoint.pt",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    smoke_parser = subparsers.add_parser(
        "cpu-smoke", help="run the no-GPU data/model/logging smoke test"
    )
    smoke_parser.add_argument("--output-dir", type=Path, required=True)
    real_smoke_parser = subparsers.add_parser(
        "real-cpu-smoke",
        help="run a tiny real-corpus CPU preflight; it never uses a GPU",
    )
    real_smoke_parser.add_argument("--archive", type=Path, required=True)
    real_smoke_parser.add_argument("--output-dir", type=Path, required=True)
    real_smoke_parser.add_argument("--text-field", default="story_zh")
    real_smoke_parser.add_argument("--max-stories", type=int, default=256)
    real_smoke_parser.add_argument("--validation-fraction", type=float, default=0.2)
    real_smoke_parser.add_argument("--steps", type=int, default=5)
    gpu_train_parser = subparsers.add_parser(
        "gpu-train", help="run the time-bounded 4090 experiment; CUDA is required"
    )
    gpu_train_parser.add_argument("--archive", type=Path, required=True)
    gpu_train_parser.add_argument("--output-dir", type=Path, required=True)
    gpu_train_parser.add_argument(
        "--resume-checkpoint",
        type=Path,
        help="continue model/optimizer state from a completed checkpoint",
    )
    gpu_train_parser.add_argument(
        "--resume-tokenizer",
        type=Path,
        help="tokenizer.json paired with --resume-checkpoint; defaults beside it",
    )
    gpu_train_parser.add_argument("--text-field", default="story_zh")
    gpu_train_parser.add_argument("--max-stories", type=int, default=500_000)
    gpu_train_parser.add_argument("--validation-fraction", type=float, default=0.02)
    gpu_train_parser.add_argument("--vocab-size", type=int, default=8_192)
    gpu_train_parser.add_argument("--context-length", type=int, default=256)
    gpu_train_parser.add_argument("--hidden-size", type=int, default=512)
    gpu_train_parser.add_argument("--heads", type=int, default=8)
    gpu_train_parser.add_argument("--layers", type=int, default=8)
    gpu_train_parser.add_argument("--batch-size", type=int, default=64)
    gpu_train_parser.add_argument("--gradient-accumulation-steps", type=int, default=2)
    gpu_train_parser.add_argument("--learning-rate", type=float, default=5e-4)
    gpu_train_parser.add_argument("--warmup-steps", type=int, default=500)
    gpu_train_parser.add_argument("--decay-steps", type=int, default=30_000)
    gpu_train_parser.add_argument("--max-minutes", type=float, default=35.0)
    gpu_train_parser.add_argument("--max-steps", type=int)
    gpu_train_parser.add_argument("--eval-every", type=int, default=100)
    gpu_train_parser.add_argument("--eval-batches", type=int, default=16)
    gpu_train_parser.add_argument("--early-stopping-evaluations", type=int, default=60)
    gpu_train_parser.add_argument(
        "--snapshot-steps",
        type=lambda value: tuple(
            sorted({int(step.strip()) for step in value.split(",") if step.strip()})
        ),
        default=(0, 500, 2_000),
        help="comma-separated early evaluated steps for weights and fixed generations",
    )
    gpu_train_parser.add_argument(
        "--snapshot-every-after",
        type=int,
        default=5_000,
        help="start regular snapshot capture at this evaluated step",
    )
    gpu_train_parser.add_argument(
        "--snapshot-interval",
        type=int,
        default=1_000,
        help="regular snapshot interval after --snapshot-every-after",
    )
    gpu_train_parser.add_argument("--seed", type=int, default=20260716)
    args = parser.parse_args(arguments)

    if args.command == "cpu-smoke":
        print(json.dumps(run_cpu_smoke_test(args.output_dir)))
        return 0
    if args.command == "real-cpu-smoke":
        print(
            json.dumps(
                run_real_cpu_smoke(
                    args.archive,
                    args.output_dir,
                    text_field=args.text_field,
                    max_stories=args.max_stories,
                    validation_fraction=args.validation_fraction,
                    steps=args.steps,
                ),
                ensure_ascii=False,
            )
        )
        return 0
    if args.command == "gpu-train":
        print(
            json.dumps(
                run_gpu_training(
                    args.archive,
                    args.output_dir,
                    text_field=args.text_field,
                    max_stories=args.max_stories,
                    validation_fraction=args.validation_fraction,
                    vocab_size=args.vocab_size,
                    context_length=args.context_length,
                    hidden_size=args.hidden_size,
                    heads=args.heads,
                    layers=args.layers,
                    batch_size=args.batch_size,
                    gradient_accumulation_steps=args.gradient_accumulation_steps,
                    learning_rate=args.learning_rate,
                    warmup_steps=args.warmup_steps,
                    decay_steps=args.decay_steps,
                    max_minutes=args.max_minutes,
                    max_steps=args.max_steps,
                    eval_every=args.eval_every,
                    eval_batches=args.eval_batches,
                    early_stopping_evaluations=args.early_stopping_evaluations,
                    snapshot_steps=args.snapshot_steps,
                    snapshot_every_after=args.snapshot_every_after,
                    snapshot_interval=args.snapshot_interval,
                    resume_checkpoint=args.resume_checkpoint,
                    resume_tokenizer=args.resume_tokenizer,
                    seed=args.seed,
                ),
                ensure_ascii=False,
            )
        )
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
