#!/usr/bin/env python3
"""正式实验：组合计数陷阱题 × N=100 采样，规则判卷。

题：从 1..20 选若干个（非空）使和能被 5 整除，有多少种选法？
真值：209727（= (2^20 + 4*2^4)/5 - 1，单位根公式；亦经 DP 暴力核验）
朴素错解：209715 = floor(2^20/5)（漏掉 +12 修正项）
"""
import os, json, re, time, urllib.request

KEY = os.environ["DEEPSEEK_API_KEY"]
URL = "https://api.deepseek.com/chat/completions"
N = 100
OUT = "content/2026-10-06-deepseek-synthetic-data/data/exp1-100x.json"

PROBLEM = ("从 1 到 20 这 20 个整数中选出若干个（不能一个都不选），"
           "要求选出的数之和能被 5 整除，一共有多少种不同的选法？"
           "请给出最终整数答案，并说明你的解法。")

TRUTH = 209727

def call(prompt):
    body = json.dumps({"model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read())

def extract(txt):
    m = re.findall(r"boxed\{([^}]+)\}", txt)
    if m:
        d = re.sub(r"[^\d]", "", m[-1])
        if d: return int(d)
    # last standalone integer near the end
    tail = txt[-400:]
    m = re.findall(r"(?<![\d.])(\d{4,7})(?![\d.])", tail)
    if m: return int(m[-1])
    m = re.findall(r"(\d[\d,]*)", tail)
    return int(m[-1].replace(",", "")) if m else None

recs = []
t0 = time.time()
for i in range(N):
    try:
        resp = call(PROBLEM)
        txt = resp["choices"][0]["message"]["content"]
        ans = extract(txt)
        usage = resp.get("usage", {})
    except Exception as e:
        txt, ans, usage = f"ERROR: {e}", None, {}
    recs.append({"i": i, "answer": ans, "correct": ans == TRUTH,
                 "text": txt, "usage": usage})
    if (i + 1) % 10 == 0:
        ok = sum(r["correct"] for r in recs)
        print(f"{i+1}/{N} passed={ok} elapsed={time.time()-t0:.0f}s", flush=True)

json.dump({"problem": PROBLEM, "truth": TRUTH, "n": N, "records": recs},
          open(OUT, "w"), ensure_ascii=False, indent=1)

ok = sum(r["correct"] for r in recs)
wrong = [r for r in recs if not r["correct"]]
print(f"DONE passed={ok}/{N} ({ok}%)")
from collections import Counter
print("wrong answers:", Counter(str(r['answer']) for r in wrong))
