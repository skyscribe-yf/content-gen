#!/usr/bin/env python3
"""mHC mechanism demo: Sinkhorn convergence + 60-layer product spectral norm.

实验 1: Sinkhorn-Knopp 迭代把无约束矩阵投影到双随机流形,
        观察行和/列和误差的指数收敛, 以及投影后谱范数 <= 1.
实验 2: 随机生成 60 层残差映射矩阵, 对比
        (a) 无约束矩阵连乘的谱范数 (~ 数千, 复现 Amax Gain ~3000 机制)
        (b) 双随机矩阵连乘的谱范数 (恒 <= 1)

机制演示, 不是官方性能基准.
"""

import numpy as np


def sinkhorn(M, iters=20):
    """交替行列归一化, 把非负矩阵投影到双随机矩阵."""
    for _ in range(iters):
        M = M / M.sum(axis=1, keepdims=True)   # 行归一化
        M = M / M.sum(axis=0, keepdims=True)   # 列归一化
    return M


def doubly_stochastic_matrix(n, seed=0):
    """生成一个随机的双随机矩阵: exp 取正 + Sinkhorn 投影."""
    rng = np.random.default_rng(seed)
    return sinkhorn(np.exp(rng.normal(size=(n, n))), iters=100)


def main():
    n = 4  # 与 V4 的 n_hc 一致
    layers = 60  # 与 V4-Pro 层数(61)同一量级

    # ---- 实验 1: Sinkhorn 收敛 ----
    rng = np.random.default_rng(42)
    M0 = np.exp(rng.normal(size=(n, n)))  # 未归一化的正矩阵
    print("=" * 64)
    print(f"实验 1: Sinkhorn 迭代收敛 (n={n}, t_max=20)")
    print("=" * 64)
    M = M0.copy()
    for t in range(1, 21):
        M = M / M.sum(axis=1, keepdims=True)
        M = M / M.sum(axis=0, keepdims=True)
        row_err = np.abs(M.sum(axis=1) - 1).max()
        col_err = np.abs(M.sum(axis=0) - 1).max()
        if t in (1, 2, 3, 5, 10, 20):
            print(f"  iter {t:2d}: 行和误差={row_err:.2e}  列和误差={col_err:.2e}")
    spec = np.linalg.norm(M, 2)
    print(f"  20 次迭代后: 谱范数 ||A||_2 = {spec:.6f} (<=1: {spec <= 1.0 + 1e-6})")
    print(f"  行和 = {M.sum(axis=1)}  列和 = {M.sum(axis=0)}")
    print()

    # ---- 实验 2: 60 层连乘谱范数对比 ----
    print("=" * 64)
    print(f"实验 2: {layers} 层残差映射连乘的谱范数")
    print("=" * 64)

    # (a) 无约束矩阵: 每层沿同一主导方向 v 放大 1+u 倍 (u~5%-25%).
    #     单层谱范数 = 1+u "看似无害", 但 60 层连乘 = ∏(1+u) 指数爆炸.
    #     这正是 Amax Gain 的测量口径: 复合映射的最坏情况放大倍数.
    results = {}
    rng_v = np.random.default_rng(7)
    v = rng_v.normal(size=n)
    v = v / np.linalg.norm(v)          # 固定主导方向 (模拟各层共享的放大轴)
    for trial in range(5):
        rng = np.random.default_rng(trial)
        P = np.eye(n)
        for _ in range(layers):
            u = rng.uniform(0.05, 0.25)  # 每层随机放大 5%-25%
            A = (1 + u) * np.outer(v, v)  # 谱范数 = 1+u, 看似无害
            P = A @ P
        results.setdefault("unconstrained", []).append(np.linalg.norm(P, 2))

    # (b) 双随机矩阵 (mHC 约束)
    for trial in range(5):
        P = np.eye(n)
        for l in range(layers):
            A = doubly_stochastic_matrix(n, seed=trial * 100 + l)
            P = A @ P
        results.setdefault("doubly_stochastic", []).append(np.linalg.norm(P, 2))

    u_norms = results["unconstrained"]
    d_norms = results["doubly_stochastic"]
    print(f"  无约束矩阵   连乘谱范数: max={max(u_norms):8.1f}  (论文 HC 峰值 ~3000)")
    print(f"  双随机矩阵   连乘谱范数: max={max(d_norms):.4f}   (论文 mHC ~1.6)")
    print(f"  改善倍数: {max(u_norms) / max(d_norms):,.0f}x")

    # 逐层观察: 无约束的谱范数指数增长, 双随机的稳定在 <=1
    rng = np.random.default_rng(0)
    P_u = np.eye(n)
    P_d = np.eye(n)
    print("\n  逐层谱范数(层 1, 10, 30, 60):")
    print(f"    {'层':>4} | {'无约束':>10} | {'双随机':>10}")
    for step in range(1, layers + 1):
        u = rng.uniform(0.05, 0.25)
        A_u = (1 + u) * np.outer(v, v)
        P_u = A_u @ P_u
        Ad = doubly_stochastic_matrix(n, seed=step)
        P_d = Ad @ P_d
        if step in (1, 10, 30, 60):
            print(f"    {step:>4} | {np.linalg.norm(P_u, 2):>10.2f} | {np.linalg.norm(P_d, 2):>10.4f}")
    print("\n结论: 无约束矩阵单层'看似无害'(谱范数 ~1.15)但 60 层连乘指数放大到几千; 双随机矩阵乘法封闭, 连乘恒 <= 1.")


if __name__ == "__main__":
    main()
