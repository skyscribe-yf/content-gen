"""Compare Qwen3-8B base and post-trained checkpoints across five prompts.

Run on an AutoDL RTX 4090 after both checkpoints are cached:
  HF_HOME=/root/autodl-tmp/huggingface HF_HUB_OFFLINE=1 \
    python experiment_sft_multirun.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MAX_NEW_TOKENS = 128
METRIC_STEPS = 32
SAMPLE_SEEDS = (17, 29, 41)
PROMPTS = (
    {"id": "explain", "text": "请解释什么是梯度下降。"},
    {
        "id": "rewrite",
        "text": "把“梯度下降沿损失下降最快的方向更新参数”改写成一句面向初学者的话。",
    },
    {
        "id": "compare",
        "text": "用三条要点比较全量梯度下降和随机梯度下降。",
    },
    {
        "id": "code",
        "text": "写一个 Python 函数，计算 f(x)=x^2 在 x 处的一步梯度下降更新。",
    },
    {
        "id": "classify",
        "text": "以下文本的情感是正面、负面还是中性？“这个教程步骤清楚，我终于懂了。”只回答标签。",
    },
)
MODELS = (
    ("base", "Qwen/Qwen3-8B-Base", False),
    ("posttrained", "Qwen/Qwen3-8B", True),
)


def distribution_metrics(logits: torch.Tensor) -> tuple[float, float]:
    """Return top-1 probability and Shannon entropy in bits."""
    probabilities = torch.softmax(logits.float(), dim=-1)
    top1 = probabilities.max().item()
    entropy_bits = -(probabilities * probabilities.clamp_min(1e-12).log2()).sum().item()
    return round(top1, 6), round(entropy_bits, 6)


def prepare_inputs(tokenizer, model, prompt: str, posttrained: bool):
    if posttrained:
        text = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        input_mode = "chat_template_without_thinking"
    else:
        text = prompt
        input_mode = "raw_continuation"
    return tokenizer(text, return_tensors="pt").to(model.device), input_mode


def decode_new_tokens(tokenizer, output_ids: torch.Tensor, input_length: int) -> str:
    return tokenizer.decode(output_ids[0][input_length:], skip_special_tokens=True)


def run_prompt(model, tokenizer, prompt: str, posttrained: bool) -> dict:
    inputs, input_mode = prepare_inputs(tokenizer, model, prompt, posttrained)
    input_length = inputs["input_ids"].shape[1]

    with torch.inference_mode():
        greedy = model.generate(
            **inputs,
            do_sample=False,
            max_new_tokens=MAX_NEW_TOKENS,
            output_scores=True,
            return_dict_in_generate=True,
        )

    metrics = [distribution_metrics(score[0]) for score in greedy.scores[:METRIC_STEPS]]
    samples = []
    for seed in SAMPLE_SEEDS:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        with torch.inference_mode():
            sampled = model.generate(
                **inputs,
                do_sample=True,
                temperature=0.7,
                top_p=0.8,
                max_new_tokens=MAX_NEW_TOKENS,
            )
        samples.append(
            {
                "seed": seed,
                "text": decode_new_tokens(tokenizer, sampled, input_length),
            }
        )

    return {
        "input_mode": input_mode,
        "greedy_text": decode_new_tokens(tokenizer, greedy.sequences, input_length),
        "mean_top1_first_32": round(sum(item[0] for item in metrics) / len(metrics), 6),
        "mean_entropy_bits_first_32": round(
            sum(item[1] for item in metrics) / len(metrics), 6
        ),
        "first_32_metrics": [
            {"step": index + 1, "top1": top1, "entropy_bits": entropy}
            for index, (top1, entropy) in enumerate(metrics)
        ],
        "samples": samples,
    }


def aggregate(results: dict) -> dict:
    summary = {}
    for model_name, prompt_results in results.items():
        summary[model_name] = {
            "mean_top1_first_32": round(
                sum(result["mean_top1_first_32"] for result in prompt_results.values())
                / len(prompt_results),
                6,
            ),
            "mean_entropy_bits_first_32": round(
                sum(
                    result["mean_entropy_bits_first_32"]
                    for result in prompt_results.values()
                )
                / len(prompt_results),
                6,
            ),
        }
    return summary


def plot_summary(summary: dict, path: Path):
    names = ["Base", "Post-trained"]
    keys = ["base", "posttrained"]
    top1 = [summary[key]["mean_top1_first_32"] for key in keys]
    entropy = [summary[key]["mean_entropy_bits_first_32"] for key in keys]

    figure, (left, right) = plt.subplots(1, 2, figsize=(10, 4.5))
    for axis, values, title, color in (
        (left, top1, "Mean top-1 probability (first 32 tokens)", "#4A90D9"),
        (right, entropy, "Mean entropy in bits (first 32 tokens)", "#E74C3C"),
    ):
        bars = axis.bar(names, values, color=color, alpha=0.85)
        axis.set_title(title)
        axis.set_ylim(0, max(values) * 1.2)
        for bar, value in zip(bars, values):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.3f}",
                ha="center",
                va="bottom",
            )

    figure.suptitle("Qwen3-8B: base vs post-trained across five prompts")
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")


def main():
    results = {}
    for model_name, model_id, posttrained in MODELS:
        print(f"Loading {model_id}...", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            local_files_only=True,
        )
        model.eval()

        results[model_name] = {}
        for prompt in PROMPTS:
            print(f"  {model_name}: {prompt['id']}", flush=True)
            results[model_name][prompt["id"]] = run_prompt(
                model, tokenizer, prompt["text"], posttrained
            )

        del model
        torch.cuda.empty_cache()

    summary = aggregate(results)
    payload = {
        "models": {
            "base": "Qwen/Qwen3-8B-Base",
            "posttrained": "Qwen/Qwen3-8B",
        },
        "prompts": PROMPTS,
        "generation": {
            "max_new_tokens": MAX_NEW_TOKENS,
            "metric_steps": METRIC_STEPS,
            "sampling": {"temperature": 0.7, "top_p": 0.8, "seeds": SAMPLE_SEEDS},
        },
        "results": results,
    }
    Path("multi_prompt_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    Path("multi_prompt_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    plot_summary(summary, Path("multi_prompt_metrics.png"))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
