#!/usr/bin/env python3
"""校准 v2：更难的候选题，目标通过率 50-85%。"""
import os, json, re, urllib.request

KEY = os.environ["DEEPSEEK_API_KEY"]
URL = "https://api.deepseek.com/chat/completions"

def call(prompt):
    body = json.dumps({"model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def extract(txt):
    m = re.findall(r"boxed\{([^}]+)\}", txt)
    if m: return m[-1].strip()
    m = re.findall(r"(-?\d+\.?\d*)", txt[-200:])
    return m[-1] if m else None

CAND = {
    "distinct50": ("把 50 拆成若干个互不相同的正整数之和（至少一个数），一共有多少种不同的拆法？不计顺序。请给出最终整数答案。", 3658),
    "expected_hth": ("反复抛一枚均匀硬币，直到首次出现连续序列「正、反、正」（HTH）。平均需要抛多少次？请给出最终整数答案。", 10),
    "digit7_2026": ("从 1 到 2026 的整数中，有多少个整数的十进制表示里含有数字 7？请给出最终整数答案。", None),
    "three_n_tiling": ("用 1×2 的骨牌不重叠地铺满 3×8 的棋盘，一共有多少种不同的铺法？请给出最终整数答案。", None),
}

# 算 digit7 真值
def count_digit7(n):
    c = 0
    for x in range(1, n+1):
        if '7' in str(x): c += 1
    return c
CAND["digit7_2026"] = (CAND["digit7_2026"][0], count_digit7(2026))

# 3×8 tiling with 1x2 dominoes: hard; compute via transfer matrix
def tile3xn(n):
    # states: bitmask of 3 rows filled
    from functools import lru_cache
    @lru_cache(None)
    def fill(col, mask):
        if col == n: return 1 if mask == 0 else 0
        if mask & 1:
            return fill(col, mask >> 1) if (mask >> 1) else None
        return None
    # simpler: DP over columns with profile
    # profile p in 0..7: rows already occupied in current column
    from functools import lru_cache
    @lru_cache(None)
    def ways(col, prof):
        if col == n:
            return 1 if prof == 0 else 0
        if prof & 1:
            return ways(col, prof >> 1)
        # place horizontal in this row (occupies next column)
        res = ways(col, (prof >> 1) | 4)   # mark next-col row0
        # place vertical occupying row+1 in same column
        if col < n and not (prof & 2):
            res += ways(col, prof >> 2)
        return res
    return ways(0, 0)

try:
    t38 = tile3xn(8)
    CAND["three_n_tiling"] = (CAND["three_n_tiling"][0], t38)
    print("3x8 tiling truth:", t38)
except Exception as e:
    print("tiling calc err", e)

for pid, (prob, truth) in CAND.items():
    ans = []
    for i in range(4):
        a = extract(call(prob)); ans.append(a)
    print(f"{pid}: truth={truth} answers={ans} correct={sum(1 for a in ans if str(a)==str(truth))}/4")
