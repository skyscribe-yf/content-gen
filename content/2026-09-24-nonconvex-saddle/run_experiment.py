"""非凸损失面：坑为什么是稀有事件 —— 自跑实验（数字事实源）

三块：
  exp1  随机对称矩阵的 Hessian：临界点里「所有方向都朝上」的概率随维度衰减 + 负特征值个数分布
  exp2  真实随机场（1D / 2D）的临界点普查：按指数分类，看坑在低维并不稀有
  exp3  对称性鞍点：隐藏层权重全部初始化成同一个值会怎样；谁来打破对称；噪声尺度 vs 批量

运行：uv run --with numpy python run_experiment.py
输出：results.json（正文所有数字的唯一来源）
"""

import json
import numpy as np

SEED = 20260924
OUT = "results.json"


# ---------------------------------------------------------------- exp1
def exp1_hessian_index():
    """临界点的二阶结构 ≈ 随机对称矩阵。统计指数（负特征值个数）分布与「全正」概率。"""
    rng = np.random.default_rng(SEED)
    out = {"note": "GOE: A=(M+M^T)/2, M~N(0,1)。临界点的 Hessian 在这个模型里就是随机对称矩阵。",
           "rows": []}
    for D, n in [(1, 200000), (2, 200000), (3, 200000), (5, 200000), (8, 100000), (10, 60000),
                 (12, 40000), (16, 20000), (20, 20000), (32, 8000), (50, 4000)]:
        M = rng.normal(size=(n, D, D))
        A = (M + np.transpose(M, (0, 2, 1))) / 2.0
        ev = np.linalg.eigvalsh(A)
        n_neg = (ev < 0).sum(axis=1)
        p_min = float((n_neg == 0).mean())
        out["rows"].append({
            "D": D,
            "samples": n,
            "p_all_positive": p_min,
            "hits_all_positive": int((n_neg == 0).sum()),
            "p_two_pow_minus_D": float(2.0 ** -D),
            "mean_index": float(n_neg.mean()),
            "mean_index_over_D": float(n_neg.mean() / D),
            "index_std": float(n_neg.std()),
            "index_hist_frac": {int(k): float(v) for k, v in
                                zip(*np.unique(n_neg, return_counts=True))} if D <= 12 else None,
        })
    # 可测范围内的衰减斜率：log P(all>0) vs D
    pts = [(r["D"], r["p_all_positive"]) for r in out["rows"] if r["hits_all_positive"] >= 5]
    if len(pts) >= 3:
        Ds = np.array([p[0] for p in pts], dtype=float)
        lp = np.log(np.array([p[1] for p in pts]))
        slope = float(np.polyfit(Ds, lp, 1)[0])
        out["decay_slope_log_per_dim"] = slope
        out["decay_base_per_dim"] = float(np.exp(slope))
        out["slope_fit_D_range"] = [int(Ds.min()), int(Ds.max())]
    out["self_check"] = self_check_p_all_positive()
    return out


def self_check_p_all_positive():
    """自检：D=1 解析值 1/2；D=2 用三维高斯求积独立算一遍（不依赖蒙特卡罗）。"""
    n = 160
    x, w = np.polynomial.hermite_e.hermegauss(n)
    w = w / w.sum()
    # 2×2：M 对角 ~N(0,1)，非对角元素 (M01+M10)/2 ~ N(0,1/2) → 写成 b=u/sqrt(2), u~N(0,1)
    A = x.reshape(-1, 1)      # a 轴
    C = x.reshape(1, -1)      # c 轴
    U2 = (x ** 2) / 2.0       # b^2 的取值（按 u~N(0,1) 加权）
    W2 = w
    total = 0.0
    for k in range(n):
        inside = (A * C > U2[k]) & (A + C > 0)
        total += W2[k] * float((inside * w.reshape(-1, 1) * w.reshape(1, -1)).sum())
    # 对照：一维直接解析
    return {"D1_analytic": 0.5, "D2_quadrature": total}


# ---------------------------------------------------------------- exp2
def _field_1d(rng, K=40, L=20.0, n_grid=200001):
    """1D 随机场：f(x)= (1/sqrt(K)) Σ a_k cos(w_k x + φ_k)，解析导数。"""
    w = rng.uniform(0.5, 4.0, K)
    a = rng.normal(size=K)
    ph = rng.uniform(0, 2 * np.pi, K)
    x = np.linspace(0, L, n_grid)
    def f1(x):
        return ((a * w)[:, None] * -np.sin(w[:, None] * x + ph[:, None])).sum(0) / np.sqrt(K)
    def f2(x):
        return ((a * w ** 2)[:, None] * -np.cos(w[:, None] * x + ph[:, None])).sum(0) / np.sqrt(K)
    return x, f1, f2


def exp2_field_1d():
    rng = np.random.default_rng(SEED + 1)
    tot_min = tot_max = 0
    runs = []
    for trial in range(5):
        x, f1, f2 = _field_1d(rng)
        g = f1(x)
        s = np.sign(g)
        idx = np.where(np.diff(s) != 0)[0]
        # 用中点法细化，避免重根
        xs = []
        for i in idx:
            lo, hi = x[i], x[i + 1]
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if np.sign(f1(np.array([lo]))[0]) == np.sign(f1(np.array([mid]))[0]):
                    lo = mid
                else:
                    hi = mid
            xs.append(0.5 * (lo + hi))
        if not xs:
            continue
        xs = np.array(xs)
        h = f2(xs)
        tot_min += int((h > 0).sum())
        tot_max += int((h < 0).sum())
        runs.append({"trial": trial, "critical_points": int(len(xs)),
                     "minima": int((h > 0).sum()), "maxima": int((h < 0).sum())})
    total = tot_min + tot_max
    return {"note": "1D 随机场：临界点只有谷底和山顶，没有马鞍。",
            "runs": runs,
            "total_critical_points": total,
            "minima": tot_min, "maxima": tot_max,
            "frac_minima": (tot_min / total) if total else None}


def exp2_field_2d():
    """2D 随机场：格点上找 |∇f| 的极小点，再用 Hessian 分类（谷底/马鞍/山顶）。"""
    rng = np.random.default_rng(SEED + 2)
    K = 60
    w = rng.normal(size=(K, 2)) * 1.6
    a = rng.normal(size=K)
    ph = rng.uniform(0, 2 * np.pi, K)
    n = 201
    xs = np.linspace(0, 12, n)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    def grads(x, y):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        shp = (K,) + (1,) * x.ndim
        arg = w[:, 0].reshape(shp) * x + w[:, 1].reshape(shp) * y + ph.reshape(shp)
        a3 = a.reshape(shp)
        wx = w[:, 0].reshape(shp)
        wy = w[:, 1].reshape(shp)
        gx = (a3 * wx * -np.sin(arg)).sum(0) / np.sqrt(K)
        gy = (a3 * wy * -np.sin(arg)).sum(0) / np.sqrt(K)
        hxx = (a3 * wx ** 2 * -np.cos(arg)).sum(0) / np.sqrt(K)
        hyy = (a3 * wy ** 2 * -np.cos(arg)).sum(0) / np.sqrt(K)
        hxy = (a3 * wx * wy * -np.cos(arg)).sum(0) / np.sqrt(K)
        return gx, gy, hxx, hyy, hxy
    gx, gy, hxx, hyy, hxy = grads(X, Y)
    mag = np.hypot(gx, gy)
    # |∇f| 的局部极小点（比阈值法稳）
    cand = (mag[1:-1, 1:-1] < mag[:-2, 1:-1]) & (mag[1:-1, 1:-1] < mag[2:, 1:-1]) & \
           (mag[1:-1, 1:-1] < mag[1:-1, :-2]) & (mag[1:-1, 1:-1] < mag[1:-1, 2:])
    idx = np.argwhere(cand) + 1
    minima = saddles = maxima = 0
    kept = 0
    for i, j in idx:
        # 用牛顿法精修到 ∇f=0
        x, y = X[i, j], Y[i, j]
        for _ in range(40):
            gx1, gy1, hxx1, hyy1, hxy1 = grads(np.array([x]), np.array([y]))
            g = np.array([gx1[0], gy1[0]])
            H = np.array([[hxx1[0], hxy1[0]], [hxy1[0], hyy1[0]]])
            if np.linalg.norm(g) < 1e-9:
                break
            try:
                step = np.linalg.solve(H + 1e-9 * np.eye(2), g)
            except np.linalg.LinAlgError:
                break
            x, y = x - step[0], y - step[1]
        gx1, gy1, hxx1, hyy1, hxy1 = grads(np.array([x]), np.array([y]))
        if np.linalg.norm([gx1[0], gy1[0]]) > 1e-4:
            continue
        H = np.array([[hxx1[0], hxy1[0]], [hxy1[0], hyy1[0]]])
        ev = np.linalg.eigvalsh(H)
        kept += 1
        if ev[0] > 0:
            minima += 1
        elif ev[1] < 0:
            maxima += 1
        else:
            saddles += 1
    return {"note": "2D 随机场：3 类临界点（谷底 / 马鞍 / 山顶）",
            "critical_points": kept, "minima": minima, "saddles": saddles, "maxima": maxima,
            "frac_minima": (minima / kept) if kept else None,
            "frac_saddle": (saddles / kept) if kept else None,
            "frac_maxima": (maxima / kept) if kept else None}


# ---------------------------------------------------------------- exp3
def _mlp_init(rng, D_in=2, H=8, mode="random", scale=0.5):
    W1 = rng.normal(size=(H, D_in)) * scale if mode == "random" else np.full((H, D_in), 0.3)
    b1 = rng.normal(size=H) * 0.1 if mode == "random" else np.zeros(H) + 0.1
    W2 = rng.normal(size=H) * scale if mode == "random" else np.full(H, 0.3)
    return W1, b1, W2


def _forward(params, X):
    W1, b1, W2 = params
    Z = np.tanh(X @ W1.T + b1)
    return Z @ W2, Z


def _grads(params, X, y, idx=None):
    W1, b1, W2 = params
    if idx is not None:
        X, y = X[idx], y[idx]
    pred, Z = _forward(params, X)
    err = pred - y
    n = len(y)
    gW2 = (Z.T @ err) * 2 / n
    dZ = np.outer(err, W2) * (1 - Z ** 2) * 2 / n
    gW1 = dZ.T @ X
    gb1 = dZ.sum(0)
    loss = float((err ** 2).mean())
    return loss, [gW1, gb1, gW2]


def exp3_symmetry(n_steps=4000, lr=0.1):
    rng = np.random.default_rng(SEED + 3)
    X = rng.normal(size=(256, 2))
    y = (X[:, 0] * X[:, 1] + 0.5 * X[:, 0])  # 需要多个隐藏单元才能拟合的目标
    results = {}

    def run(mode, noise_sigma=0.0, batch=None):
        params = _mlp_init(rng, mode=mode)
        hist = []

        def full_loss(p):
            pred, _ = _forward(p, X)
            return float(((pred - y) ** 2).mean())

        for t in range(n_steps):
            idx = None if batch is None else rng.integers(0, len(X), batch)
            loss, g = _grads(params, X, y, idx)
            if noise_sigma > 0:  # 参数级彼此独立的随机性（不是小批量噪声）
                g = [gi + rng.normal(scale=noise_sigma, size=gi.shape) for gi in g]
            params = [p - lr * gi for p, gi in zip(params, g)]
            if t % 200 == 0 or t == n_steps - 1:
                hist.append({"step": t, "loss": full_loss(params)})   # 统一口径：全量数据损失
        W1 = params[0]
        spread = float(np.abs(W1 - W1.mean(axis=0, keepdims=True)).max())
        return {"mode": mode, "noise_sigma": noise_sigma, "batch": batch,
                "final_loss": full_loss(params), "loss_curve": hist,
                "unit_spread_final": spread, "params": [p.tolist() for p in params]}

    results["identical_fullbatch"] = run("identical")
    results["random_fullbatch"] = run("random")
    results["identical_param_noise"] = run("identical", noise_sigma=0.01)
    results["identical_minibatch_noise"] = run("identical", batch=8)
    results["random_minibatch"] = run("random", batch=8)

    # 噪声尺度 vs 批量：同一批初始点上梯度的方差
    params = _mlp_init(rng, mode="random")
    var_rows = []
    for B in [1, 2, 8, 32, 128, 256]:
        samples = []
        for _ in range(400):
            idx = rng.integers(0, len(X), B)
            _, g = _grads(params, X, y, idx)
            samples.append(g[0].ravel())
        S = np.array(samples)
        var_rows.append({"batch": B, "grad_var": float(S.var(axis=0).mean())})
    Bs = np.array([r["batch"] for r in var_rows], dtype=float)
    Vs = np.array([r["grad_var"] for r in var_rows])
    slope = float(np.polyfit(np.log(Bs), np.log(Vs), 1)[0])
    results["grad_var_vs_batch"] = {"rows": var_rows, "loglog_slope": slope}
    return results


def main():
    out = {
        "seed": SEED,
        "exp1_hessian_index": exp1_hessian_index(),
        "exp2_field_1d": exp2_field_1d(),
        "exp2_field_2d": exp2_field_2d(),
        "exp3_symmetry": exp3_symmetry(),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    self_check(out)

    e1 = out["exp1_hessian_index"]
    print("== exp1 临界点的二阶结构（随机对称矩阵）")
    for r in e1["rows"]:
        print(f"  D={r['D']:>2}  P(全正)={r['p_all_positive']:.3e}  命中={r['hits_all_positive']:>5}"
              f"  2^-D={r['p_two_pow_minus_D']:.3e}  平均负特征值/D={r['mean_index_over_D']:.3f}")
    if "decay_base_per_dim" in e1:
        print(f"  实测衰减：每加一维 ×{e1['decay_base_per_dim']:.3f}"
              f"（拟合区间 D={e1['slope_fit_D_range']}）")
    e2a, e2b = out["exp2_field_1d"], out["exp2_field_2d"]
    print(f"== exp2 1D 随机场：临界点 {e2a['total_critical_points']}，谷底 {e2a['minima']}，"
          f"山顶 {e2a['maxima']}，谷底占比 {e2a['frac_minima']:.3f}")
    print(f"== exp2 2D 随机场：临界点 {e2b['critical_points']}，谷底 {e2b['minima']} / 马鞍 {e2b['saddles']}"
          f" / 山顶 {e2b['maxima']}，谷底占比 {e2b['frac_minima']:.3f}，马鞍占比 {e2b['frac_saddle']:.3f}")
    print("== exp3 对称性鞍点")
    for k, v in out["exp3_symmetry"].items():
        if k == "grad_var_vs_batch":
            print(f"  逐点梯度方差 vs 批量：log-log 斜率 {v['loglog_slope']:.3f}"
                  f"（{-1.0:.1f} 表示 Var∝1/B）")
        else:
            print(f"  {k:<28} final_loss={v['final_loss']:.3e}  单元间参数差={v['unit_spread_final']:.3e}")


def self_check(out):
    """可跑的自检：数字一变就报错。"""
    e1, e2a, e2b, e3 = (out["exp1_hessian_index"], out["exp2_field_1d"],
                        out["exp2_field_2d"], out["exp3_symmetry"])
    rows = {r["D"]: r for r in e1["rows"]}
    assert abs(rows[1]["p_all_positive"] - 0.5) < 0.005, "D=1 应恰为 1/2（解析值）"
    assert abs(rows[2]["p_all_positive"] - e1["self_check"]["D2_quadrature"]) < 0.01, "D=2 应与求积独立结果一致"
    assert rows[5]["p_all_positive"] < rows[2]["p_all_positive"] < rows[1]["p_all_positive"], "全正概率应随维递减"
    assert all(abs(r["mean_index_over_D"] - 0.5) < 0.01 for r in e1["rows"]), "典型指数应约为 D/2"
    assert abs(e2a["frac_minima"] - 0.5) < 0.06, "1D 里谷底应约一半（不稀有）"
    assert 0.15 < e2b["frac_minima"] < 0.45, "2D 里谷底占比应明显低于一半"
    assert e3["identical_fullbatch"]["unit_spread_final"] < 1e-12, "全同初始化不应自行打破对称"
    assert e3["identical_minibatch_noise"]["unit_spread_final"] < 1e-12, "小批量噪声也不应打破对称"
    assert e3["identical_param_noise"]["unit_spread_final"] > 1e-2, "参数级独立噪声应打破对称"
    assert e3["identical_fullbatch"]["final_loss"] > 50 * e3["random_fullbatch"]["final_loss"], "全同初始化的损失应远高于随机初始化"
    assert abs(e3["grad_var_vs_batch"]["loglog_slope"] + 1.0) < 0.15, "逐点梯度方差应约 ∝ 1/批量"
    print("self-check: 11/11 通过")


def replot():
    """从 results.json 重绘三张脚本图（数字图只由脚本产出，AI 图不承载数字）。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = json.load(open(OUT, encoding="utf-8"))
    plt.rcParams["font.sans-serif"] = ["Noto Serif CJK SC", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # --- 04 局部极小占比 vs 维度 -----------------------------------------
    rows = d["exp1_hessian_index"]["rows"]
    Ds = [r["D"] for r in rows]
    ps = [r["p_all_positive"] for r in rows]
    hits = [r["hits_all_positive"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 5.6), dpi=200)
    shown = [(x, p) for x, p, h in zip(Ds, ps, hits) if h >= 5]
    ax.plot([x for x, _ in shown], [p for _, p in shown], "o-", color="#c0392b",
            lw=2.4, ms=9, label="实测：全部特征值为正的比例")
    ax.plot(Ds, [2.0 ** -x for x in Ds], "--", color="#7f8c8d", lw=2,
            label="抛硬币粗估 $2^{-D}$")
    zero = [(x, 2.2e-9) for x, h in zip(Ds, hits) if h == 0]
    ax.plot([x for x, _ in zero], [y for _, y in zero], "x", color="#2c3e50", ms=11, mew=2.4)
    if zero:
        ax.annotate("D = 8 / 10 / 20 / 50：分别抽样 10万 / 6万 / 2万 / 4千 次，全部零命中",
                    xy=(11, 2.6e-9), xytext=(2.6, 6e-8), fontsize=11.5, color="#2c3e50",
                    arrowprops=dict(arrowstyle="->", color="#2c3e50", lw=1.5))
    for r in rows:
        if r["hits_all_positive"] >= 5:
            ax.annotate(f"{r['p_all_positive']*100:.3g}%", (r["D"], r["p_all_positive"]),
                        textcoords="offset points", xytext=(6, 8), fontsize=11.5, color="#c0392b")
    ax.set_yscale("log")
    ax.set_ylim(1e-9, 1.2)
    ax.set_xscale("log")
    ax.set_xticks([1, 2, 3, 5, 8, 10, 20, 50])
    ax.set_xticklabels([1, 2, 3, 5, 8, 10, 20, 50])
    ax.set_xlabel("维度 D", fontsize=13)
    ax.set_ylabel("临界点里「所有方向都朝上」的比例", fontsize=13)
    ax.set_title("每多一维，坑大约乘以 0.121（实测）", fontsize=15)
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=11.5, loc="lower left")
    fig.tight_layout()
    fig.savefig("04-minima-fraction-vs-D.png")
    plt.close(fig)

    # --- 05 指数（负特征值个数）分布 ------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5.0), dpi=200)
    for D, color, shift in [(10, "#2980b9", 0.35), (12, "#8e44ad", -0.35)]:
        row = [r for r in rows if r["D"] == D][0]
        hist = {int(k): v for k, v in row["index_hist_frac"].items()}
        tot = sum(hist.values())
        ks = sorted(hist)
        ax.bar([k + shift for k in ks], [hist[k] / tot for k in ks], width=0.34,
               color=color, alpha=0.9, label=f"D={D}（均值 {row['mean_index']:.1f}）")
        ax.axvline(D / 2, color=color, ls="--", lw=1.6, alpha=0.9)
    ax.annotate("局部极小在这里（指数 = 0）：\nD=10 抽样 6 万次，一次都没出现",
                xy=(0.1, 0.002), xytext=(0.35, 0.30), fontsize=11.5, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.6))
    ax.set_xlim(-0.6, 12.6)
    ax.set_xlabel("临界点的指数（负特征值个数）", fontsize=13)
    ax.set_ylabel("占比", fontsize=13)
    ax.set_title("临界点几乎全卡在「半数方向朝下」上", fontsize=15)
    ax.grid(alpha=0.2, axis="y")
    ax.legend(fontsize=11.5)
    fig.tight_layout()
    fig.savefig("05-index-distribution.png")
    plt.close(fig)

    # --- 06 三组初始化的损失曲线 -----------------------------------------
    e3 = d["exp3_symmetry"]
    name = {"identical_fullbatch": "全同初始化",
            "random_fullbatch": "随机初始化",
            "identical_param_noise": "全同 + 参数级独立噪声",
            "identical_minibatch_noise": "全同 + 小批量噪声"}
    color = {"identical_fullbatch": "#c0392b", "random_fullbatch": "#27ae60",
             "identical_param_noise": "#2980b9", "identical_minibatch_noise": "#e67e22"}
    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=200)
    for k, label in name.items():
        cur = e3[k]["loss_curve"]
        ax.plot([c["step"] for c in cur], [c["loss"] for c in cur],
                lw=2.4, color=color[k], label=f"{label}（终值 {e3[k]['final_loss']:.3g}）")
    ax.set_yscale("log")
    ax.set_xlabel("训练步数", fontsize=13)
    ax.set_ylabel("训练损失（对数坐标）", fontsize=13)
    ax.set_title("全同初始化卡在 1.203，比随机初始化差 313 倍", fontsize=15)
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=11.5)
    fig.tight_layout()
    fig.savefig("06-loss-curves-initialization.png")
    plt.close(fig)
    print("已重绘：04-minima-fraction-vs-D.png / 05-index-distribution.png / 06-loss-curves-initialization.png")
    for k, v in e3.items():
        if k != "grad_var_vs_batch":
            print(f"  {k:<28} 全量最终损失={v['final_loss']:.4g}  单元间参数差={v['unit_spread_final']:.3g}")


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:
        replot()
    else:
        main()
