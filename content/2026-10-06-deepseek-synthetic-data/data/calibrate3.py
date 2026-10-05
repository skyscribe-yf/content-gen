#!/usr/bin/env python3
"""校准 v3：陷阱题，逼出错误答案。"""
import os, json, re, urllib.request
from math import gcd

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
    if m: return re.sub(r"[^\d]", "", m[-1]) or m[-1].strip()
    m = re.findall(r"(\d[\d,]*)", txt[-200:])
    return m[-1].replace(",", "") if m else None

# 真值
sq_points_6 = sum(k * (6 - k) ** 2 for k in range(1, 6))          # 6x6 points -> 5x5 cells
sel3 = None
res = [x % 3 for x in range(1, 21)]
from math import comb
c0, c1, c2 = res.count(0), res.count(1), res.count(2)
sel3 = comb(c0,3) + c1*c2*c0 + comb(c1,3) + comb(c2,3)
cop = sum(1 for x in range(1, 1001) if gcd(x, 1000) == 1)
p3 = round(2026**2 / 12)

CAND = {
    "grid_squares": ("在一个 6×6 的点阵中（共 6 行 6 列一共 36 个点，相邻点距离为 1），以这些点为顶点可以组成多少个正方形？注意：边不一定平行于网格线。请给出最终整数答案。", sq_points_6),
    "select3_mod3": ("从 1 到 20 这 20 个整数中选出 3 个不同的数，要求它们的和能被 3 整除，一共有多少种不同的选法？请给出最终整数答案。", sel3),
    "coprime_1000": ("在 1 到 1000 的整数中，有多少个数与 1000 的最大公约数等于 1？请给出最终整数答案。", cop),
    "p3_2026": ("把 2026 拆成 3 个正整数之和（不计顺序），一共有多少种不同的拆法？请给出最终整数答案。", p3),
}
print("truths:", {k: v for k, (_, v) in CAND.items()})

for pid, (prob, truth) in CAND.items():
    ans = []
    for i in range(4):
        ans.append(extract(call(prob)))
    ok = sum(1 for a in ans if str(a) == str(truth))
    print(f"{pid}: truth={truth} answers={ans} correct={ok}/4")
