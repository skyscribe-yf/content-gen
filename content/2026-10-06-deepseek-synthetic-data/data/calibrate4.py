#!/usr/bin/env python3
"""校准 v4：计算量大/易滑的题，目标通过率 <100%。"""
import os, json, re, urllib.request
from math import comb

KEY = os.environ["DEEPSEEK_API_KEY"]
URL = "https://api.deepseek.com/chat/completions"

def call(prompt):
    body = json.dumps({"model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def extract(txt):
    m = re.findall(r"boxed\{([^}]+)\}", txt)
    if m: return re.sub(r"[^\d]", "", m[-1]) or m[-1].strip()
    m = re.findall(r"(\d[\d,]*)", txt[-200:])
    return m[-1].replace(",", "") if m else None

# 真值
def domino_4xn(n):
    # cell-by-cell profile DP: H rows, n cols, 1x2 dominoes
    from functools import lru_cache
    H = 4; W = n
    @lru_cache(None)
    def dp(col, mask):
        if col == W:
            return 1 if mask == 0 else 0
        res = [0]
        def fill(row, cur, nxt):
            if row == H:
                res[0] += dp(col + 1, nxt); return
            if cur & (1 << row):
                fill(row + 1, cur, nxt); return
            if row + 1 < H and not (cur & (1 << (row + 1))):
                fill(row + 2, cur | (1 << row) | (1 << (row + 1)), nxt)
            fill(row + 1, cur | (1 << row), nxt | (1 << row))
        fill(0, mask, 0)
        return res[0]
    return dp(0, 0)

def subsets_div(n, m):
    cnt = [0]*m; cnt[0] = 1
    for k in range(1, n+1):
        nc = cnt[:]
        for r in range(m):
            nc[(r+k) % m] += cnt[r]
        cnt = nc
    return cnt[0]  # includes empty set

def derange(n):
    d = [1, 0]
    for i in range(2, n+1):
        d.append((i-1)*(d[-1]+d[-2]))
    return d[n]

CAND = {
    "digit_sum_2p1000": ("2 的 1000 次方是一个很大的十进制整数。它的各位数字之和是多少？请给出最终整数答案。", 1366),
    "catalan_paths": ("从 (0,0) 走到 (10,10)，每次只能向右或向上走一步，且路径不能越过对角线 y=x（允许经过 y=x 上的点），一共有多少条不同的路径？请给出最终整数答案。", 16796),
    "change_100": ("用 1、5、10、25、50 分的美元硬币凑出 100 分，一共有多少种不同的凑法？硬币顺序不计。请给出最终整数答案。", None),
    "domino_4x10": ("用 1×2 的骨牌不重叠地铺满 4×10 的棋盘，一共有多少种不同的铺法？请给出最终整数答案。", domino_4xn(10)),
    "derange_7": ("把 1,2,3,4,5,6,7 重新排列，要求每个数都不在自己的原始位置上，一共有多少种不同的排列？请给出最终整数答案。", derange(7)),
    "subsets_div5_20": ("从 1 到 20 这 20 个整数中选出若干个（不能一个都不选），要求选出的数之和能被 5 整除，一共有多少种不同的选法？请给出最终整数答案。", subsets_div(20,5)-1),
}
# change_100 truth
coins = [1,5,10,25,50]
dp = [0]*101; dp[0]=1
for c in coins:
    for s in range(c,101): dp[s]+=dp[s-c]
CAND["change_100"] = (CAND["change_100"][0], dp[100])
print("truths:", {k: v for k,(_,v) in CAND.items()})

for pid, (prob, truth) in CAND.items():
    ans = [extract(call(prob)) for _ in range(3)]
    ok = sum(1 for a in ans if str(a) == str(truth))
    print(f"{pid}: truth={truth} answers={ans} correct={ok}/3")
