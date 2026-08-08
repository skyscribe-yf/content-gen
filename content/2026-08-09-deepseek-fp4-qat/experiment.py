#!/usr/bin/env python3
"""FP4 QAT 机制演示：STE 直通梯度 + FP4→FP8 无损反量化。

实验 1：量化不可微 → 朴素截断梯度归零、权重冻结；STE 直通梯度让训练继续。
实验 2：FP4→FP8 反量化无损性验证——FP4 子块 scale 最大/最小比值不超过阈值时，
        反量化回 FP8（E4M3）误差精确为 0；比值超阈值开始有损。

仅机制演示，不代表 DeepSeek 官方性能。NumPy 自包含，无第三方依赖。
"""
import numpy as np

# ─────────────────────────── 格式常量 ───────────────────────────
# OCP MX v1.0：FP4 E2M1，偏置 1，可表示值（正侧）
E2M1_VALUES = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
E4M3_MAX = 448.0        # FP8 E4M3 最大有限值（1.75 × 2^8）
E4M3_EMIN = -6          # 最小正规指数
SUBNORM_STEP = 2.0 ** -9  # E4M3 subnormal 最小分辨率


def quantize_e2m1(x: np.ndarray) -> np.ndarray:
    """就近取整到 E2M1 可表示值集合（输入须已在 ±6 范围内）。"""
    shape = x.shape
    flat = np.asarray(x, dtype=np.float64).ravel()
    sign = np.sign(flat)
    a = np.abs(flat)
    idx = np.argmin(np.abs(E2M1_VALUES[:, None] - a[None, :]), axis=0)
    return (sign * E2M1_VALUES[idx]).reshape(shape)


def fp4_group_quant(w: np.ndarray, group: int = 32) -> np.ndarray:
    """MXFP4 风格分组量化：每 1×group 子块一个 E8M0（2 的幂）scale。

    返回反量化后的值（= FP4 元素 × scale），供后续计算/再量化。
    """
    w = np.asarray(w, dtype=np.float64)
    rows, cols = w.shape
    q = np.zeros_like(w)
    for i in range(rows):
        for j in range(0, cols, group):
            block = w[i, j:j + group]
            maxabs = np.max(np.abs(block)) if block.size else 0.0
            if maxabs == 0.0:
                continue
            k = np.floor(np.log2(maxabs)) - 2  # 除以 ≤6 的最大 2 的幂（4）
            s = 2.0 ** k
            q[i, j:j + group] = quantize_e2m1(block / s) * s
    return q


def quantize_e4m3(x: np.ndarray) -> np.ndarray:
    """FP8 E4M3 量化（binade 舍入 + subnormal + 饱和），与 FP8 篇 experiment 一致。"""
    x = np.asarray(x, dtype=np.float64)
    y = np.clip(x, -E4M3_MAX, E4M3_MAX)
    a = np.abs(y)
    e = np.floor(np.log2(np.maximum(a, 1e-30)))
    e = np.clip(e, E4M3_EMIN, 8)
    m = np.round(y / (2.0 ** e) * 8.0) / 8.0  # 3 位尾数
    q = m * 2.0 ** e
    sub = a < 2.0 ** E4M3_EMIN
    q = np.where(sub, np.round(y / SUBNORM_STEP) * SUBNORM_STEP, q)
    return q


# ─────────────────────────── 实验 1：STE vs 梯度截断 ───────────────────────────
def toy_mlp_forward(x, w1, w2, quantize_weights):
    """2 层 MLP（8→64→1，tanh）。quantize_weights=True 时权重先过 FP4。"""
    w1q = fp4_group_quant(w1, 32) if quantize_weights else w1
    w2q = fp4_group_quant(w2, 32) if quantize_weights else w2
    h = np.tanh(x @ w1q)
    return h @ w2q, w1q, w2q


def train(ste: bool, quantize_weights: bool, x, y, lr=0.03, epochs=300, seed=0):
    """按 ste/quantize 配置训练 toy MLP，返回 [初始, 25, 75, 150, 300] 的 loss。"""
    rng = np.random.default_rng(seed)
    w1 = rng.standard_normal((8, 64)) * 0.5
    w2 = rng.standard_normal((64, 1)) * 0.5
    checkpoint = []

    def loss_fn():
        pred, _, _ = toy_mlp_forward(x, w1, w2, quantize_weights)
        return float(np.mean((pred - y) ** 2))

    checkpoint.append(loss_fn())
    for epoch in range(epochs):
        pred, w1q, w2q = toy_mlp_forward(x, w1, w2, quantize_weights)
        err = (pred - y) / x.shape[0] * 2.0
        g_w2q = np.tanh(x @ w1q).T @ err
        h = np.tanh(x @ w1q)
        g_w1q = x.T @ (err @ w2q.T * (1.0 - h ** 2))
        if ste:
            # STE：梯度直通到 FP32 master
            w1 -= lr * g_w1q
            w2 -= lr * g_w2q
        elif quantize_weights:
            # 朴素截断：量化器导数视为 0 → master 不更新
            pass
        else:
            # 无量化基线：标准反传
            w1 -= lr * g_w1q
            w2 -= lr * g_w2q
        if epoch + 1 in (25, 75, 150, 300):
            checkpoint.append(loss_fn())
    return checkpoint


def experiment1():
    print("=" * 66)
    print("实验 1：量化不可微 → 朴素截断梯度归零；STE 直通让训练继续")
    print("=" * 66)
    print("模型：2 层 MLP（8→64→1，tanh），MSE 回归，2000 样本，300 epoch")
    print("量化：每 32 元素子块一个 2 的幂 scale，FP4(E2M1) 就近取整")
    print()
    rng = np.random.default_rng(42)
    x = rng.standard_normal((2000, 8))
    y = np.sin(x[:, [0]]) + 0.5 * x[:, [1]] ** 2 + 0.3 * np.cos(x[:, [2]])
    header = ["epoch", "STE+FP4", "截断+FP4", "无量化基线"]
    rows = np.array([
        train(ste=True,  quantize_weights=True,  x=x, y=y),
        train(ste=False, quantize_weights=True,  x=x, y=y),
        train(ste=False, quantize_weights=False, x=x, y=y),
    ]).T
    print(f"{header[0]:>6} {header[1]:>10} {header[2]:>10} {header[3]:>12}")
    for i, ep in enumerate([0, 25, 75, 150, 300]):
        print(f"{ep:>6} {rows[i,0]:>10.4f} {rows[i,1]:>10.4f} {rows[i,2]:>12.4f}")
    print()
    print("→ 截断路 loss 纹丝不动（权重冻结，梯度被量化器吃掉了）")
    print("→ STE 路收敛，逼近无量化基线：量化感知训练能跑的数学根基")
    print()


# ─────────────────────────── 实验 2：FP4→FP8 无损性 ───────────────────────────
def build_block(m_min: float, m_max: float, rows: int = 128, cols: int = 128,
                group: int = 32, seed: int = 0):
    """构造 128×128 权重块：每 1×32 子块的量级从 m_min 线性(对数域)铺到 m_max。

    返回 (原始块, FP4 反量化块, 子块 scale 数组)。
    """
    rng = np.random.default_rng(seed)
    w = np.zeros((rows, cols))
    scales = np.zeros((rows, cols // group))
    n_sub = rows * (cols // group)  # 512 个子块
    k_range = np.linspace(np.log2(m_min), np.log2(m_max), n_sub)
    for i in range(rows):
        for j in range(0, cols, group):
            sub = i * (cols // group) + j // group
            mag = 2.0 ** k_range[sub]
            w[i, j:j + group] = mag * (0.25 + 0.25 * rng.random(group))
            scales[i, j // group] = mag / 4.0  # 名义 scale（≈ E8M0 前的量级）
    return w, scales


def experiment2():
    print("=" * 66)
    print("实验 2：FP4→FP8 反量化无损性——scale 比值阈值的数学边界")
    print("=" * 66)
    print("结构：128×128 FP8(E4M3) 块内嵌 512 个 1×32 FP4 子块，各配 2 的幂 scale")
    print("判定：FP4 反量化值再量化回 E4M3，逐位相等 → 无损（误差 0）")
    print("注：m_min=0.5 保证最小子块反量化值恰好落在 E4M3 正规区下沿（2⁻⁶）")
    print()
    header = ["s_max/s_min", "反量化误差", "无损?"]
    print(f"{header[0]:>12} {header[1]:>14} {header[2]:>8}")
    for r in [10.0, 100.0, 1e3, 2e3, 3e3, 1e4, 1e6]:
        w, scales = build_block(m_min=0.5, m_max=0.5 * r)
        w_deq = fp4_group_quant(w, 32)          # FP4 量化 + 反量化（E2M1 × scale）
        w_fp8 = quantize_e4m3(w_deq)            # 反量化值存进 FP8
        err = float(np.max(np.abs(w_fp8 - w_deq)))
        ratio = scales.max() / scales.min()
        print(f"{ratio:>12.1f} {err:>14.3e} {('YES' if err == 0 else 'no'):>8}")
    print()
    print("→ 比值 ≤ 约 2×10³ 时反量化误差精确为 0：所有值落在 E4M3 正规区")
    print("→ 比值超阈值，最大子块值溢出 E4M3 上限(448) → 饱和 → 开始有损")
    print("→ V4 报告：当前权重实测满足条件，故官方敢说『无损』")
    print()


if __name__ == "__main__":
    np.set_printoptions(precision=4, suppress=True)
    experiment1()
    experiment2()
