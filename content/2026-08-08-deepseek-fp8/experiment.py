#!/usr/bin/env python3
"""FP8 训练机制演示：per-tensor vs per-group 量化误差对比。

模拟 V3 报告的 fine-grained 量化（激活 1×128 tile / 权重 128×128 block），
用真实 FP8 E4M3 浮点模型（binade 舍入 + subnormal + 饱和）演示：
outlier 与正常值的比值一旦接近/超过 E4M3 动态范围（≈2.9×10⁴），
per-tensor 全局 scale 会把正常值压进 subnormal 区间，精度雪崩；
per-group 只毁掉 outlier 所在组。

仅机制演示，不代表 DeepSeek 官方性能。NumPy 自包含，无第三方依赖。
"""
import numpy as np

E4M3_MAX = 448.0        # FP8 E4M3 最大有限值（1.75 × 2^8）
E4M3_EMIN = -6          # 最小正规指数（1 - 偏置7）
SUBNORM_STEP = 2.0 ** -9  # subnormal 最小分辨率


def quantize_e4m3(x: np.ndarray, scale: float) -> np.ndarray:
    """FP8 E4M3 量化：y = x/scale → FP8 舍入 → 乘回 scale。

    3 位尾数 → 每个 binade 内 8 个台阶（相对精度 ~6.25%）；
    |y| < 2^-6 进入 subnormal，分辨率骤降到 2^-9；
    |y| > 448 饱和。
    """
    y = x / scale
    y = np.clip(y, -E4M3_MAX, E4M3_MAX)
    a = np.abs(y)
    # normal binade 指数
    e = np.floor(np.log2(np.maximum(a, 1e-30)))
    e = np.clip(e, E4M3_EMIN, 8)
    m = np.round(y / (2.0 ** e) * 8.0) / 8.0  # 3 位尾数
    q = m * 2.0 ** e
    # subnormal：低于最小正规值时按 2^-9 台阶
    sub = a < 2.0 ** E4M3_EMIN
    q = np.where(sub, np.round(y / SUBNORM_STEP) * SUBNORM_STEP, q)
    return q * scale


def mre(x: np.ndarray, xq: np.ndarray) -> float:
    """相对误差，与正文公式一致。"""
    return float(np.linalg.norm(x - xq) / np.linalg.norm(x))


def report(rows, w, label):
    """对给定张量跑 per-tensor / per-group，输出指标。"""
    s_pt = float(np.max(np.abs(w))) / E4M3_MAX
    q_pt = quantize_e4m3(w, s_pt)
    g = np.stack([quantize_e4m3(w[i], float(np.max(np.abs(w[i]))) / E4M3_MAX)
                  for i in range(rows)])
    # 普通行（不含 outlier）的平均误差
    clean_rows = [i for i in range(rows) if np.max(np.abs(w[i])) < 1.0]
    mre_pt_clean = np.mean([mre(w[i], q_pt[i]) for i in clean_rows])
    mre_pg_clean = np.mean([mre(w[i], g[i]) for i in clean_rows])
    return {
        "label": label,
        "s_pt": s_pt,
        "mre_pt_all": mre(w, q_pt),
        "mre_pg_all": mre(w, g),
        "mre_pt_clean": mre_pt_clean,
        "mre_pg_clean": mre_pg_clean,
        "mre_pt_row0": mre(w[0], q_pt[0]),
        "mre_pg_row0": mre(w[0], g[0]),
    }


def main() -> None:
    rng = np.random.default_rng(42)
    rows, cols = 128, 128

    print("=" * 68)
    print("FP8 训练机制演示：outlier 如何毁掉 per-tensor 量化")
    print("=" * 68)

    # 场景 A（激活）：正常值 ±0.03，outlier = 5000（比值 ~1.7×10⁵ > 动态范围）
    act = np.clip(rng.normal(0.0, 0.01, size=(rows, cols)), -0.03, 0.03)
    act[0, 0] = 5000.0
    ra = report(rows, act, "场景A 激活：outlier=5000 vs 正常±0.03（比值 1.7×10⁵）")

    # 场景 B（权重）：正常值 ±1，outlier = 200（比值 200 << 动态范围）
    wt = np.clip(rng.normal(0.0, 0.3, size=(rows, cols)), -1.0, 1.0)
    wt[0, 0] = 200.0
    rb = report(rows, wt, "场景B 权重：outlier=200 vs 正常±1（比值 2×10²）")

    print(f"\n{'场景':<52}{'pt普通行误差':>12}{'pg普通行误差':>12}{'pt-outlier行':>13}{'pg-outlier行':>13}")
    print("-" * 102)
    for r in (ra, rb):
        print(f"{r['label']:<38}{r['mre_pt_clean']:>13.1%}{r['mre_pg_clean']:>13.1%}"
              f"{r['mre_pt_row0']:>14.1%}{r['mre_pg_row0']:>14.1%}")
        print(f"{'per-tensor scale':>38}{r['s_pt']:>18.4f}")
        print()

    print("解读：")
    print("  - 场景A：per-tensor 把正常值压进 subnormal（y≈0.0067 < 2^-6），")
    print(f"    普通行误差 {ra['mre_pt_clean']:.1%}；per-group 普通行回到 {ra['mre_pg_clean']:.1%}，")
    print(f"    改善 {ra['mre_pt_clean']/ra['mre_pg_clean']:.1f} 倍。")
    print("  - 场景B：outlier 比值远小于 E4M3 动态范围（2.9×10⁴），per-tensor 也扛得住，")
    print(f"    普通行误差 {rb['mre_pt_clean']:.1%}——这解释了为什么权重可以用更粗的 128×128 block。")

    # 台阶可视化：per-tensor 下正常值 y = x/s 的指数分布
    print("\n量化台阶（场景A per-tensor，scale=%.4f）:" % ra["s_pt"])
    y = act[1] / ra["s_pt"]  # 普通行
    e = np.clip(np.floor(np.log2(np.abs(y) + 1e-30)), -9, 8)
    below = int((np.abs(y) < 2 ** E4M3_EMIN).sum())
    print(f"  普通行 128 个正常值里 {below} 个落入 subnormal（< 2^-6），"
          f"其余最高 binade 2^{int(e.max())}，只有 8 个台阶可用")


if __name__ == "__main__":
    main()
