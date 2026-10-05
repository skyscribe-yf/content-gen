#!/usr/bin/env python3
"""冒烟测试 v2：保存完整输出 + 抽最终答案。"""
import os, json, re, urllib.request

KEY = os.environ["DEEPSEEK_API_KEY"]
URL = "https://api.deepseek.com/chat/completions"

PROBLEMS = {
    "coins125": "用 1 分、2 分、5 分的硬币凑出 1 元（100 分），一共有多少种不同的凑法？硬币顺序不计。请给出最终整数答案，并说明你的解法。",
    "weights134": "用 1 克、3 克、4 克的砝码（每种足够多）称出 20 克，一共有多少种不同的组合？不计顺序。请给出最终整数答案，并说明你的解法。",
}

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
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

out = {}
for pid, prob in PROBLEMS.items():
    out[pid] = []
    for i in range(3):
        txt = call(prob)
        nums = re.findall(r"(?:答案|共|总|因此|所以)[^\n]{0,20}?(\d+)", txt)
        out[pid].append({"text": txt, "tail": txt[-400:]})
        print(f"[{pid} run{i}] tail:\n{txt[-350:]}\n")

json.dump(out, open("content/2026-10-06-deepseek-synthetic-data/data/smoke.json", "w"), ensure_ascii=False, indent=1)
print("saved")
