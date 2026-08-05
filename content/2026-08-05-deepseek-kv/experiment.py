#!/usr/bin/env python3
"""K=V + Partial RoPE + de-RoPE mechanism demo for the DeepSeek-V4 article.

This is a *mechanism demonstration*, not a model benchmark. It verifies three
design paths with tiny random vectors (16 dims, last 2 rotated; the real
DeepSeek-V4-Pro uses 512 dims with the last 64 rotated, see config.json):

  1. A compressed entry can serve as both key and value (MQA path).
  2. With Partial RoPE, QK inner products depend on relative distance only in
     the rotated dims; content dims are position-free.
  3. de-RoPE (rotate the attention output by -i) restores absolute-position
     invariance: same content + same distance => same output.

Run:  python3 experiment.py
"""

from __future__ import annotations

import numpy as np

rng = np.random.default_rng(42)

C = 16          # head dimension (demo; real config: 512)
R = 2           # rotated (rope) dims, the LAST R dims (demo; real: 64)


def rot_matrix(pos: int, rope_dim: int, base: float = 100.0) -> np.ndarray:
    """Block-diagonal 2x2 rotation matrix applied to the last rope_dim dims."""
    M = np.eye(C)
    for k in range(rope_dim // 2):
        theta = pos / base ** (2.0 * k / rope_dim)
        idx = C - rope_dim + 2 * k
        c, s = np.cos(theta), np.sin(theta)
        M[idx:idx + 2, idx:idx + 2] = [[c, -s], [s, c]]
    return M


def rope(x: np.ndarray, pos: int) -> np.ndarray:
    return rot_matrix(pos, R) @ x


# ---------------------------------------------------------------- Part 1
print("== 1) K=V shared entry (MQA path) ==")
n_entries = 6
entries = rng.normal(size=(n_entries, C))          # compressed KV entries
q = rng.normal(size=(1, C))                        # one query head
scores = q @ entries.T                              # Q @ K^T (K = entries)
weights = np.exp(scores - scores.max())
weights = weights / weights.sum()                   # softmax
out = weights @ entries                             # V = entries
identity_ok = np.allclose(scores, q @ entries.T) and np.allclose(out, weights @ entries)
print(f"entries shape={entries.shape}, scores shape={scores.shape}, out shape={out.shape}")
print(f"same array used as K and V: {identity_ok}")
print(f"out (first 4 dims): {np.round(out[:4], 4)}")

# ---------------------------------------------------------------- Part 2
print("\n== 2) Partial RoPE: position lives only in the last R dims ==")
v = rng.normal(size=C)
# absolute positions with the same distance d=3
pairs = [(5, 8), (105, 108)]
row = []
for i, j in pairs:
    q_i = rope(q[0], i)
    k_j = rope(v, j)
    row.append(float(q_i @ k_j))
print(f"QK inner product for distance d=3 at absolute (5,8) and (105,108): "
      f"{row[0]:.4f} vs {row[1]:.4f}  (equal => relative only)")
# content perturbation: perturb only non-rope dims => inner product changes
# identically regardless of absolute position
v2 = v.copy()
v2[: C - R] += 0.7 * rng.normal(size=C - R)
rows2 = []
for i, j in pairs:
    rows2.append(float(rope(q[0], i) @ rope(v2, j)))
print(f"after perturbing only content dims: {rows2[0]:.4f} vs {rows2[1]:.4f} "
      f"(equal => content shift position-free)")
print(f"rope-only shift changes inner product: "
      f"{row[0]:.4f} -> {float(rope(q[0], 6) @ rope(v, 9)):.4f} (d=3 same, abs shifted)")

# ---------------------------------------------------------------- Part 3
print("\n== 3) de-RoPE: output rotation by -i removes absolute position ==")
a = 0.4                                       # attention weight (single entry)
naive = []                                    # outputs WITHOUT de-RoPE
derope = []                                   # outputs WITH de-RoPE
for i, j in pairs:
    o_naive = a * rope(v, j)                  # naive: V carries rotation R_j
    o_derope = rope(o_naive, -i)              # de-RoPE: rotate by -i
    naive.append(o_naive)
    derope.append(o_derope)
d_naive = np.max(np.abs(naive[0] - naive[1]))
d_derope = np.max(np.abs(derope[0] - derope[1]))
print(f"max|diff| between outputs at (5,8) and (105,108), same content:")
print(f"  without de-RoPE: {d_naive:.6f}   (absolute position leaks in)")
print(f"  with de-RoPE:    {d_derope:.2e}   (absolute-position invariant)")
print(f"de-RoPE output (first 4 dims): {np.round(derope[0][:4], 4)}")
# relative distance is still encoded: different d => different de-roped output
out_d2 = rope(a * rope(v, 8), -5)   # d = 3
out_d4 = rope(a * rope(v, 9), -5)   # d = 4
print(f"different distance d=3 vs d=4 still differ (max|diff|): "
      f"{np.max(np.abs(out_d2 - out_d4)):.4f}  (relative position retained)")
