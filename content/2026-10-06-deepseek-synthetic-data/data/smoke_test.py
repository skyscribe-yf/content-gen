#!/usr/bin/env python3
"""冒烟测试：校准组合计数题，确保 (a) API 通 (b) 有错答案 (c) 有多解法。"""
import os, json, urllib.request

KEY = os.environ["DEEPSEEK_API_KEY"]
URL = "https://api.deepseek.com/chat/completions"

PROBLEMS = [
    ("coins125", "用 1 分、2 分、5 分的硬币凑出 1 元（100 分），一共有多少种不同的凑法？硬币顺序不计。请给出最终整数答案，并说明你的解法。"),
    ("weights134", "用 1 克、3 克、4 克的砝码（每种足够多）称出 20 克，一共有多少种不同的组合？不计顺序。请给出最终整数答案，并说明你的解法。"),
]

def call(prompt):
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0,
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KEY}",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

for pid, prob in PROBLEMS:
    print("=" * 20, pid)
    for i in range(2):
        out = call(prob)
        print(f"--- run {i} ---")
        print(out[:900])
    print()
