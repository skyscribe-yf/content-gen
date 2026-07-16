"""Extract attention weights from Qwen3-8B for self-referential sentence."""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import json

MODEL_PATH = "/home/skyscribe/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
OUTPUT_PATH = "/home/skyscribe/srcs/content-gen/content/2026-07-25-Transformer全景/attention_data.json"

SENTENCE = "这篇文章用一句话走完Transformer全过程"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

print("Loading model (CPU, this will take a minute)...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    dtype=torch.float32,
    device_map="cpu",
    trust_remote_code=True,
    output_attentions=True,  # not enough alone, need forward pass kwarg
)
model.eval()

# Tokenize
inputs = tokenizer(SENTENCE, return_tensors="pt")
input_ids = inputs["input_ids"]
tokens = [tokenizer.decode([tid]) for tid in input_ids[0]]
print(f"Sentence: {SENTENCE}")
print(f"Tokens ({len(tokens)}): {tokens}")
print(f"IDs: {input_ids[0].tolist()}")

# Forward pass with attention outputs
print("Running forward pass...")
with torch.no_grad():
    outputs = model(input_ids, output_attentions=True)

# outputs.attentions is a tuple of (batch, num_heads, seq_len, seq_len) per layer
attentions = outputs.attentions
num_layers = len(attentions)
print(f"Got attention from {num_layers} layers")

# Extract layers 1, 18, 36 (0-indexed: 0, 17, 35)
# Qwen3-1.7B has 28 layers. Pick layer 1, 14, 28 (mapped from 8B's layer 1, 18, 36)
target_layers = {
    "layer_1": 0,
    "layer_14": 13,
    "layer_28": 27,
}

result = {
    "sentence": SENTENCE,
    "tokens": tokens,
    "token_ids": input_ids[0].tolist(),
    "num_layers": num_layers,
    "num_heads": attentions[0].shape[1],
    "layers": {}
}

for name, layer_idx in target_layers.items():
    attn = attentions[layer_idx]  # shape: [batch=1, num_heads, seq_len, seq_len]
    weights = attn[0].float().numpy()  # [num_heads, seq_len, seq_len]
    # Average across heads for a summary
    avg_weights = weights.mean(axis=0)  # [seq_len, seq_len]
    result["layers"][name] = {
        "index": layer_idx,
        "shape": list(weights.shape),
        "avg_attention": avg_weights.tolist(),
        # Per-head: too much data, just store top heads
        "head_summary": {}
    }
    # For each head, note which token pairs have strongest attention
    seq_len = weights.shape[1]
    for h in range(min(4, weights.shape[0])):  # first 4 heads
        head_weights = weights[h]
        # Find top-3 token pairs per query position
        top_pairs = {}
        for q in range(seq_len):
            topk = head_weights[q].argsort()[-3:][::-1]  # top 3
            top_pairs[tokens[q]] = [(tokens[k], float(head_weights[q][k])) for k in topk]
        result["layers"][name]["head_summary"][f"head_{h}"] = top_pairs

# Also extract hidden states for dimension tracking
with torch.no_grad():
    outputs_full = model(input_ids, output_hidden_states=True)
hidden = outputs_full.hidden_states
result["hidden_size"] = hidden[0].shape[-1]
result["num_hidden_layers"] = len(hidden) - 1  # includes embedding layer

# Save
with open(OUTPUT_PATH, "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\nSaved to {OUTPUT_PATH}")
print(f"Hidden size: {result['hidden_size']}")
print(f"Layers: {result['num_hidden_layers']}")
print(f"Num attention heads: {result['num_heads']}")
