from __future__ import annotations

import sys
import json
import tarfile
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pretrain_4090


def test_load_stories_from_a_jsonl_tar_uses_only_the_configured_text_field(tmp_path):
    source = tmp_path / "stories.tar.gz"
    payload = '\n'.join(
        [
            json.dumps({"story": "第一篇", "unused": "忽略"}, ensure_ascii=False),
            json.dumps({"story": "第二篇"}, ensure_ascii=False),
            json.dumps({"story": ""}, ensure_ascii=False),
        ]
    ).encode("utf-8")
    jsonl = tmp_path / "stories.jsonl"
    jsonl.write_bytes(payload)
    with tarfile.open(source, "w:gz") as archive:
        archive.add(jsonl, arcname="data/stories.jsonl")

    stories = pretrain_4090.load_stories_from_tar(
        source, max_stories=10, text_field="story"
    )

    assert stories == ["第一篇", "第二篇"]


def test_real_cpu_smoke_logs_validation_and_writes_a_checkpoint(tmp_path):
    source = tmp_path / "stories.tar.gz"
    jsonl = tmp_path / "stories.jsonl"
    jsonl.write_text(
        "\n".join(
            json.dumps(
                {"story": f"这是第{index}个独立故事。小猫在花园里散步，然后安全回家。"},
                ensure_ascii=False,
            )
            for index in range(16)
        ),
        encoding="utf-8",
    )
    with tarfile.open(source, "w:gz") as archive:
        archive.add(jsonl, arcname="data/stories.jsonl")

    result = pretrain_4090.run_real_cpu_smoke(
        source,
        tmp_path / "out",
        text_field="story",
        max_stories=16,
        validation_fraction=0.25,
        steps=2,
    )
    metric_rows = [
        json.loads(line)
        for line in (tmp_path / "out" / "metrics.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert result["device"] == "cpu"
    assert result["train_stories"] > 0
    assert result["validation_stories"] > 0
    assert len(metric_rows) == 2
    assert all(row["validation_nll"] > 0 for row in metric_rows)
    assert (tmp_path / "out" / "checkpoint.pt").exists()


def test_byte_level_bpe_has_explicit_special_tokens_and_encodes_chinese_text():
    tokenizer = pretrain_4090.build_byte_level_bpe_tokenizer(
        ["小猫在花园散步。", "小狗也在花园散步。"], vocab_size=64
    )

    encoded = tokenizer.encode("小猫在花园散步。")

    assert tokenizer.token_to_id("[PAD]") == 0
    assert tokenizer.token_to_id("[UNK]") == 1
    assert encoded.ids


def test_sample_token_batch_keeps_each_context_inside_one_story():
    generator = torch.Generator().manual_seed(5)

    contexts, targets = pretrain_4090.sample_token_batch(
        [[1, 2, 3, 4, 5], [7, 8, 9, 10, 11]],
        context_length=3,
        batch_size=4,
        generator=generator,
        device=torch.device("cpu"),
    )

    assert contexts.shape == (4, 3)
    assert targets.shape == (4,)
    valid_examples = {((1, 2, 3), 4), ((2, 3, 4), 5), ((7, 8, 9), 10), ((8, 9, 10), 11)}
    assert all(
        (tuple(context.tolist()), int(target)) in valid_examples
        for context, target in zip(contexts, targets)
    )


def test_wall_clock_cosine_learning_rate_uses_elapsed_time_not_step_count():
    assert pretrain_4090.wall_clock_cosine_learning_rate(0.0003, 0, 3000) == pytest.approx(0.0003)
    assert pretrain_4090.wall_clock_cosine_learning_rate(0.0003, 3000, 3000) == pytest.approx(0.000015)
    midpoint = pretrain_4090.wall_clock_cosine_learning_rate(0.0003, 1500, 3000)
    assert 0.00015 < midpoint < 0.00016
    assert pretrain_4090.wall_clock_cosine_learning_rate(0.0003, 9000, 3000) == pytest.approx(0.000015)


def test_fixed_token_batches_are_repeatable_for_fair_validation():
    kwargs = {
        "context_length": 3,
        "batch_size": 2,
        "batches": 3,
        "seed": 23,
        "device": torch.device("cpu"),
    }
    stories = [[1, 2, 3, 4, 5], [7, 8, 9, 10, 11]]

    first = pretrain_4090.make_fixed_token_batches(stories, **kwargs)
    second = pretrain_4090.make_fixed_token_batches(stories, **kwargs)

    assert len(first) == len(second) == 3
    for (first_contexts, first_targets), (second_contexts, second_targets) in zip(first, second):
        assert torch.equal(first_contexts, second_contexts)
        assert torch.equal(first_targets, second_targets)


def test_early_stopping_only_triggers_after_configured_non_improving_evaluations():
    assert not pretrain_4090.should_stop_early(4, patience_evaluations=5)
    assert pretrain_4090.should_stop_early(5, patience_evaluations=5)
    assert not pretrain_4090.should_stop_early(100, patience_evaluations=0)


def test_warmup_cosine_learning_rate_warms_then_decays_over_optimizer_steps():
    assert pretrain_4090.warmup_cosine_learning_rate(0.0005, 1, 100, 1000) == pytest.approx(0.000005)
    assert pretrain_4090.warmup_cosine_learning_rate(0.0005, 100, 100, 1000) == pytest.approx(0.0005)
    assert pretrain_4090.warmup_cosine_learning_rate(0.0005, 1000, 100, 1000) == pytest.approx(0.000025)


def test_split_stories_is_stable_and_never_leaks_a_story_between_sets():
    stories = [f"故事 {index}" for index in range(20)]

    first_train, first_validation = pretrain_4090.split_stories(
        stories, validation_fraction=0.5
    )
    second_train, second_validation = pretrain_4090.split_stories(
        stories, validation_fraction=0.5
    )

    assert first_train == second_train
    assert first_validation == second_validation
    assert set(first_train).isdisjoint(first_validation)
    assert set(first_train) | set(first_validation) == set(stories)
    assert first_train
    assert first_validation


def test_make_windows_keeps_context_and_target_inside_each_story():
    windows = pretrain_4090.make_windows(
        [[1, 2, 3, 4], [7, 8, 9]], context_length=2
    )

    assert windows == [([1, 2], 3), ([2, 3], 4), ([7, 8], 9)]


def test_causal_model_generates_from_a_short_prompt():
    torch.manual_seed(7)
    model = pretrain_4090.CausalTransformer(
        vocab_size=16, context_length=8, hidden_size=16, heads=4, layers=1
    )

    logits = model(torch.tensor([[1, 2, 3, 4]]))
    generated = pretrain_4090.generate(
        model, [1, 2], max_new_tokens=4, pad_token_id=0, temperature=0.0
    )

    assert logits.shape == (1, 4, 16)
    assert len(generated) == 6
    assert all(0 <= token < 16 for token in generated)


def test_generation_uses_an_unpadded_short_context():
    class UnpaddedPromptModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.context_length = 8
            self.language_model_head = torch.nn.Linear(1, 4, bias=False)
            self.anchor = torch.nn.Parameter(torch.zeros(()))
            self.seen_shapes: list[tuple[int, int]] = []

        def forward(self, token_ids, *, padding_mask=None):
            assert padding_mask is None
            self.seen_shapes.append(tuple(token_ids.shape))
            return torch.zeros(
                (*token_ids.shape, self.language_model_head.out_features),
                device=token_ids.device,
            )

    model = UnpaddedPromptModel()

    generated = pretrain_4090.generate(
        model,
        [1, 2],
        max_new_tokens=2,
        pad_token_id=0,
        temperature=0.0,
        forbidden_token_ids={0, 1},
    )

    assert generated == [1, 2, 2, 2]
    assert model.seen_shapes == [(1, 2), (1, 3)]


def test_generation_can_forbid_the_padding_token():
    model = pretrain_4090.CausalTransformer(
        vocab_size=8, context_length=4, hidden_size=8, heads=2, layers=1
    )
    for parameter in model.parameters():
        parameter.data.zero_()

    generated = pretrain_4090.generate(
        model,
        [1, 2],
        max_new_tokens=2,
        pad_token_id=0,
        temperature=0.0,
        forbidden_token_ids={0, 1},
    )

    assert generated[-2:] == [2, 2]


def test_save_milestone_artifacts_writes_one_checkpoint_and_reproducible_generations(
    tmp_path,
):
    tokenizer = pretrain_4090.build_byte_level_bpe_tokenizer(
        ["小猫在花园散步。", "小狗在河边散步。"], vocab_size=64
    )
    validation_tokens = [
        tokenizer.encode("小猫在花园散步。").ids,
        tokenizer.encode("小狗在河边散步。").ids,
    ]
    model = pretrain_4090.CausalTransformer(
        vocab_size=tokenizer.get_vocab_size(),
        context_length=8,
        hidden_size=16,
        heads=4,
        layers=1,
    )

    checkpoint_path = pretrain_4090.save_milestone_artifacts(
        model=model,
        tokenizer=tokenizer,
        validation_tokens=validation_tokens,
        output_dir=tmp_path,
        step=500,
        validation_nll=3.2,
        seed=19,
        prefix_tokens=4,
        max_new_tokens=4,
        prefixes_per_snapshot=2,
    )
    generation_rows = [
        json.loads(line)
        for line in (tmp_path / "generations.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert checkpoint_path == tmp_path / "checkpoints" / "step-000500.pt"
    assert checkpoint_path.exists()
    assert torch.load(checkpoint_path, weights_only=True)["step"] == 500
    assert len(generation_rows) == 4
    assert {row["mode"] for row in generation_rows} == {"greedy", "sample"}
    assert {row["prefix_index"] for row in generation_rows} == {0, 1}
    assert all(row["step"] == 500 for row in generation_rows)
    assert all(row["full_text"].startswith(row["prefix"]) for row in generation_rows)


def test_snapshot_schedule_keeps_early_milestones_then_captures_every_thousand_steps():
    selected = (0, 500, 2_000)

    assert pretrain_4090.should_capture_snapshot(
        0, selected, every_after=5_000, interval=1_000
    )
    assert pretrain_4090.should_capture_snapshot(
        2_000, selected, every_after=5_000, interval=1_000
    )
    assert pretrain_4090.should_capture_snapshot(
        5_000, selected, every_after=5_000, interval=1_000
    )
    assert pretrain_4090.should_capture_snapshot(
        9_000, selected, every_after=5_000, interval=1_000
    )
    assert not pretrain_4090.should_capture_snapshot(
        5_500, selected, every_after=5_000, interval=1_000
    )


def test_load_resume_checkpoint_recovers_weights_global_step_and_prior_best(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.pt"
    model_state = {"weight": torch.tensor([1.0, 2.0])}
    torch.save(
        {
            "model_state": model_state,
            "summary": {
                "steps": 12_345,
                "best_step": 12_100,
                "best_validation_nll": 4.2,
            },
            "config": {"vocab_size": 64},
        },
        checkpoint_path,
    )

    resume = pretrain_4090.load_resume_checkpoint(checkpoint_path)

    assert torch.equal(resume["model_state"]["weight"], model_state["weight"])
    assert resume["completed_steps"] == 12_345
    assert resume["best_step"] == 12_100
    assert resume["best_validation_nll"] == pytest.approx(4.2)
    assert resume["config"] == {"vocab_size": 64}


def test_train_step_updates_parameters_and_returns_mean_token_loss():
    torch.manual_seed(3)
    model = pretrain_4090.CausalTransformer(
        vocab_size=12, context_length=4, hidden_size=16, heads=4, layers=1
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
    contexts = torch.tensor([[1, 2, 3, 4], [4, 3, 2, 1]])
    targets = torch.tensor([5, 6])
    before = model.language_model_head.weight.detach().clone()

    loss = pretrain_4090.train_step(model, optimizer, contexts, targets)

    assert loss > 0
    assert not torch.equal(before, model.language_model_head.weight)


def test_cpu_smoke_test_writes_metrics_and_a_fixed_generation(tmp_path):
    result = pretrain_4090.run_cpu_smoke_test(tmp_path)
    metric_rows = [
        json.loads(line)
        for line in (tmp_path / "metrics.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert result["device"] == "cpu"
    assert result.get("cpu_threads") == 1
    assert len(result["greedy_ids"]) == 7
    assert len(metric_rows) == 3
    assert all(row["train_nll"] > 0 for row in metric_rows)
    assert all(row["validation_nll"] > 0 for row in metric_rows)


def test_main_runs_cpu_smoke_without_a_gpu(tmp_path):
    exit_code = pretrain_4090.main(
        ["cpu-smoke", "--output-dir", str(tmp_path)]
    )

    assert exit_code == 0
    assert (tmp_path / "metrics.jsonl").exists()
