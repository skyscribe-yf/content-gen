#!/usr/bin/env python3
"""C2 钱账受控统计：compaction 前后各 N 轮（默认 5）、同 provider+model 过滤。

口径（docs/series-plan-2026-10-context-compression.md §4.2 + 作者 2026-10-24 拍板 #3）：
  1. 遍历 ~/.pi/agent/sessions/**/*.jsonl 找 type=="compaction" 事件
  2. 窗口 = 压缩前/后各 N 条带 usage 的 assistant 消息；全部同 (provider, model) 才收
  3. T = tokensBefore；T' = 压缩后第一条 assistant 的 input+cacheRead
  4. ρ 从 ~/.pi/token-logs/usage.jsonl 按 provider/model 线性拟合
     cost ~ input + cacheRead + output + const，取 cacheRead 系数 / input 系数
  5. N* = (C_comp + T'(1-ρ)) / ((T-T')ρ)，C_comp = compaction 调用自身 totalTokens
     （token 口径的一阶近似；κ = C_comp / T）
  6. 未来回合数 = 压缩后同会话 assistant 消息数（代理指标）

用法：
  python3 scripts/compaction_stats.py                 # 受控统计（5/5 窗口）
  python3 scripts/compaction_stats.py --window 3
  python3 scripts/compaction_stats.py --json out.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

SESSIONS = os.path.expanduser("~/.pi/agent/sessions/**/*.jsonl")
USAGE_LOG = os.path.expanduser("~/.pi/token-logs/usage.jsonl")

# 钱账排除（不参与 ρ 拟合 / N* / 回本 / 费用统计；token 量级不受影响）：
# - ollama-cloud：作者 2026-10-26 拍板「计费不准，那个数据不要用」
# - commandcode：ρ 拟合 >1（约 10.25），计价结构异常（series-plan §4.3 既有排除）
EXCLUDE_MONEY_PROVIDERS = {"ollama-cloud", "commandcode"}

# 全量排除（token 量级也不算，作者 2026-10-26 拍板「讯飞的数字也不要算」）：
# - xunfei / xunfei-ex（xopglm51、astron-code-latest）：不报 cacheRead、cost=0
EXCLUDE_PROVIDERS = {"xunfei", "xunfei-ex"} | EXCLUDE_MONEY_PROVIDERS


def norm_usage(u: dict) -> dict:
    cost = u.get("cost") or {}
    return {
        "input": u.get("input", 0) or 0,
        "cacheRead": u.get("cacheRead", 0) or 0,
        "cacheWrite": u.get("cacheWrite", 0) or 0,
        "output": u.get("output", 0) or 0,
        "totalTokens": u.get("totalTokens", 0) or 0,
        "cost": cost.get("total", 0) or 0,
    }


def walk_sessions(window: int):
    samples = []
    n_comp = 0
    for f in glob.glob(SESSIONS, recursive=True):
        try:
            lines = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
        except Exception:
            continue
        asst = []  # (line_idx, provider, model, usage, ts)
        compactions = []
        for i, e in enumerate(lines):
            if e.get("type") == "compaction":
                compactions.append((i, e))
            elif e.get("type") == "message":
                m = e.get("message") or {}
                if m.get("role") == "assistant":
                    u = m.get("usage") or {}
                    if u.get("totalTokens"):
                        asst.append((i, m.get("provider"), m.get("model"),
                                     norm_usage(u), e.get("timestamp")))
        if not compactions:
            continue
        n_comp += len(compactions)
        for ci, ev in compactions:
            pre = [a for a in asst if a[0] < ci][-window:]
            post = [a for a in asst if a[0] > ci][:window]
            if len(pre) < window or not post:
                continue
            combo = {(a[1], a[2]) for a in pre + post}
            if len(combo) != 1:
                continue  # 跨模型窗口，弃
            provider, model = pre[-1][1], pre[-1][2]
            future = sum(1 for a in asst if a[0] > ci)
            samples.append({
                "file": os.path.basename(f),
                "timestamp": ev.get("timestamp"),
                "provider": provider,
                "model": model,
                "tokensBefore": ev.get("tokensBefore"),
                "compaction_usage": norm_usage(ev.get("usage") or {}),
                "pre": [a[3] for a in pre],
                "post": [a[3] for a in post],
                "future_rounds": future,
            })
    return n_comp, samples


def fit_rho(need: set):
    """usage.jsonl 里按 (provider, model) 拟合 ρ = coef(cacheRead)/coef(input)。"""
    import numpy as np
    buckets: dict = {}
    with open(USAGE_LOG, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            key = (r.get("provider"), r.get("model"))
            if key not in need or key[0] in EXCLUDE_MONEY_PROVIDERS:
                continue
            cost = r.get("cost")
            total = cost.get("total") if isinstance(cost, dict) else cost
            inp = r.get("inputTokens") or 0
            cr = r.get("cacheReadTokens") or 0
            out = r.get("outputTokens") or 0
            if not total or (inp + cr) <= 0 or out < 0:
                continue
            buckets.setdefault(key, []).append((inp, cr, out, total))
    out = {}
    for key, rows in buckets.items():
        A = np.array([[r[0], r[1], r[2], 1.0] for r in rows], dtype=float)
        b = np.array([r[3] for r in rows], dtype=float)
        try:
            coef, *_ = np.linalg.lstsq(A, b, rcond=None)
        except Exception:
            continue
        ci, cc = coef[0], coef[1]
        if ci > 0:
            pred = A @ coef
            ss_res = float(((b - pred) ** 2).sum())
            ss_tot = float(((b - b.mean()) ** 2).sum()) or 1.0
            out[key] = {"rho": float(cc / ci), "n": len(rows),
                        "r2": 1 - ss_res / ss_tot}
    return out


def med(xs):
    xs = sorted(xs)
    n = len(xs)
    return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=5)
    ap.add_argument("--json", help="把逐样本结果写到该路径")
    args = ap.parse_args()

    n_comp, all_samples = walk_sessions(args.window)
    samples = [s for s in all_samples if s["provider"] not in EXCLUDE_PROVIDERS]
    print(f"compaction 事件总数 {n_comp}；同模型 {args.window}/{args.window} 窗口样本 "
          f"{len(all_samples)}，剔除讯飞/排除名单后 {len(samples)}（provider/model 分布：")
    from collections import Counter
    for (p, m), c in Counter((s['provider'], s['model']) for s in samples).most_common():
        print(f"    {c:3d}  {p} / {m}")

    rhos = fit_rho({(s["provider"], s["model"]) for s in samples})
    print("\nρ 拟合（usage.jsonl 全量计费行）：")
    for (p, m), r in sorted(rhos.items()):
        print(f"    {p} / {m}: ρ={r['rho']:.4f}  n={r['n']}  R²={r['r2']:.3f}")

    # 窗口对比：每轮均值
    def turn_stats(rows):
        n = len(rows)
        return {
            "input": sum(r["input"] for r in rows) / n,
            "cacheRead": sum(r["cacheRead"] for r in rows) / n,
            "total": sum(r["totalTokens"] for r in rows) / n,
            "cost": sum(r["cost"] for r in rows) / n,
            "hit": sum(r["cacheRead"] for r in rows) /
                   max(1, sum(r["cacheRead"] + r["input"] for r in rows)),
        }

    pre_all, post_all = [], []
    money_samples = [s for s in samples if s["provider"] not in EXCLUDE_MONEY_PROVIDERS]
    for s in samples:
        pre_all.append(turn_stats(s["pre"]))
        post_all.append(turn_stats(s["post"]))
    m_pre = [turn_stats(s["pre"]) for s in money_samples]
    m_post = [turn_stats(s["post"]) for s in money_samples]
    print(f"\n窗口每轮均值（{len(samples)} 样本；费用口径剔除 ollama-cloud/commandcode 后 "
          f"{len(money_samples)} 样本）：")
    print(f"    前 {args.window} 轮: input={med([x['input'] for x in pre_all]):,.0f}  "
          f"cacheRead={med([x['cacheRead'] for x in pre_all]):,.0f}  "
          f"hit={med([x['hit'] for x in pre_all]):.1%}  "
          f"cost=${med([x['cost'] for x in m_pre]) or 0:.4f}")
    print(f"    后 {args.window} 轮: input={med([x['input'] for x in post_all]):,.0f}  "
          f"cacheRead={med([x['cacheRead'] for x in post_all]):,.0f}  "
          f"hit={med([x['hit'] for x in post_all]):.1%}  "
          f"cost=${med([x['cost'] for x in m_post]) or 0:.4f}")
    # 后窗口第 1 轮 vs 第 5 轮（缓存恢复曲线）
    firsts = [turn_stats([s["post"][0]]) for s in samples if s["post"]]
    lasts = [turn_stats([s["post"][-1]]) for s in samples if len(s["post"]) == args.window]
    print(f"    压缩后第 1 轮: input={med([x['input'] for x in firsts]):,.0f}  "
          f"hit={med([x['hit'] for x in firsts]):.1%}")
    if lasts:
        print(f"    压缩后第 {args.window} 轮: input={med([x['input'] for x in lasts]):,.0f}  "
              f"hit={med([x['hit'] for x in lasts]):.1%}")
    # 标题口径：tokensBefore → 压缩后首轮 totalTokens 的降幅（已剔全量排除名单）
    tb = [s["tokensBefore"] for s in samples if s.get("tokensBefore")]
    post1 = [s["post"][0]["totalTokens"] for s in samples if s["post"]]
    drops = [1 - s["post"][0]["totalTokens"] / s["tokensBefore"] for s in samples
             if s.get("tokensBefore") and s["post"][0]["totalTokens"]]
    if tb and post1:
        print(f"\n降幅口径（n={len(tb)}）：tokensBefore 中位 {med(tb):,.0f} → 压缩后首轮 "
              f"{med(post1):,.0f}（聚合 {1 - med(post1) / med(tb):.0%}）；"
              f"逐样本降幅中位 {med(drops):.0%}")

    # N* 回本检验（token 口径）
    print("\nN* 回本检验（T=tokensBefore，T'=压缩后首轮 input+cacheRead，C_comp=压缩调用 totalTokens）：")
    usable = []
    for s in samples:
        if s["provider"] in EXCLUDE_MONEY_PROVIDERS:
            continue
        T = s["tokensBefore"] or 0
        Tp = s["post"][0]["input"] + s["post"][0]["cacheRead"]
        C = s["compaction_usage"]["totalTokens"]
        if T and Tp and T > Tp:
            usable.append((s, T, Tp, C))
    print(f"    可用（T>T'）{len(usable)} / {len(samples)}")
    rho_table = {}
    for (p, m), r in rhos.items():
        rho_table[(p, m)] = r["rho"]
    # 也挂计划文档里的既有估计做敏感性
    plan_rhos = {("opencode-go", "deepseek-v4-pro"): 0.003,
                 ("opencode-go", "glm-5.2"): 0.1857,
                 ("xiaomi-mimo-tp", "mimo-v2.5-pro"): 0.20}
    for label, key2rho in (("拟合", rho_table), ("计划文档粗扫", plan_rhos)):
        rows = []
        for (p, m), rho in sorted(key2rho.items()):
            sub = [(s, T, Tp, C) for (s, T, Tp, C) in usable
                   if (s["provider"], s["model"]) == (p, m)]
            if not sub or rho <= 0:
                continue
            nstars, recouped = [], 0
            for s, T, Tp, C in sub:
                nstar = (C + Tp * (1 - rho)) / max(1e-9, (T - Tp) * rho)
                nstars.append(nstar)
                if s["future_rounds"] >= nstar:
                    recouped += 1
            rows.append((p, m, rho, len(sub), med(nstars),
                         recouped / len(sub), med([s["future_rounds"] for s, *_ in sub])))
        if rows:
            print(f"    [{label}]")
            for p, m, rho, n, nstar, rec, fut in rows:
                print(f"      {p}/{m}: ρ={rho:.4f}  n={n}  N*中位={nstar:.1f} 轮  "
                      f"未来轮中位={fut:.0f}  实际回本={rec:.0%}")

    if args.json:
        for s in samples:
            for k in ("pre", "post"):
                s[k] = [ {kk: vv for kk, vv in r.items()} for r in s[k] ]
        json.dump({"window": args.window, "n_compaction": n_comp,
                   "n_samples": len(samples), "rho_fit": {f"{p}|{m}": v for (p, m), v in rhos.items()},
                   "samples": samples}, open(args.json, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n逐样本明细 → {args.json}")


if __name__ == "__main__":
    sys.exit(main())
