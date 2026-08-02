"""
Qwen3-8B base vs instruct token probability comparison.
Runs on an AutoDL RTX 4090 in BF16.

Usage:
  python experiment_sft_compare.py

Outputs:
  - top10_base.json: top-10 token probs from base model
  - top10_instruct.json: top-10 token probs from instruct model
  - comparison.png: side-by-side bar chart
"""

import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

PROMPT = "请解释什么是梯度下降"
MODEL_BASE = "Qwen/Qwen3-8B-Base"
MODEL_INSTRUCT = "Qwen/Qwen3-8B"
TOP_K = 10


def get_top_k_probs(model_name: str, prompt: str, is_instruct: bool = False):
    """Load model, run inference, return top-k token probabilities."""
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()

    if is_instruct:
        # Apply chat template for instruct model
        messages = [{"role": "user", "content": prompt}]
        input_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    else:
        # Base model: plain text continuation
        input_text = prompt

    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model(**inputs)
        # Get logits for the next token position (last position)
        next_token_logits = outputs.logits[0, -1, :]
        probs = torch.softmax(next_token_logits, dim=-1)

    top_k_probs, top_k_indices = torch.topk(probs, TOP_K)
    tokens = [tokenizer.decode([idx.item()]) for idx in top_k_indices]

    result = [
        {"token": t, "probability": round(p.item(), 4)}
        for t, p in zip(tokens, top_k_probs)
    ]

    # Also get the generated text for reference
    with torch.no_grad():
        generated = model.generate(
            **inputs, max_new_tokens=100, do_sample=False, temperature=1.0
        )
    generated_text = tokenizer.decode(
        generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )

    # Free GPU memory
    del model
    torch.cuda.empty_cache()

    return result, generated_text


def plot_comparison(base_data, instruct_data, output_path="comparison.png"):
    """Plot side-by-side bar chart of top-k token probabilities."""
    import matplotlib.pyplot as plt
    import matplotlib

    matplotlib.rcParams["font.sans-serif"] = [
        "Noto Sans CJK SC",
        "SimHei",
        "DejaVu Sans",
    ]
    matplotlib.rcParams["axes.unicode_minus"] = False

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Base model
    tokens_b = [d["token"] for d in base_data]
    probs_b = [d["probability"] for d in base_data]
    ax1.barh(range(len(tokens_b)), probs_b, color="#4A90D9", alpha=0.8)
    ax1.set_yticks(range(len(tokens_b)))
    ax1.set_yticklabels(tokens_b, fontsize=12)
    ax1.set_xlabel("Probability", fontsize=11)
    ax1.set_title("Qwen3-8B Base\n(top-10 tokens)", fontsize=13)
    ax1.invert_yaxis()
    for i, v in enumerate(probs_b):
        ax1.text(v + 0.005, i, f"{v:.3f}", va="center", fontsize=10)

    # Instruct model
    tokens_i = [d["token"] for d in instruct_data]
    probs_i = [d["probability"] for d in instruct_data]
    ax2.barh(range(len(tokens_i)), probs_i, color="#E74C3C", alpha=0.8)
    ax2.set_yticks(range(len(tokens_i)))
    ax2.set_yticklabels(tokens_i, fontsize=12)
    ax2.set_xlabel("Probability", fontsize=11)
    ax2.set_title("Qwen3-8B Instruct\n(top-10 tokens)", fontsize=13)
    ax2.invert_yaxis()
    for i, v in enumerate(probs_i):
        ax2.text(v + 0.005, i, f"{v:.3f}", va="center", fontsize=10)

    plt.suptitle(
        f'Prompt: "{PROMPT}"\nNext-token probability distribution comparison',
        fontsize=14,
        y=1.02,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Chart saved to {output_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("Qwen3-8B Base vs Instruct: Token Probability Comparison")
    print(f"Prompt: {PROMPT}")
    print("=" * 60)

    # Base model
    print("\n[1/2] Loading base model...")
    base_result, base_text = get_top_k_probs(MODEL_BASE, PROMPT, is_instruct=False)
    print(f"Base model top-10: {json.dumps(base_result, ensure_ascii=False, indent=2)}")
    print(f"Base model output: {base_text[:200]}...")

    with open("top10_base.json", "w", encoding="utf-8") as f:
        json.dump(
            {"prompt": PROMPT, "top10": base_result, "generated": base_text},
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Instruct model
    print("\n[2/2] Loading instruct model...")
    instruct_result, instruct_text = get_top_k_probs(
        MODEL_INSTRUCT, PROMPT, is_instruct=True
    )
    print(
        f"Instruct model top-10: {json.dumps(instruct_result, ensure_ascii=False, indent=2)}"
    )
    print(f"Instruct model output: {instruct_text[:200]}...")

    with open("top10_instruct.json", "w", encoding="utf-8") as f:
        json.dump(
            {"prompt": PROMPT, "top10": instruct_result, "generated": instruct_text},
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Plot
    print("\n[3/3] Generating comparison chart...")
    plot_comparison(base_result, instruct_result)

    # Summary
    print(f"\nBase top-1 probability: {base_result[0]['probability']:.4f}")
    print(f"Instruct top-1 probability: {instruct_result[0]['probability']:.4f}")
    print(f"Distribution narrowing ratio: {instruct_result[0]['probability'] / base_result[0]['probability']:.2f}x")
    print("\nDone!")
