#!/usr/bin/env python3
"""
Muon 双实验（机制演示，不是官方性能基准）
实验 1：Newton-Schulz 收敛性 —— 条件数 κ 对迭代步数的影响（奇异值被拉向 1），对照 SVD 精确解
实验 2：窄谷二次型上 Adam（对角缩放）vs Muon（正交化）的更新方向特性
"""
import numpy as np


def singular_values_to_one(svs, steps=15):
    """对角阵上 NS 迭代退化为标量迭代 x ← ½x(3−x²)，返回奇异值偏离 1 的序列"""
    svs = np.asarray(svs, dtype=float).copy()
    max_dev = []
    for _ in range(steps):
        svs = 0.5 * svs * (3.0 - svs ** 2)
        max_dev.append(np.max(np.abs(svs - 1.0)))
    return max_dev


def experiment1():
    print("=" * 66)
    print("实验 1：Newton-Schulz 收敛性——奇异值从 [1/√κ, 1] 被拉向 1")
    print("（实际训练中动量平滑+梯度裁剪+归一化后 X0 已接近正交；")
    print("  本实验直接展示条件数 κ 对收敛步数的影响）")
    print("=" * 66)
    print(f"{'kappa':>6} | {'step2 偏离':>11} {'step5 偏离':>11} {'到1e-8步数':>10} {'SVD解正交误差':>12}")
    print("-" * 66)
    for kappa in (3, 8, 50, 200):
        svs = np.linspace(1.0 / np.sqrt(kappa), 1.0, 8)   # 特征值在 [1/κ, 1]
        devs = singular_values_to_one(svs)
        reached = next((i + 1 for i, d in enumerate(devs) if d < 1e-8), None)
        rng = np.random.default_rng(0)
        G = rng.standard_normal((16, 8))
        U, _, Vt = np.linalg.svd(G, full_matrices=False)
        svd_orth = np.linalg.norm((U @ Vt).T @ (U @ Vt) - np.eye(U.shape[1]))
        print(f"{kappa:>6} | {devs[1]:>11.2e} {devs[4]:>11.2e} {str(reached):>10} {svd_orth:>12.2e}")

    print("\n二阶收敛验证（κ=8，比值 dev[k+1]/dev[k]² 应接近常数）:")
    devs = singular_values_to_one(np.linspace(1.0 / np.sqrt(8.0), 1.0, 8), steps=6)
    for k in range(4):
        print(f"  dev[{k}]={devs[k]:.3e}  dev[{k+1}]/dev[{k}]^2={devs[k+1]/devs[k]**2:.2f}")


def adam_step(W, g, m, v, lr, b1=0.9, b2=0.999, eps=1e-8):
    m = b1 * m + (1 - b1) * g
    v = b2 * v + (1 - b2) * g ** 2
    mh, vh = m / (1 - b1), v / (1 - b2)
    return W - lr * mh / (np.sqrt(vh) + eps), m, v


def muon_step(W, g, M, lr, beta=0.9):
    M = beta * M + (1 - beta) * g
    X = M / (np.linalg.norm(M, 'fro') + 1e-12)
    I = np.eye(X.shape[1])
    for _ in range(5):                       # NS-5
        X = 0.5 * X @ (3 * I - X.T @ X)
    return W - lr * X, M


def experiment2():
    print("\n" + "=" * 66)
    print("实验 2：窄谷二次型 f(W)=½tr(W^T A W)，A=diag(100,1)，参数 W∈R^{2×2}")
    print("对比指标：每步更新方向与'直指最优点方向(-W)'的夹角（越小越直）")
    print("简化说明：A 对角时梯度方向接近最优方向，差异集中在更新方向的特性上")
    print("=" * 66)
    A = np.diag([100.0, 1.0])
    W0 = np.array([[1.0, 1.0], [0.01, 0.01]])
    N = 60
    print(f"{'':6} | {'首步方向偏差':>10} {'全程方向偏差均值':>12} {'60步路径长':>10} {'60步后|W|/|W0|':>12}")
    print("-" * 66)
    for name, lr0, muon in (("Adam", 0.05, False), ("Muon", 0.05, True)):
        W = W0.copy(); m = np.zeros_like(W); v = np.zeros_like(W); M = np.zeros_like(W)
        prev = W.copy(); path_len = 0.0; angs = []
        for _ in range(N):
            g = A @ W
            if muon:
                W, M = muon_step(W, g, M, lr0)
            else:
                W, m, v = adam_step(W, g, m, v, lr0)
            path_len += np.linalg.norm(W - prev)
            d = (W - prev); d /= (np.linalg.norm(d) + 1e-12)
            angs.append(np.degrees(np.arccos(np.clip(-np.sum(d * W / np.linalg.norm(W)), -1, 1))))
            prev = W.copy()
        print(f"{name:>6} | {angs[0]:>10.1f}° {np.mean(angs):>10.1f}° "
              f"{path_len:>10.3f} {np.linalg.norm(W)/np.linalg.norm(W0):>12.3f}")
    print("\n解读：Muon 正交化抹平了逐元素缩放的幅度偏置，首步方向几乎正对最优点；")
    print("全程方向偏差也更小（更接近直线）。注意：toy 只演示方向机制，")
    print("真实大模型上的收敛收益（同 token 数 loss 更低）以 Moonlight / Kimi K2 论文实证为准。")


if __name__ == "__main__":
    experiment1()
    experiment2()
