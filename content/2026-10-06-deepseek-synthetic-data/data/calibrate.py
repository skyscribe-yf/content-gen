#!/usr/bin/env python3
"""校准：4 个候选组合计数题 × 4 次采样，估计错误率与解法多样性。"""
import os, json, re, urllib.request
from itertools import product

KEY = os.environ["DEEPSEEK_API_KEY"]
URL = "https://api.deepseek.com/chat/completions"

# ---- 真值（暴力/DP） ----
def true_coins():
    return sum(1 for a in range(101) for b in range(51) for c in range(21) if a + 2*b + 5*c == 100)
def true_distinct(n):
    dp = [0]*(n+1); dp[0] = 1
    for k in range(1, n+1):
        for s in range(n, k-1, -1):
            dp[s] += dp[s-k]
    return dp[n]
def true_domino(n):
    a, b = 1, 2
    for _ in range(n-1):
        a, b = b, a+b
    return a
def true_mod3(n):
    # subsets of 1..n (nonempty) with sum % 3 == 0
    cnt = [1, 0, 0]
    for k in range(1, n+1):
        nc = [0, 0, 0]
        for r in range(3):
            nc[r] += cnt[r]
            nc[(r+k) % 3] += cnt[r]
        cnt = nc
    return cnt[0] - 1

CAND = {
    "coins125_moderate": ("用 1 分、2 分、5 分的硬币凑出 1 元（100 分），一共有多少种不同的凑法？硬币顺序不计。请给出最终整数答案，并说明你的解法。", true_coins()),
    "distinct30_hard": ("把 30 拆成若干个互不相同的正整数之和（至少一个数），一共有多少种不同的拆法？不计顺序。请给出最终整数答案，并说明你的解法。", true_distinct(30)),
    "domino2x10": ("用 1×2 的骨牌不重叠地铺满 2×10 的棋盘，一共有多少种不同的铺法？请给出最终整数答案，并说明你的解法。", true_domino(10)),
    "mod3_12": ("从 1 到 12 这 12 个整数中选出若干个（不能一个都不选），要求选出的数之和能被 3 整除，一共有多少种不同的选法？请给出最终整数答案，并说明你的解法。", true_mod3(12)),
}

def call(prompt):
    body = json.dumps({"model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def extract(txt):
    m = re.findall(r"boxed\{(\d+)\}", txt)
    if m: return int(m[-1])
    m = re.findall(r"(\d+)", txt[-260:])
    return int(m[-1]) if m else None

for pid, (prob, truth) in CAND.items():
    hits = 0; answers = []
    for i in range(4):
        t = call(prob); a = extract(t); answers.append(a)
        hits += (a == truth)
    print(f"{pid}: truth={truth} answers={answers} correct={hits}/4")
