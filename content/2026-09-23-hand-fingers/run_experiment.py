#!/usr/bin/env python3
"""六根手指篇 · 自跑实验（seed 20260923）

实验 ① 像素不敏感度：多一根手指在像素损失里值多少分
  ①a 一根手指的面积账（占画面 / 占手）
  ①b 多一根手指的像素改动量，对照：等面积无结构斑块 / 整图亮度 +2% / 同批正常样本间抖动
  ①c 判别力：规则法（数根数）vs 像素损失法（在 5 指样本上训练的小模型）的 AUC

实验 ② 像素预算：分辨率 × 压缩率 → 重建后手指根数错误率
  合成 5 指手 → 块平均下采样 f 倍（模拟 VAE 压缩）→ 双线性上采样重建
  → 固定扫描行上数白色段数 = 手指根数 → 错误率表 + 解析 latent 宽度

数字事实源：results.json
运行：uv run --with matplotlib --with numpy python run_experiment.py
"""
import json
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Noto Sans CJK TC", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

SEED = 20260923
BG, FG, THR = 0.50, 0.85, 0.675     # 背景灰 / 手（肤色）灰 / 判定阈值
OUT = {}


# ---------------------------------------------------------------- 合成手
def hand_layout(rng, W, scale, jitter=0.02):
    """返回手指参数表 [(x, w, h)] 与几何 meta（不含额外手指）。"""
    hand_w = scale * W
    cx = 0.5 * W + rng.normal(0, jitter * W)
    palm_top = 0.52 * W
    fw = 0.13 * hand_w
    gap = 0.035 * hand_w
    rel_h = [0.72, 0.86, 0.95, 0.86, 0.72]
    span = 5 * fw + 4 * gap
    fx = cx - span / 2
    fingers = []
    for i in range(5):
        w_i = fw * (1 + rng.normal(0, jitter * 2))
        h_i = hand_w * rel_h[i] * (1 + rng.normal(0, jitter))
        x_i = fx + i * (fw + gap) + rng.normal(0, jitter * 0.5 * hand_w)
        fingers.append((x_i, w_i, h_i))
    meta = dict(W=W, scale=scale, hand_w=hand_w, finger_w=fw, gap=gap,
                palm_top=palm_top, palm_w=hand_w, palm_h=0.55 * hand_w,
                cx=cx, scan_y=int(round(palm_top - 0.45 * hand_w)))
    return fingers, meta


def render(W, fingers, meta, extra=None, blob=None):
    """把布局画成图：背景 BG、手 FG。extra=(x,w,h) 额外手指；blob=(x,y,w,h) 无结构斑块。"""
    img = np.full((W, W), BG, dtype=np.float64)
    y0 = int(round(meta["palm_top"]))
    y1 = int(round(meta["palm_top"] + meta["palm_h"]))
    x0 = int(round(meta["cx"] - meta["palm_w"] / 2))
    x1 = int(round(meta["cx"] + meta["palm_w"] / 2))
    img[max(0, y0):min(W, y1), max(0, x0):min(W, x1)] = FG
    for (x_i, w_i, h_i) in fingers:
        fy0 = int(round(meta["palm_top"] - h_i))
        img[max(0, fy0):y0, max(0, int(round(x_i))):min(W, int(round(x_i + w_i)))] = FG
    if extra is not None:
        x_i, w_i, h_i = extra
        fy0 = int(round(meta["palm_top"] - h_i))
        img[max(0, fy0):y0, max(0, int(round(x_i))):min(W, int(round(x_i + w_i)))] = FG
    if blob is not None:
        bx, by, bw, bh = blob
        img[max(0, int(by)):min(W, int(by + bh)),
            max(0, int(bx)):min(W, int(bx + bw))] = FG
    return img


def extra_finger(fingers, meta, rng):
    """经典 artifact：五指之外多一根（放在小指外侧，与邻指之间留标准指缝）。"""
    fw = meta["finger_w"]
    gap = meta["gap"]
    x_last = fingers[4][0] + fingers[4][1]
    w_extra = fw * 0.8 * (1 + rng.normal(0, 0.02))
    h_extra = meta["hand_w"] * 0.70
    return (x_last + gap, w_extra, h_extra)


def count_fingers(img, scan_y, thr=THR, min_run=2):
    row = img[scan_y] > thr
    runs, run_len = 0, 0
    for v in row:
        if v:
            run_len += 1
        else:
            if run_len >= min_run:
                runs += 1
            run_len = 0
    if run_len >= min_run:
        runs += 1
    return runs


def count_fingers_profile(img, meta, thr=THR, min_run=2):
    """更稳的计数：在手指带（掌心之上）取列向平均轮廓，数轮廓里的段数。

    相邻手指在个别行可能相碰，但在整条带上大多分开——轮廓法比单行法稳。
    """
    W = img.shape[0]
    hand_w = meta["hand_w"]
    y0 = int(round(meta["palm_top"] - 0.60 * hand_w))
    y1 = int(round(meta["palm_top"] - 0.10 * hand_w))
    band = (img[max(0, y0):max(1, y1)] > thr).mean(axis=0)
    prof = band > 0.5
    runs, run_len = 0, 0
    for v in prof:
        if v:
            run_len += 1
        else:
            if run_len >= min_run:
                runs += 1
            run_len = 0
    if run_len >= min_run:
        runs += 1
    return runs


def block_down_up(img, f):
    """块平均下采样 f 倍 + 双线性上采样（模拟 VAE 压缩的像素预算损失）。"""
    W = img.shape[0]
    n = W // f
    small = img[: n * f, : n * f].reshape(n, f, n, f).mean(axis=(1, 3))
    ys = np.linspace(0, n - 1, W)
    y0 = np.floor(ys).astype(int); y1 = np.minimum(y0 + 1, n - 1); wy = (ys - y0)[:, None]
    x0 = np.floor(ys).astype(int); x1 = np.minimum(x0 + 1, n - 1); wx = (ys - x0)[None, :]
    top = small[y0][:, x0] * (1 - wx) + small[y0][:, x1] * wx
    bot = small[y1][:, x0] * (1 - wx) + small[y1][:, x1] * wx
    return top * (1 - wy) + bot * wy


def auc_of(scores0, scores1):
    """Mann-Whitney AUC：scores1 是否系统性地更高。"""
    allv = np.concatenate([scores0, scores1])
    lab = np.concatenate([np.zeros(len(scores0)), np.ones(len(scores1))])
    order = np.argsort(allv, kind="mergesort")
    ranks = np.empty(len(allv), dtype=float)
    ranks[order] = np.arange(1, len(allv) + 1)
    n1, n0 = lab.sum(), len(lab) - lab.sum()
    return float((ranks[lab == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


# ------------------------------------------------- 实验 ① 像素不敏感度
def exp1():
    W, SCALE, N = 512, 0.25, 160
    r = np.random.default_rng(SEED + 1)
    A5, A6, metas, layouts = [], [], [], []
    for _ in range(N):
        fingers, meta = hand_layout(r, W, SCALE)
        a = render(W, fingers, meta)
        ex = extra_finger(fingers, meta, r)
        b = render(W, fingers, meta, extra=ex)
        A5.append(a); A6.append(b); metas.append(meta); layouts.append(fingers)
    A5 = np.stack(A5); A6 = np.stack(A6)

    # ①a 面积账
    m0 = metas[0]
    one_finger_area = m0["finger_w"] * m0["hand_w"] * 0.82
    hand_area = 5 * one_finger_area + m0["palm_h"] * m0["palm_w"]
    finger_share_of_hand = one_finger_area / hand_area
    hand_area_frac = hand_area / (W * W)
    finger_share_of_image = one_finger_area / (W * W)
    changed_px_frac = float((np.abs(A6 - A5) > 0.1).mean())

    # ①b 改动量对照（全部按同一「像素差异能量」口径：均方根差 ×  √N）
    def rms(a, b):
        return float(np.sqrt(((a - b) ** 2).mean()))

    d_extra = rms(A6, A5)
    # 正常样本间抖动：随机配对的 5 指样本
    perm = r.permutation(N)
    d_jitter = float(np.mean([rms(A5[i], A5[perm[i]]) for i in range(N)]))
    # 等面积无结构斑块（放在手的右侧背景里，面积 = 一根手指）
    blob_area = one_finger_area
    bw = int(round(np.sqrt(blob_area / 1.6))); bh = int(round(blob_area / bw))
    bx = int(round(m0["cx"] + 0.75 * m0["hand_w"])); by = int(round(0.55 * W))
    A_blob = np.stack([render(W, f_, me, blob=(bx, by, bw, bh))
                       for f_, me in zip(layouts, metas)])
    d_blob = rms(A_blob, A5)
    # 整图亮度 +2%
    A_bright = np.clip(A5 * 1.02, 0, 1)
    d_bright = rms(A_bright, A5)
    # 强一点的全图扰动：亮度 +10%
    d_bright10 = rms(np.clip(A5 * 1.10, 0, 1), A5)

    # ①c 判别力
    # 规则法：数根数
    rule_acc = float(np.mean([count_fingers_profile(A6[i], metas[i]) == 6
                              for i in range(N)]))
    # 像素损失法 A：到训练均值的 L2（最简单的像素口径）
    mean_img = A5.mean(axis=0)
    s5 = np.array([rms(A5[i], mean_img) for i in range(N)])
    s6 = np.array([rms(A6[i], mean_img) for i in range(N)])
    auc_l2 = auc_of(s5, s6)
    # 像素损失法 B：在 5 指样本上训练的小模型（线性自编码器 / PCA 瓶颈，64×64）
    S = 64
    def small(A):
        n = A.shape[0]
        return A.reshape(n, W // S, S, W // S, S).mean(axis=(1, 3))
    B5, B6 = small(A5), small(A6)
    idx = r.permutation(N); tr, te = idx[: N * 3 // 4], idx[N * 3 // 4:]
    X = B5[tr].reshape(len(tr), -1)
    mu = X.mean(axis=0)
    _, _, Vt = np.linalg.svd(X - mu, full_matrices=False)
    K = 32
    P = Vt[:K]
    def err(B):
        Y = B.reshape(B.shape[0], -1) - mu
        return ((Y - (Y @ P.T) @ P) ** 2).mean(axis=1)
    e5, e6 = err(B5[te]), err(B6[te])
    auc_model = auc_of(e5, e6)
    inc_pct = float((e6.mean() - e5.mean()) / e5.mean() * 100)
    inc_over_std = float((e6.mean() - e5.mean()) / e5.std())

    OUT["exp1"] = dict(
        seed=SEED, W=W, scale=SCALE, n=N, train=len(tr), test=len(te), bottleneck=K,
        hand_area_frac_of_image=hand_area_frac,
        one_finger_share_of_image=finger_share_of_image,
        one_finger_share_of_hand=finger_share_of_hand,
        changed_pixel_frac=changed_px_frac,
        rms_extra_finger=d_extra, rms_jitter_between_normal=d_jitter,
        rms_equal_area_blob=d_blob, rms_bright_2pct=d_bright,
        rms_bright_10pct=d_bright10,
        ratio_jitter_over_extra=d_jitter / d_extra,
        ratio_extra_over_bright2=d_extra / d_bright,
        rule_based_count_acc=rule_acc,
        auc_pixel_l2_to_mean=auc_l2, auc_trained_model=auc_model,
        model_loss_increase_pct=inc_pct, model_loss_increase_over_std=inc_over_std,
        latent_finger_px_at_512_f8=float(m0["finger_w"] / 8),
    )

    print("exp1:", json.dumps(OUT["exp1"], ensure_ascii=False, indent=1))


# --------------------------------------------------- 实验 ② 像素预算
def soft_gap_depth(img, meta, f=None):
    """指缝深度（连续口径）：1 = 指缝与背景一样干净，0 = 被手指填平。

    在手指带内取列向平均轮廓；手指电平取各指中心列的中位数，背景电平 = BG。
    每条指缝取轮廓谷底，深度 = (手指电平 − 谷底) / (手指电平 − 背景电平)。
    """
    W = img.shape[0]
    y0 = int(round(meta["palm_top"] - 0.60 * meta["hand_w"]))
    y1 = int(round(meta["palm_top"] - 0.10 * meta["hand_w"]))
    prof = img[max(0, y0):max(1, y1)].mean(axis=0)
    fw, gap = meta["finger_w"], meta["gap"]
    fx = meta["cx"] - (5 * fw + 4 * gap) / 2
    finger_lv = float(np.median([prof[int(round(fx + (k + 0.5) * fw + k * gap))]
                                 for k in range(5)]))
    depths = []
    for k in range(4):
        gx0 = int(round(fx + (k + 1) * fw + k * gap))
        gx1 = max(gx0 + 1, int(round(gx0 + gap)))
        valley = float(prof[gx0:gx1].min())
        depths.append((finger_lv - valley) / max(1e-9, finger_lv - BG))
    return float(np.clip(np.mean(depths), 0.0, 1.0))


def exp2():
    res = {}
    N = 60
    for scale in [0.12, 0.25]:
        for W in [256, 512, 1024]:
            for f in [4, 8, 16]:
                r = np.random.default_rng(SEED + 2 + int(scale * 100) + W + f)
                depths, latent_gap, latent_finger = [], [], []
                for _ in range(N):
                    fingers, meta = hand_layout(r, W, scale)
                    img = render(W, fingers, meta)
                    rec = block_down_up(img, f)
                    depths.append(soft_gap_depth(rec, meta))
                    latent_gap.append(meta["gap"] / f)
                    latent_finger.append(meta["finger_w"] / f)
                depths = np.array(depths)
                res[f"scale{scale}_W{W}_f{f}"] = dict(
                    scale=scale, W=W, f=f, n=N,
                    latent_gap_px=float(np.mean(latent_gap)),
                    latent_finger_px=float(np.mean(latent_finger)),
                    mean_gap_depth=float(depths.mean()),
                    frac_gap_flat=float((depths < 0.5).mean()),
                )
    OUT["exp2"] = res

    fig, axes = plt.subplots(1, 2, figsize=(13.4, 4.5))
    for scale, ls in [(0.12, "-"), (0.25, "--")]:
        for f, color in [(4, "#3b7dd8"), (8, "#d94f3d"), (16, "#8d8d8d")]:
            xs, ys = [], []
            for W in [256, 512, 1024]:
                d = res[f"scale{scale}_W{W}_f{f}"]
                xs.append(W); ys.append(d["mean_gap_depth"] * 100)
            axes[0].plot(xs, ys, ls, marker="o", color=color,
                         label=f"压缩 {f}×（手占画面 {int(scale*100)}%）")
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks([256, 512, 1024]); axes[0].set_xticklabels(["256", "512", "1024"])
    axes[0].set_xlabel("分辨率"); axes[0].set_ylabel("重建后的指缝深度 (%)")
    axes[0].set_title("① 分辨率 × 压缩率：指缝还剩多少")
    axes[0].legend(fontsize=8, ncol=2); axes[0].grid(alpha=0.3)

    labels, gaps, fing = [], [], []
    for scale in [0.12, 0.25]:
        for W in [256, 512, 1024]:
            labels.append(f"{int(scale*100)}%/{W}")
            gaps.append(res[f"scale{scale}_W{W}_f8"]["latent_gap_px"])
            fing.append(res[f"scale{scale}_W{W}_f8"]["latent_finger_px"])
    x = np.arange(len(labels)); wd = 0.38
    axes[1].bar(x - wd / 2, fing, wd, label="一根手指宽度", color="#0F4C81")
    axes[1].bar(x + wd / 2, gaps, wd, label="指缝宽度", color="#e8a33d")
    axes[1].axhline(1.0, color="#d94f3d", ls="--", lw=1.4)
    axes[1].text(len(labels) - 0.5, 1.05, "1 个 latent 像素", color="#d94f3d",
                 ha="right", fontsize=9)
    axes[1].set_xticks(x); axes[1].set_xticklabels(labels, fontsize=9)
    axes[1].set_ylabel("latent 中的宽度（像素，压缩 8×）")
    axes[1].set_title("② 像素预算账（手占画面比例 / 分辨率）")
    axes[1].legend(fontsize=9)
    plt.tight_layout()
    plt.savefig("02-pixel-budget.png", dpi=150)
    plt.close(fig)
    print("exp2 done")


# ------------------------------------- 实验 ①b 条件平均（模态平均）
def exp1b():
    """两个模态（手指布局 A / 右移半个指距的 B）各半，训练目标 = 像素均方误差。

    检验：① 小模型的输出是不是 A、B 的平均；② 这个「平均解」在像素损失下
    是否比任何一只正确的手都低；③ 平均出来的手，数得出几条手指状条纹。
    """
    W, SCALE, N = 512, 0.25, 400
    r = np.random.default_rng(SEED + 5)
    fingers, meta = hand_layout(np.random.default_rng(SEED), W, SCALE, jitter=0.0)
    A = render(W, fingers, meta)
    shift = 0.5 * (meta["finger_w"] + meta["gap"])
    B = render(W, [(x + shift, w, h) for (x, w, h) in fingers], meta)
    avg_clean = 0.5 * (A + B)

    cues = np.array([i % 2 for i in range(N)], dtype=float)
    Y = np.stack([(A if c == 0 else B) + r.normal(0, 0.01, (W, W)) for c in cues])
    Xd = np.hstack([cues[:, None], np.ones((N, 1))])
    w, *_ = np.linalg.lstsq(Xd, Y.reshape(N, -1), rcond=None)
    pred_half = (np.array([0.5, 1.0]) @ w).reshape(W, W)

    def rms(a, b):
        return float(np.sqrt(((a - b) ** 2).mean()))

    d_ab = rms(A, B)
    L_mean = 0.5 * rms(avg_clean, A) ** 2 + 0.5 * rms(avg_clean, B) ** 2
    L_mode = 0.5 * 0.0 + 0.5 * d_ab ** 2

    def profile(img, meta, thr=THR):
        y0 = int(round(meta["palm_top"] - 0.60 * meta["hand_w"]))
        y1 = int(round(meta["palm_top"] - 0.10 * meta["hand_w"]))
        return (img[y0:y1] > thr).mean(axis=0)

    def stripe_count(img, meta, level=0.60):
        prof = profile(img, meta)
        runs, n = 0, 0
        for v in prof > level:
            if v:
                n += 1
            else:
                if n >= 3:
                    runs += 1
                n = 0
        if n >= 3:
            runs += 1
        return runs

    OUT["exp1b"] = dict(
        seed=SEED, W=W, scale=SCALE, n=N, shift_px=float(shift),
        model_output_vs_clean_average_rms=rms(pred_half, avg_clean),
        rms_between_modes=d_ab,
        loss_conditional_mean=L_mean, loss_always_pick_one_mode=L_mode,
        loss_ratio_mean_over_mode=L_mean / L_mode,
        finger_count_mode_A=count_fingers_profile(A, meta),
        stripe_count_mode_A=stripe_count(A, meta),
        stripe_count_average=stripe_count(avg_clean, meta),
        stripe_count_model_output=stripe_count(pred_half, meta),
    )

    fig, axes = plt.subplots(1, 4, figsize=(15.2, 4.2))
    panels = [(A, "模态 A：五根手指", "#0F4C81"),
              (B, "模态 B：手指右移半个指距", "#0F4C81"),
              (avg_clean, "像素损失的解 = A、B 的平均", "#d94f3d"),
              (np.abs(avg_clean - A) * 3, "平均解与 A 的差异（×3）", "#d94f3d")]
    for ax, (im, ttl, col) in zip(axes, panels):
        ax.imshow(im, cmap="gray", vmin=0, vmax=1)
        ax.set_title(ttl, fontsize=11, color=col)
        ax.axis("off")
    axes[2].text(0.5, -0.07, f"数出 {stripe_count(avg_clean, meta)} 条手指状条纹"
                             f"（正常手 {stripe_count(A, meta)} 条）",
                 transform=axes[2].transAxes, ha="center", fontsize=11, color="#d94f3d")
    axes[3].text(0.5, -0.07, f"平均解的损失只有「永远选 A」的 {L_mean/L_mode*100:.0f}%",
                 transform=axes[3].transAxes, ha="center", fontsize=11, color="#d94f3d")
    plt.tight_layout()
    plt.savefig("01-mode-average.png", dpi=150)
    plt.close(fig)
    print("exp1b:", json.dumps(OUT["exp1b"], ensure_ascii=False))


if __name__ == "__main__":
    exp1()
    exp1b()
    exp2()
    with open("results.json", "w", encoding="utf-8") as fp:
        json.dump(OUT, fp, ensure_ascii=False, indent=2)
    print("saved results.json")
