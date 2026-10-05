#!/usr/bin/env python3
"""对 N=100 的正确答案做方法归类，回答：筛完只剩正确答案后，还有几条不同的路。"""
import json, re
from collections import Counter

D = json.load(open("content/2026-10-06-deepseek-synthetic-data/data/exp1-100x.json"))
recs = D["records"]
print("N =", len(recs), " passed =", sum(r["correct"] for r in recs))

# 方法家族关键词
FAM = {
    "单位根/生成函数": [r"单位根", r"五次单位根", r"生成函数", r"母函数", r"复数根", r"分圆", r"roots of unity"],
    "动态规划/递推": [r"动态规划", r"\bDP\b", r"递推", r"转移方程", r"dp\[", r"状态转移"],
    "余数分类计数": [r"余数", r"模\s*5", r"分类讨论", r"每类", r"平均分", r"residue"],
    "补集/容斥": [r"补集", r"容斥", r"反面", r"总数减去"],
    "暴力枚举/程序": [r"暴力", r"枚举所有", r"写个?程序", r"Python", r"代码", r"comput"],
}
def fam_of(txt):
    hits = [k for k, pats in FAM.items() if any(re.search(p, txt) for p in pats)]
    return hits

corr = [r for r in recs if r["correct"]]
fam_cnt = Counter()
for r in corr:
    fs = fam_of(r["text"])
    for f in fs: fam_cnt[f] += 1
    if not fs:
        fam_cnt["(未匹配)"] += 1

print("\n方法家族命中次数（可多条命中）:")
for k, v in fam_cnt.most_common():
    print(f"  {k}: {v}")

# 主方法：按优先级取一个
def primary(txt):
    for name in ["单位根/生成函数", "动态规划/递推", "余数分类计数", "补集/容斥", "暴力枚举/程序"]:
        if any(re.search(p, txt) for p in FAM[name]):
            return name
    return "(未匹配)"
prim = Counter(primary(r["text"]) for r in corr)
print("\n主方法分布（每条取一个）:")
for k, v in prim.most_common():
    print(f"  {k}: {v}")

# 错误答案分布
print("\n错误答案:", Counter(str(r['answer']) for r in recs if not r['correct']))

# 正确答案文本是否含公式/代码特征的多样性
tail_sig = Counter()
for r in corr:
    t = r["text"]
    sig = ("含boxed" if "boxed" in t else "无boxed")
    tail_sig[sig] += 1
print("\n格式特征:", dict(tail_sig))
