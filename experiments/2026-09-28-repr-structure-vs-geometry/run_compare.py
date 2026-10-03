#!/usr/bin/env python3
"""Same 96 Chinese passages, four domestic embedding APIs.

Compares neighbor identity (mutual kNN, MST edge overlap) with distance
agreement on those same relations. Metrics follow You et al. 2026,
arXiv:2609.27252, simplified to one vector per model (no layer max).

Does not print API keys.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
TAG = sys.argv[1] if len(sys.argv) > 1 else "clustered"
CORPUS = ROOT / (sys.argv[2] if len(sys.argv) > 2 else "corpus.json")
CACHE = ROOT / "embeddings" / TAG
OUT = ROOT / f"results-{TAG}.json"

K = 10
TAUS = (1.0, 0.1, 0.01, 0.001)
N_PERM = 200
SEED = 0
ALPHA = 0.05


def post(url: str, key: str, payload: dict, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()[:500]
        raise RuntimeError(f"HTTP {exc.code} {url}: {body}") from exc


def embed_openai(url: str, key: str, model: str, texts: list[str], dimensions: int | None, batch: int) -> np.ndarray:
    vectors = [None] * len(texts)
    for start in range(0, len(texts), batch):
        chunk = texts[start : start + batch]
        payload: dict = {"model": model, "input": chunk}
        if dimensions is not None:
            payload["dimensions"] = dimensions
        body = post(url, key, payload)
        for item in body["data"]:
            vectors[start + item["index"]] = item["embedding"]
        time.sleep(0.15)
    if any(v is None for v in vectors):
        raise RuntimeError(f"missing vectors for {model}")
    return np.asarray(vectors, dtype=np.float64)


def embed_minimax(key: str, texts: list[str], batch: int = 16) -> np.ndarray:
    url = "https://api.minimax.chat/v1/embeddings"
    vectors = []
    for start in range(0, len(texts), batch):
        chunk = texts[start : start + batch]
        body = post(url, key, {"model": "embo-01", "texts": chunk, "type": "db"})
        if body.get("base_resp", {}).get("status_code") not in (0, None):
            raise RuntimeError(f"minimax error: {body.get('base_resp')}")
        got = body["vectors"]
        if len(got) != len(chunk):
            raise RuntimeError(f"minimax returned {len(got)} for {len(chunk)}")
        vectors.extend(got)
        time.sleep(0.15)
    return np.asarray(vectors, dtype=np.float64)


def load_or_fetch(name: str, fetch) -> np.ndarray:
    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"{name}.npy"
    if path.exists():
        return np.load(path)
    arr = fetch()
    np.save(path, arr)
    meta = {"name": name, "shape": list(arr.shape), "fetched": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (CACHE / f"{name}.meta.json").write_text(json.dumps(meta, indent=2))
    return arr


def pairwise_euclidean(x: np.ndarray) -> np.ndarray:
    # x: (n, d)
    sq = np.sum(x * x, axis=1, keepdims=True)
    d2 = np.maximum(sq + sq.T - 2 * x @ x.T, 0.0)
    np.fill_diagonal(d2, 0.0)
    return np.sqrt(d2)


def pairwise_cosine_distance(x: np.ndarray) -> np.ndarray:
    nrm = np.linalg.norm(x, axis=1, keepdims=True)
    nrm = np.maximum(nrm, 1e-12)
    y = x / nrm
    sim = np.clip(y @ y.T, -1.0, 1.0)
    dist = 1.0 - sim
    np.fill_diagonal(dist, 0.0)
    return dist


def knn_sets(dist: np.ndarray, k: int) -> list[set[int]]:
    n = dist.shape[0]
    sets = []
    for i in range(n):
        order = np.argsort(dist[i], kind="mergesort")
        neigh = [int(j) for j in order if j != i][:k]
        sets.append(set(neigh))
    return sets


def mknn(a: list[set[int]], b: list[set[int]], k: int) -> float:
    return float(np.mean([len(a[i] & b[i]) / k for i in range(len(a))]))


class UnionFind:
    def __init__(self, n: int):
        self.p = list(range(n))
        self.r = [0] * n

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.r[ra] < self.r[rb]:
            self.p[ra] = rb
        elif self.r[ra] > self.r[rb]:
            self.p[rb] = ra
        else:
            self.p[rb] = ra
            self.r[ra] += 1
        return True


def mst_edges(dist: np.ndarray) -> set[tuple[int, int]]:
    n = dist.shape[0]
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            edges.append((dist[i, j], i, j))
    edges.sort(key=lambda t: (t[0], t[1], t[2]))
    uf = UnionFind(n)
    chosen = set()
    for _, i, j in edges:
        if uf.union(i, j):
            chosen.add((i, j))
            if len(chosen) == n - 1:
                break
    return chosen


def h0_overlap(tx: set[tuple[int, int]], ty: set[tuple[int, int]], n: int) -> float:
    return len(tx & ty) / (n - 1)


def normalize_dist(dist: np.ndarray) -> np.ndarray:
    pos = dist[dist > 0]
    scale = np.quantile(pos, 0.9)
    if scale <= 0:
        scale = 1.0
    return dist / scale


def agreement_weights(dx: np.ndarray, dy: np.ndarray, pairs: list[tuple[int, int]], tau: float) -> float:
    if not pairs:
        return 0.0
    acc = 0.0
    for i, j in pairs:
        a = dx[i, j]
        b = dy[i, j]
        if a <= 0 or b <= 0:
            continue
        acc += np.exp(-abs(np.log(a) - np.log(b)) / tau)
    return float(acc)


def distance_aware_mknn(dx: np.ndarray, dy: np.ndarray, ax, ay, k: int, tau: float) -> float:
    n = len(ax)
    total = 0.0
    for i in range(n):
        shared = ax[i] & ay[i]
        pairs = [(i, j) if i < j else (j, i) for j in shared]
        # weights use the actual directed pair distances; matrix is symmetric
        w = 0.0
        for j in shared:
            a = dx[i, j]
            b = dy[i, j]
            if a <= 0 or b <= 0:
                continue
            w += np.exp(-abs(np.log(a) - np.log(b)) / tau)
        total += w / k
    return float(total / n)


def distance_aware_h0(dx, dy, shared_edges, n: int, tau: float) -> float:
    return agreement_weights(dx, dy, list(shared_edges), tau) / (n - 1)


def spearman_upper(dx: np.ndarray, dy: np.ndarray) -> float:
    n = dx.shape[0]
    iu = np.triu_indices(n, k=1)
    a = dx[iu]
    b = dy[iu]
    ra = np.argsort(np.argsort(a, kind="mergesort")).astype(np.float64)
    rb = np.argsort(np.argsort(b, kind="mergesort")).astype(np.float64)
    ra -= ra.mean()
    rb -= rb.mean()
    denom = np.sqrt(np.sum(ra * ra) * np.sum(rb * rb))
    if denom == 0:
        return 0.0
    return float(np.sum(ra * rb) / denom)


def mean_abs_cosine_gap(x: np.ndarray, y: np.ndarray, pairs: list[tuple[int, int]]) -> float:
    def sim(v):
        nrm = np.linalg.norm(v, axis=1, keepdims=True)
        z = v / np.maximum(nrm, 1e-12)
        return np.clip(z @ z.T, -1.0, 1.0)

    sx, sy = sim(x), sim(y)
    if not pairs:
        return float("nan")
    gaps = [abs(sx[i, j] - sy[i, j]) for i, j in pairs]
    return float(np.mean(gaps))


def shared_neighbor_pairs(ax, ay) -> list[tuple[int, int]]:
    pairs = []
    for i, (a, b) in enumerate(zip(ax, ay)):
        for j in a & b:
            if i < j:
                pairs.append((i, j))
    return pairs


def calibrate(obs: float, nulls: np.ndarray, alpha: float = ALPHA) -> float:
    # Paper eq 8: c_alpha is the (1-alpha) quantile of {T_obs, T(1)..T(K)}.
    pool = np.concatenate([nulls, [obs]])
    c = float(np.quantile(pool, 1 - alpha))
    if c >= 1:
        return 0.0
    return float(max((obs - c) / (1 - c), 0.0))


def topic_purity(neigh: list[set[int]], topics: list[str], k: int) -> float:
    scores = []
    for i, s in enumerate(neigh):
        if not s:
            continue
        scores.append(sum(topics[j] == topics[i] for j in s) / k)
    return float(np.mean(scores))


def main() -> None:
    corpus = json.loads(CORPUS.read_text())
    texts = [item["text"] for item in corpus["items"]]
    topics = [item["topic"] for item in corpus["items"]]
    ids = [item["id"] for item in corpus["items"]]
    n = len(texts)

    bailian = os.environ["BAILIAN_API_KEY"]
    zhipu = os.environ["ZHIPU_API_KEY"]
    minimax = os.environ["MINIMAX_API_KEY"]
    bailian_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
    zhipu_url = "https://open.bigmodel.cn/api/paas/v4/embeddings"

    models = {
        "qwen-v4": lambda: embed_openai(bailian_url, bailian, "text-embedding-v4", texts, 1024, 10),
        "qwen-3.7": lambda: embed_openai(bailian_url, bailian, "qwen3.7-text-embedding", texts, 1024, 10),
        "glm-emb3": lambda: embed_openai(zhipu_url, zhipu, "embedding-3", texts, 1024, 32),
        "minimax-embo01": lambda: embed_minimax(minimax, texts, 16),
    }

    embs = {}
    for name, fetch in models.items():
        print(f"load {name}", flush=True)
        embs[name] = load_or_fetch(name, fetch)
        print(f"  shape {embs[name].shape}", flush=True)

    names = list(embs)
    # Precompute distances and neighbor structures.
    geo = {}
    for name, x in embs.items():
        euc = pairwise_euclidean(x)
        cos_d = pairwise_cosine_distance(x)
        geo[name] = {
            "euc": euc,
            "euc_n": normalize_dist(euc),
            "cos": cos_d,
            "cos_n": normalize_dist(cos_d),
            "knn_cos": knn_sets(cos_d, K),
            "knn_euc": knn_sets(euc, K),
            "mst_cos": mst_edges(cos_d),
            "mst_euc": mst_edges(euc),
        }
        print(f"purity {name} cosine-kNN {topic_purity(geo[name]['knn_cos'], topics, K):.3f}", flush=True)

    rng = np.random.default_rng(SEED)
    perms = [rng.permutation(n) for _ in range(N_PERM)]

    def permute_sets(sets, perm):
        # Neighbor identities are sample indices. After permuting correspondence
        # of model B, B's neighbor j of sample perm[i] maps back by inv.
        inv = np.empty(n, dtype=int)
        inv[perm] = np.arange(n)
        out = []
        for i in range(n):
            out.append({int(inv[j]) for j in sets[int(perm[i])]})
        return out

    pairs_out = []
    for ia, na in enumerate(names):
        for nb in names[ia + 1 :]:
            ga, gb = geo[na], geo[nb]
            row = {"a": na, "b": nb, "n": n, "k": K}
            for metric, knn_key, dist_key, mst_key in (
                ("cosine", "knn_cos", "cos_n", "mst_cos"),
                ("euclidean", "knn_euc", "euc_n", "mst_euc"),
            ):
                ax, ay = ga[knn_key], gb[knn_key]
                obs = mknn(ax, ay, K)
                nulls = np.array([mknn(ax, permute_sets(ay, p), K) for p in perms])
                mst_obs = h0_overlap(ga[mst_key], gb[mst_key], n)
                # permute MST of B: edge (perm[i], perm[j]) maps to (i, j) via inv
                mst_nulls = []
                for p in perms:
                    inv = np.empty(n, dtype=int)
                    inv[p] = np.arange(n)
                    mapped = set()
                    for i, j in gb[mst_key]:
                        ii, jj = int(inv[i]), int(inv[j])
                        mapped.add((min(ii, jj), max(ii, jj)))
                    mst_nulls.append(h0_overlap(ga[mst_key], mapped, n))
                mst_nulls = np.array(mst_nulls)
                shared = ax  # placeholder
                shared_pairs = shared_neighbor_pairs(ax, ay)
                tau_scores = {}
                for tau in TAUS:
                    tau_scores[str(tau)] = distance_aware_mknn(ga[dist_key], gb[dist_key], ax, ay, K, tau)
                h0_tau = {}
                shared_edges = ga[mst_key] & gb[mst_key]
                for tau in TAUS:
                    h0_tau[str(tau)] = distance_aware_h0(ga[dist_key], gb[dist_key], shared_edges, n, tau)
                row[metric] = {
                    "mknn": obs,
                    "mknn_null_mean": float(nulls.mean()),
                    "mknn_null_p95": float(np.quantile(nulls, 0.95)),
                    "mknn_calibrated": calibrate(obs, nulls),
                    "h0": mst_obs,
                    "h0_null_mean": float(mst_nulls.mean()),
                    "h0_null_p95": float(np.quantile(mst_nulls, 0.95)),
                    "h0_calibrated": calibrate(mst_obs, mst_nulls),
                    "shared_neighbor_undirected_pairs": len(shared_pairs),
                    "mean_abs_cosine_gap_on_shared_neighbors": mean_abs_cosine_gap(embs[na], embs[nb], shared_pairs),
                    "spearman_pairwise": spearman_upper(ga["cos" if metric == "cosine" else "euc"], gb["cos" if metric == "cosine" else "euc"]),
                    "distance_aware_mknn": tau_scores,
                    "distance_aware_h0": h0_tau,
                    "mknn_retained_at_tau": {t: (tau_scores[t] / obs if obs else 0.0) for t in tau_scores},
                }
            pairs_out.append(row)
            c = row["cosine"]
            print(
                f"{na} vs {nb}: mKNN {c['mknn']:.3f} (null {c['mknn_null_mean']:.3f}) "
                f"retain@0.01 {c['mknn_retained_at_tau']['0.01']:.3f} "
                f"H0 {c['h0']:.3f} spearman {c['spearman_pairwise']:.3f}",
                flush=True,
            )

    # Same-model sanity: mKNN of a model with itself must be 1.
    sanity = {}
    for name in names:
        s = geo[name]["knn_cos"]
        sanity[name] = mknn(s, s, K)

    result = {
        "date": "2026-09-28",
        "corpus_n": n,
        "k": K,
        "n_perm": N_PERM,
        "seed": SEED,
        "models": {
            "qwen-v4": "dashscope text-embedding-v4 dimensions=1024 (Qwen3-Embedding series)",
            "qwen-3.7": "dashscope qwen3.7-text-embedding dimensions=1024",
            "glm-emb3": "bigmodel embedding-3 dimensions=1024",
            "minimax-embo01": "minimax embo-01 type=db",
        },
        "not_available": {
            "deepseek": "https://api.deepseek.com/embeddings returned 404 on 2026-09-28",
            "kimi": "https://api.moonshot.cn/v1/embeddings returned 401 with KIMI_API_KEY; no public embedding model id confirmed",
        },
        "shapes": {name: list(arr.shape) for name, arr in embs.items()},
        "topic_purity_cosine_knn": {name: topic_purity(geo[name]["knn_cos"], topics, K) for name in names},
        "self_mknn": sanity,
        "ids": ids,
        "pairs": pairs_out,
        "paper": "https://arxiv.org/abs/2609.27252",
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
