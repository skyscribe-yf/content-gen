# 事实来源

核对时间：2026-10-07。贴图只用下面能对上原文的句子。

## 选题档位

出圈猎奇，接近 09-05 费马大定理那档：普通人听得懂「一次甩出 722 篇数学稿，模型却不给用」。当天/次日窗口（官方 10 月 6 日发，今天 10 月 7 日）。

同日扫到、本篇不用：

- Mistral Large 4（Le Chonk），10 月 6 日，HN 约 1690 分。1T 总参 / 49B 激活，权重月底，API 预览 $1.36 / $4.18。圈内大事件，可另做一篇。
- OpenAI Pro 200 用量腰斩、新 Pro 500。钱包题材，但已流传约一周，错过当天窗口。

## 官方

- OpenAI，2026-10-06，*Sharing AI progress in mathematics*  
  https://openai.com/index/sharing-ai-progress-in-mathematics/  
  内部前沿模型产出的数学结果；咨询了高等研究院「数学与人工智能顾问组」，发布方式参考其公开建议。GitHub：https://github.com/openai/math  
  「The average result used the equivalent compute of roughly three hours of ChatGPT Pro thinking.」  
  模型尚未放出：「working to responsibly release the model that produced these results.」

- 仓库 README（2026-10-07 抓取）https://github.com/openai/math  
  - 「The current catalogue contains 722 manuscripts organized into 372 families.」  
  - 「This collection includes results at different stages of verification. Not all have accompanying Lean formalizations.」  
  - 「Some of the unformalized results could have issues.」  
  - 「On average, each result used three hours of ChatGPT Pro thinking compute with that model.」  
  - 「the model was posed approximately 4,000 problems.」  
  - 「unreleased internal OpenAI model.」  
  - 例外流程包括黎曼 ζ 函数无零点区域，以及「proof of the Hodge Conjecture for CM abelian varieties」。  
  - 「the writeup for the Re(s) > 11/12 zero-free region for the Riemann zeta function was human edited for readability.」

- Lean 对照文件（2026-10-07 抓取原文）  
  https://github.com/openai/math/blob/main/lean/ComparatorChallenges/BarnetteHamiltonian.lean  

```lean
theorem main : MainStatement.{u} := by
  sorry
```

- 同题说明 https://github.com/openai/math/blob/main/lean/docs/180.md  
  「The formalization proves this statement for every such graph.」  
  论文：*Paired states and Hamiltonian cycles in cubic bipartite planar graphs*（September 24, 2026）。

## 顾问组

高等研究院 Advisory Group on Mathematics and Artificial Intelligence，2026-09-29  
https://agmai.org/general-sep29/

「we do not endorse this practice, and we ask them to stop testing advanced mathematical problems on proprietary models.」

同文还写：用内部闭源模型做数学研究，会把实验室和整个数学共同体拆成两层。

## Barnette 猜想

- 1969 年由 David W. Barnette 提出。Wolfram MathWorld 引 *Recent Progress in Combinatorics*（1969）；Wikipedia、arXiv:1310.5504 同此年份。  
- 陈述：每个 3-连通、三次、二部、平面图都有哈密顿圈（每个顶点正好经过一次的圈）。  
- Wikipedia《Barnette's conjecture》页，抓取时标注更新于 2026-09-29，仍列为 unsolved。该日期早于 10 月 6 日这次发布。

## 讨论热度（会变，不写进图）

- Hacker News https://news.ycombinator.com/item?id=49984923  
  2026-10-07 抓取时首页第 1，720 分，656 条评论。  
- 评论里 jboggan：Barnette 猜想断断续续想了 24 年；并指出 Lean 文件里是 `sorry`。这是公开评论，不是官方履历。  
- OpenAI 原帖 https://x.com/OpenAI/status/2107596713791767021  
  2026-10-07 抓取时约 1.98 万赞、451 万浏览。图内不用这个会变的数。

## 不写进正文的说法

- 「一天干完数学界十年」：是转帖，不是官方数字。  
- 「证明了唯一游戏猜想」「解了霍奇猜想」：本篇未从仓库逐篇核对到可以这么说的程度。霍奇只按 README 的 CM 阿贝尔簇特例写。  
- 不把 722 篇都写成已证明。仓库自己说验证进度不一，未形式化的可能有问题。  
- 不画陶哲轩或任何真人脸。
