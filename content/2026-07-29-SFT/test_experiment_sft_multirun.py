import math

import torch

from experiment_sft_multirun import (
    MAX_NEW_TOKENS,
    PROMPTS,
    SAMPLE_SEEDS,
    distribution_metrics,
)


def test_distribution_metrics_for_uniform_logits():
    top1, entropy_bits = distribution_metrics(torch.tensor([0.0, 0.0]))

    assert top1 == 0.5
    assert entropy_bits == 1.0


def test_distribution_metrics_for_four_to_one_odds():
    top1, entropy_bits = distribution_metrics(torch.log(torch.tensor([4.0, 1.0])))

    assert top1 == 0.8
    assert math.isclose(entropy_bits, 0.721928, rel_tol=1e-5)


def test_experiment_has_multiple_prompts_and_longer_generation():
    assert len(PROMPTS) == 5
    assert SAMPLE_SEEDS == (17, 29, 41)
    assert MAX_NEW_TOKENS == 128
