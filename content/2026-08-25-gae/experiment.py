#!/usr/bin/env python3
"""GAE 篇数字事实验证（2026-08-24 蒙特卡洛）。

设定：线性走廊随机游走（状态 1..N，0 与 N+1 为吸收端），随机策略（左右各 0.5），
  R_t = N(0, sigma_r^2) 过程噪声 + 两端终止奖励。
真实 V* 迭代精确求解；critic 带误差 Vhat = V* + e（系统性低估 + 白噪声）。
对 lambda ∈ {0, 0.5, 0.9, 0.95, 0.99, 1}：
  - A_t = Σ_l (γλ)^l δ_{t+l}, δ_t = R_t + γVhat(s_{t+1}) - Vhat(s_t)
  - bias  = E[Ahat - Astar]，var = Var(Ahat)，mse = E[(Ahat - Astar)^2]
输出表格 + 正文反差数字。
"""
import numpy as np

rng = np.random.default_rng(42)

N = 30
GAMMA = 0.99
SIGMA_R = 1.0
REWARD_GOOD = +2.0
REWARD_BAD = -2.0
T = 200
S0 = N // 2

# ---- 1. 精确求解 V*（随机策略）----
V = np.zeros(N + 2)
V[0] = REWARD_BAD
V[N + 1] = REWARD_GOOD
for _ in range(200000):
    Vn = V.copy()
    for s in range(1, N + 1):
        Vn[s] = 0.5 * GAMMA * (V[s - 1] + V[s + 1])
    if np.max(np.abs(Vn - V)) < 1e-13:
        V = Vn
        break
    V = Vn

# ---- 2. critic 误差：系统性低估 + 白噪声 ----
e_bias = 0.12 * np.max(np.abs(V))
e_noise = rng.normal(0, 0.05 * np.max(np.abs(V)), N + 2)
e = np.zeros(N + 2)
e[1 : N + 1] = e_bias + e_noise[1 : N + 1]
Vhat = V + e

# ---- 3. 蒙特卡洛采样 ----
M = 600_000
s = np.full(M, S0, dtype=int)
S = np.zeros((M, T), dtype=int)
R = np.zeros((M, T))
done = np.zeros((M, T), dtype=bool)
for t in range(T):
    S[:, t] = s
    move = rng.choice([-1, 1], size=M)
    s_next = s + move
    r = rng.normal(0, SIGMA_R, M)
    hit_l = s_next <= 0
    hit_r = s_next >= N + 1
    r[hit_l] = REWARD_BAD
    r[hit_r] = REWARD_GOOD
    R[:, t] = r
    done[:, t] = hit_l | hit_r
    s = np.clip(s_next, 0, N + 1)

# 真实优势：A*_t = R_t + γV*(s_{t+1}) - V*(s_t)
Sn = np.concatenate([S[:, 1:], S[:, -1:]], axis=1)
A_star = R + GAMMA * V[Sn] - V[S]

def gae(S, R, lam):
    Vh = Vhat[S]
    Vh_next = Vhat[Sn]
    delta = R + GAMMA * Vh_next - Vh
    A = np.zeros_like(delta)
    acc = np.zeros(M)
    for t in range(T - 1, -1, -1):
        acc = delta[:, t] + (GAMMA * lam) * acc
        A[:, t] = acc
    return A

results = {}
for lam in [0.0, 0.5, 0.9, 0.95, 0.99, 1.0]:
    A = gae(S, R, lam)
    m = ~done
    bias = (A - A_star)[m].mean()
    var = A[m].var()
    mse = ((A - A_star) ** 2)[m].mean()
    eff = 1.0 / (1.0 - GAMMA * lam)
    results[lam] = dict(bias=float(bias), var=float(var), mse=float(mse), eff=eff)

print(f"{'λ':>6} {'偏差':>10} {'方差':>12} {'MSE':>12} {'有效视野':>10}")
for lam, d in results.items():
    print(f"{lam:>6.2f} {d['bias']:>10.4f} {d['var']:>12.4f} {d['mse']:>12.4f} {d['eff']:>10.2f}")

v0, v05, v95, v1 = results[0.0]["var"], results[0.5]["var"], results[0.95]["var"], results[1.0]["var"]
print()
print(f"λ=1 方差 / λ=0.95 方差 = {v1 / v95:.1f} 倍")
print(f"λ=1 方差 / λ=0.5 方差  = {v1 / v05:.1f} 倍")
print(f"λ=1 方差 / λ=0 方差    = {v1 / v0:.1f} 倍")
print(f"bias(λ=0)={results[0.0]['bias']:.4f}  bias(λ=0.95)={results[0.95]['bias']:.4f}  bias(λ=1)={results[1.0]['bias']:.4f}")
print(f"MSE 最小 λ: {min(results, key=lambda k: results[k]['mse'])}")
print(f"γλ=0.95*0.99={0.95*0.99:.4f} → 有效视野 {1/(1-0.95*0.99):.1f} 步")
print(f"γλ=0.99 → 有效视野 {1/(1-0.99):.0f} 步")
