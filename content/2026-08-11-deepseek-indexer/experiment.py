#!/usr/bin/env python3
"""
Lightning Indexer 机制演示（先筛后算）
========================================
复现 DeepSeek-V4 CSA 里 Lightning Indexer 的核心链路：
  压缩块 → indexer 打分（ReLU 淘汰）→ top-k 选择 → 核心注意力只算选中的块

任务：associative recall（联想检索）——序列开头埋 K 对 (key, value)，
末尾放一个 query key，模型必须从开头检索出对应 value。注意力天然聚焦在
少数"关键块"上，是稀疏注意力最典型的受益场景。

三个指标：
  1. 召回率：indexer 挑出的 top-k 块，覆盖了多少"真实注意力权重"（论文口径：99.7%）
  2. 核心注意力 FLOPs：全量（对全部 T 块） vs 稀疏（只对 k 块）
  3. 输出质量：稀疏注意力的输出 vs 全量注意力的输出，余弦相似度

训练逻辑（呼应论文 §4.2.2 的 warmup 阶段）：
  阶段一：小 Transformer 用密集注意力正常训练（模型学会检索关键块）
  阶段二：用密集注意力的真实权重当老师（soft label），训练 indexer 模仿

⚠️ 机制演示，不是官方性能基准。自包含，CPU 可跑（约 1-2 分钟）。
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(42)

# ---------------------------------------------------------------------------
# 配置（数值远小于 V4，但结构一致：m=4 压缩率、多头加权打分、top-k 选择）
# ---------------------------------------------------------------------------
SEQ_LEN = 256           # 序列长度（V4 正文主例 128K，这里缩小便于演示）
M = 4                   # 压缩率 compress_rate_csa（V4 也是 4）
N_BLOCKS = SEQ_LEN // M  # 压缩后的块数 T（V4 主例：128K/4 = 32K 块）
N_HEADS = 2             # indexer 打分 head 数（V4: 64）
HIDDEN = 64             # 隐藏维度
N_PAIRS = 4             # 序列开头埋几对 (key, value)

VOCAB = 32
KEY_MIN, KEY_MAX = 2, 16      # key/value 取值域
NOISE_MIN = 17                # 噪音 token 取值域


def make_batch(batch_size):
    """associative recall：开头 N_PAIRS 对 (key,value)，末尾 query，预测对应 value。"""
    seqs = torch.randint(NOISE_MIN, VOCAB, (batch_size, SEQ_LEN + 1))
    query_keys = []
    for b in range(batch_size):
        keys = torch.randint(KEY_MIN, KEY_MAX, (N_PAIRS,))
        vals = torch.randint(KEY_MIN, KEY_MAX, (N_PAIRS,))
        # 开头埋 N_PAIRS 对 (key, value)
        for i, (k, v) in enumerate(zip(keys, vals)):
            seqs[b, 2 * i] = k
            seqs[b, 2 * i + 1] = v
        # 末尾放 query key，目标 = 对应 value
        qi = torch.randint(0, N_PAIRS, (1,)).item()
        seqs[b, SEQ_LEN - 1] = keys[qi]
        seqs[b, SEQ_LEN] = vals[qi]
        query_keys.append(qi)
    return seqs[:, :-1], seqs[:, 1:]


class MiniTransformer(nn.Module):
    """两层注意力 + 单层 FFN 迷你 Transformer：产生真实注意力权重（老师信号来源）。

    两层结构是 associative recall 的经典配置：第一层检索 key 位置，
    第二层把 value 信息汇聚到 query（一层注意力做不好这个任务）。
    """

    def __init__(self):
        super().__init__()
        self.emb = nn.Embedding(VOCAB, HIDDEN)
        self.attn1 = nn.MultiheadAttention(HIDDEN, 1, batch_first=True, bias=False)
        self.attn2 = nn.MultiheadAttention(HIDDEN, 1, batch_first=True, bias=False)
        self.ff = nn.Sequential(nn.Linear(HIDDEN, 4 * HIDDEN), nn.GELU(), nn.Linear(4 * HIDDEN, HIDDEN))
        self.n1 = nn.LayerNorm(HIDDEN)
        self.n2 = nn.LayerNorm(HIDDEN)
        self.n3 = nn.LayerNorm(HIDDEN)
        self.out = nn.Linear(HIDDEN, VOCAB)

    def _mask(self):
        return torch.tril(torch.ones(SEQ_LEN, SEQ_LEN) * -1e9)

    def forward(self, x, return_attn=False):
        h = self.emb(x)
        m = self._mask()
        a1, attn = self.attn1(h, h, h, attn_mask=m)
        h = self.n1(h + a1)
        a2, _ = self.attn2(h, h, h, attn_mask=m)
        h = self.n2(h + a2)
        h = self.n3(h + self.ff(h))
        logits = self.out(h)
        if return_attn:
            return logits, attn, h  # attn [B, 1, S, S]（第一层，检索层）
        return logits


class LightningIndexer(nn.Module):
    """结构对齐 V4（论文 eq.13-17）：多头打分 + ReLU 淘汰 + 加权求和。

    简化：跳过低秩双投影（W_DQ/W_IUQ），直接用块表示打分——机制等价。
    """

    def __init__(self):
        super().__init__()
        self.q_proj = nn.ModuleList([nn.Linear(HIDDEN, HIDDEN) for _ in range(N_HEADS)])
        self.k_proj = nn.Linear(HIDDEN, HIDDEN)
        self.w_proj = nn.Linear(HIDDEN, N_HEADS)

    def score(self, q_hidden, block_keys):
        """对每个 query 给全部块打分：Σ_h w_h · ReLU(q_h · K^IComp)"""
        scores_h = []
        for h in range(N_HEADS):
            q_h = self.q_proj[h](q_hidden)                      # [B, S, D]
            s_h = F.relu(q_h @ block_keys.transpose(-1, -2))    # [B, S, T] ReLU 淘汰
            scores_h.append(s_h)
        w = self.w_proj(q_hidden)                                # [B, S, H]
        score = torch.stack(scores_h, dim=-1)                    # [B, S, T, H]
        return (score * w.unsqueeze(2)).sum(dim=-1)              # [B, S, T]

    def forward(self, q_hidden, block_keys, k):
        scores = self.score(q_hidden, block_keys)
        return scores.topk(k, dim=-1).indices


def compress(hidden, m=M):
    """块压缩：每 m 个 token 平均成一个块表示（V4 用 softmax 门控池化，等价演示）。"""
    b, s, d = hidden.shape
    n = s // m
    return hidden[:, : n * m].view(b, n, m, d).mean(dim=2)       # [B, T, D]


def block_attn_weights(probs, m=M):
    """token 级注意力权重 → 块级（真实注意力的老师信号）。"""
    probs = probs.squeeze(1)                                     # [B, S, S]
    b, s1, s2 = probs.shape
    n = s2 // m
    w = probs[:, :, : n * m].view(b, s1, n, m).sum(dim=-1)       # [B, S, T]
    return w / w.sum(dim=-1, keepdim=True).clamp_min(1e-9)


# ---------------------------------------------------------------------------
# 阶段一：训练小 Transformer（密集注意力 warmup，对应论文 1T tokens 阶段）
# ---------------------------------------------------------------------------
print("=" * 62)
print("阶段一：训练小 Transformer（密集注意力 warmup，对应论文 1T tokens 阶段）")
print("=" * 62)
model = MiniTransformer()
opt = torch.optim.AdamW(model.parameters(), lr=3e-3)

for step in range(800):
    x, y = make_batch(32)
    logits = model(x)
    loss = F.cross_entropy(logits.reshape(-1, VOCAB), y.reshape(-1))
    opt.zero_grad()
    loss.backward()
    opt.step()
    if step % 200 == 0:
        print(f"  step {step:4d}  loss {loss.item():.4f}")

model.eval()
x, y = make_batch(16)
with torch.no_grad():
    _, probs, h_eval = model(x, return_attn=True)  # 真实注意力权重（老师）[B,1,S,S]
teacher = block_attn_weights(probs)           # 块级老师信号 [B, S, T]
conc = (teacher > 0.1).float().mean().item()   # 平均每 query 集中多少块
print(f"  老师信号：平均每个 query 的注意力集中在 {conc:.2f} 块（共 {N_BLOCKS} 块）")

# ---------------------------------------------------------------------------
# 阶段二：训练 Lightning Indexer（老师 = 密集注意力真实权重，soft label 监督）
# ---------------------------------------------------------------------------
print("\n" + "=" * 62)
print("阶段二：训练 Indexer（老师 = 密集注意力真实权重，soft label 监督）")
print("=" * 62)
indexer = LightningIndexer()
opt2 = torch.optim.AdamW(indexer.parameters(), lr=5e-3)

for step in range(500):
    x, y = make_batch(32)
    with torch.no_grad():
        _, probs_t, h = model(x, return_attn=True)   # 真实注意力当老师（与评测同口径）
        teacher_b = block_attn_weights(probs_t)
        block_keys = compress(h)                     # indexer 检索键来自深层表示
    scores = indexer.score(h, block_keys)            # 连续打分 [B, S, T]
    loss = F.cross_entropy(scores.reshape(-1, N_BLOCKS), teacher_b.reshape(-1, N_BLOCKS))
    opt2.zero_grad()
    loss.backward()
    opt2.step()
    if step % 200 == 0:
        print(f"  step {step:4d}  loss {loss.item():.4f}")

# ---------------------------------------------------------------------------
# 评测：召回率 × FLOPs × 输出质量（基线统一为块级全量注意力）
# ---------------------------------------------------------------------------
print("\n" + "=" * 62)
print("评测：不同 k 下的 召回率 / 核心注意力 FLOPs / 输出质量")
print("=" * 62)
with torch.no_grad():
    x, y = make_batch(16)                        # 重新生成评测批，保证一致
    _, probs, h = model(x, return_attn=True)
    teacher = block_attn_weights(probs)
    block_keys = compress(h)
    block_h = compress(h)

    # 统一打分器：indexer 的连续分数（全量与稀疏共用同一套分数，口径一致）
    scores_all = indexer.score(h, block_keys)                    # [B, S, T]
    full_probs = F.softmax(torch.tril(scores_all), dim=-1)       # 全量基线
    full_out = full_probs @ block_h                              # 块级全量输出

    # query 位置：末尾 N_PAIRS 个 token（任务关键：需要检索开头对应块）
    q_pos = slice(-N_PAIRS, None)

    print(f"  {'k':>3} {'召回率':>8} {'q-召回率':>9} {'FLOPs节省':>9} {'输出相似度':>10}")
    for k in [2, 4, 8, 16, 64]:
        sel = indexer(h, block_keys, k)                         # [B, S, k]
        gathered = teacher.gather(-1, sel)
        recall = gathered.sum(dim=-1).mean().item()             # 1) 召回率（全部位置）
        recall_q = gathered[:, q_pos].sum(dim=-1).mean().item() # 1b) query 位置召回率
        T_full, T_sparse = N_BLOCKS, k                          # 2) 核心注意力点积次数
        neg = torch.finfo(scores_all.dtype).min
        sparse_scores = torch.full_like(scores_all, neg)
        sparse_scores.scatter_(-1, sel, scores_all.gather(-1, sel))
        sparse_probs = F.softmax(torch.tril(sparse_scores), dim=-1)
        sparse_out = sparse_probs @ block_h                     # 3) 稀疏输出
        cos = F.cosine_similarity(sparse_out, full_out, dim=-1).mean().item()
        print(f"  {k:>3} {recall*100:>7.1f}% {recall_q*100:>8.1f}% {T_full/T_sparse:>8.1f}x {cos:>9.4f}")

print()
print("结论：")
print("  · 召回率：k 越大覆盖的真实注意力越多（论文验收口径 99.7% 对应大 k）")
print("  · FLOPs：核心注意力从全量 T 块降到 k 块（V4 主例：32K 块 → 512 块 = 64×）")
print("  · 输出相似度：稀疏输出与块级全量输出的一致性（漏块只是信息少一点）")
print("  ⚠️ 机制演示，不是官方性能基准；indexer 打分本身的成本未计入（V4 中为 FP4 廉价路径）")
