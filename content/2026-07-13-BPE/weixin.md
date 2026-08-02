---
title: "BPE分词：AI为什么把文字切成碎片？"
author: "数解AI"
digest: "为什么 AI 不按词读字？BPE 分词用频率统计把句子切成 token，切法直接影响上下文窗口和 API 费用。从原理到代码，一次讲懂 Tokenizer 内部机制。"
type: "原理篇"
series: "大模型原理"
keywords: ["BPE", "分词", "Tokenizer", "token", "API计费"]
cover: 00-cover.png
wechatUrl: "https://mp.weixin.qq.com/s/5nR_KI47v_U8KwpQA4Uv5Q"
scheduledPublish: "2026-07-13T08:00:00+08:00"
---

这是「大模型原理」系列的**第一篇**。

**BPE 分词（Byte Pair Encoding）** 解决一件事：大模型不按「词」读字，而是把文字切成 **token**。切多了，上下文更短、API 更贵；切法不对，模型还会在数字母这种题上翻车。

如果你刚看过 [DeepSeek 为什么便宜约 30 倍](https://mp.weixin.qq.com/s/QdkD0CR2fD-HfY77-gX3Ug)，或 [AI 上下文为什么越长越慢](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q)，账单和速度里反复出现同一个单位：**token**。训练回路（[梯度下降](https://mp.weixin.qq.com/s/V6mGvCVFpTvmC51pNtxiTw) → [Adam](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)）讲的是参数怎么学；本系列从**文字怎么进模型**讲起。

链路很短，但每一步都踩坑：

> **文字 → BPE 分词（本篇）→ 词嵌入 → 位置编码 → 注意力 → …**

这里先拆入口：一句话为什么被 Tokenizer 切成奇怪的碎片？下一篇再讲 token ID 怎么变成向量。

## 🎯 驱动问题

你输入一句话，模型先把它切成一串 token。

但在聊 token 之前，先看一个现象。

2023 年到 2024 年初，当时最先进的大模型有一个让人哭笑不得的短板——数不清 `strawberry` 里有几个 `r`。你问它，它经常回答 2 个（正确答案是 3 个）。能做微积分、能写代码的模型，连数字母这种小学生题目都会翻车。很多人第一次遇到时都愣了一下：它到底是怎么"看"文字的？

这道题后来和 Sam Altman、OpenAI 的"Strawberry"项目联系在一起，成了模型讨论里的经典梗。但把梗放在一边，它抛出了一个真正值得追问的问题：**模型到底是按什么单位看文字？**

![Sam Altman 草莓帖文与网友回应的合成截图](04-strawberry-x-collage.png)

*左：Sam Altman 于 2024 年 8 月 7 日在 X 发布的草莓照片；右：网友用同一张图玩“数草莓”的回应。来源：X 帖文及用户提供截图。*

比如：

> 请用 Python 写一个 Transformer，参数量 7B。

人类一眼看出这里有中文、英文、数字和标点。分词器的工作方式更朴素：它只负责把这串字符切成模型能查表的片段。

DeepSeek-V4-Pro 的 tokenizer 实际跑出来是 14 个 token：

```text
请用 Python 写一个 Transformer，参数量 7B。
→ 14 个 token
```

有时，一个汉字会和邻居合成 token；英文单词可能完整保留，也可能被切成几段；数字 `7B` 甚至会拆成 `7` 和 `B`。

为什么不干脆按“词”切？

BPE 的眼里没有“词”这个概念。它更像一台统计机器：哪些相邻片段总是一起出现？那就把它们粘起来。

它只做一件事：**在训练语料里寻找高频的相邻片段，把它们合并起来。**

下面从字符开始，一步步看片段怎样合并，最后再看看真实模型到底怎么切。

<!-- 配图 01：封面。核心文字：一句话，为什么被切碎？ -->

## ① 模型为什么不直接读文字？

神经网络不能直接把“猫”“Transformer”塞进矩阵乘法。

它需要整数编号：

```text
“猫”          →  某个整数
“Transformer”  →  另一个整数
“。”           →  还有一个整数
```

这本“文字到整数”的字典，就是词表（vocabulary）。分词器做的工作，可以写成三步：

```text
文字 → token 片段 → token ID
```

这里先把一个容易混淆的地方说清楚：token 不等于词。

它可能是一个完整的词，也可能是半个词、一个汉字、几个汉字、一个数字，甚至是字节级碎片。

DeepSeek-V4-Pro 的公开 `config.json` 里，`vocab_size` 是 **129280**。但这不等于“有 129280 个完整词”：它的 `tokenizer.json` 显示，基础 BPE 模型词表是 **128000** 个条目，另外还配置了 added tokens 和特殊 token。

这里有一个容易踩的坑：`config.json` 的模型词表规模和 `tokenizer.json` 里的基础 BPE 词表，不是两个可以随手相加的数字。写文章时要按字段含义分别看。

![文字到 Token ID 的三段映射](01-infographic-token-id.png)

*分词器把文本切成 token，再为每个 token 分配整数编号。图片仅展示部分 token 作为示例，实际该句共 14 个 token。*

## ② BPE 怎么把小片段粘成大块？

BPE 的全名是 Byte Pair Encoding，最早并不是为大模型发明的。它原本是一种压缩思路：反复寻找最常出现的一对相邻符号，把它们替换成一个新符号。

后来，这套"高频片段合并"的办法被用来构造子词词表（Sennrich 等人在 2016 年将 BPE 引入神经机器翻译中处理罕见词）。

先不用真实词表。看一个缩小版例子。

假设训练语料里反复出现这些词：

```text
low    low    lower    lowest
```

一开始，模型把每个词拆成字符：

```text
l o w
l o w
l o w e r
l o w e s t
```

统计所有相邻字符对：

```text
(l, o) 出现 4 次
(o, w) 出现 4 次
(w, e) 出现 2 次
(e, r) 出现 1 次
```

最高频的 pair 是 `(l, o)`，先把它们粘起来：

```text
l o w → lo w
```

再数一遍。`lo` 和 `w` 还是经常挨在一起，于是继续合并：

```text
lo w → low
```

现在，`low` 已经成了一个 token。`lower` 可以表示为：

```text
low e r
```

`lowest` 则可能变成：

```text
low e s t
```

BPE 的脾气可以概括成一句话：**常见片段越合越大，罕见片段先保持小块。**

所以它不是“词典里有没有这个词”的二选一。

一个词太常见，就整体进入词表；一个词没见过，也可以拆成模型认识的片段。新词、错别字、代码变量名，通常都能找到某种拆法。

<!-- 配图 03：low → low e r → lowest 的逐轮合并过程 -->

![BPE 高频片段逐轮合并](02-flowchart-bpe-merge.png)

*BPE 每轮寻找高频相邻片段，再把它们合并。*

## ③ 用一小段代码看懂 BPE

把刚才的过程写成代码，核心就四步：数 pair、找最高频的一对、合并，然后继续循环。

```python
from collections import Counter

def get_pairs(words):
    return Counter(
        pair
        for word in words
        for pair in zip(word, word[1:])
    )

def merge_pair(words, target):
    merged_words = []
    for word in words:
        merged, i = [], 0
        while i < len(word):
            if i + 1 < len(word) and (word[i], word[i + 1]) == target:
                merged.append(word[i] + word[i + 1])
                i += 2
            else:
                merged.append(word[i])
                i += 1
        merged_words.append(merged)
    return merged_words

words = [list(word) for word in ["low", "low", "lower", "lowest"]]

for _ in range(2):
    pairs = get_pairs(words)
    best_pair, count = pairs.most_common(1)[0]
    words = merge_pair(words, best_pair)
    print(best_pair, count, words)
```

这段代码是教学版，故意把复杂度压低了。真实 tokenizer 还要处理空格、Unicode、字节、特殊 token，以及合并后的匹配顺序等工程细节。

但算法的骨架没有变：

> **频率统计 → 选择 pair → 合并 → 更新词表。**

训练完成后，tokenizer 会保存两样东西：一张 token 到 ID 的词表，以及一组有顺序的 merge rules。推理时不再重新统计语料，只按照已经学好的规则，把新文本切成 token。

## ④ 看真实模型：DeepSeek-V4-Pro 怎么切一句话？

刚才的代码只解释“合并规则怎么长出来”。真实 tokenizer 还得处理空格、字节和特殊 token。用 DeepSeek-V4-Pro 的分词器切一次混合文本，就能看到它具体怎么下刀。

这段代码直接加载 DeepSeek-V4-Pro 公开仓库里的 tokenizer：

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "deepseek-ai/DeepSeek-V4-Pro"
)

text = "请用 Python 写一个 Transformer，参数量 7B。"
tokens = tokenizer.tokenize(text)
ids = tokenizer.encode(text, add_special_tokens=False)

print(tokens)
print(ids)
print(len(ids))
```

按 2026 年 7 月 10 日核验到的公开 tokenizer，输出是：

```text
tokens:
['è¯·', 'çĶ¨', 'ĠPython', 'Ġ', 'åĨĻ', 'ä¸Ģä¸ª',
 'ĠTransformer', 'ï¼Į', 'åıĤ', 'æķ°éĩı', 'Ġ', '7', 'B', 'ãĢĤ']

ids:
[2788, 642, 15255, 223, 2935, 1057, 105668, 303,
 2294, 9853, 223, 25, 36, 320]

count:
14
```

先别被 `è¯·`、`çĶ¨` 这些片段吓到。这里看到的是 byte-level BPE 的“工作现场”：中文先变成 UTF-8 字节，tokenizer 再把这些字节映射成可以合并的片段。打印 token 时，某些字节会借用可打印字符来显示，于是人眼看上去像乱码。

英文片段就比较给面子：`ĠPython`、`ĠTransformer` 还能勉强认出来。开头那个 `Ġ` 也不是神秘字母，它表示这个片段前面带着一个空格。中文的 UTF-8 字节则不太客气，直接把编码过程的痕迹摊在了桌面上。

所以这里要区分两件事：`tokenize()` 打印的是 tokenizer 内部的显示形式；模型真正使用的是对应的 token ID。乱码只是显示得不友好，不代表输入被破坏了。

看 token ID 就清楚多了：`Transformer` 作为一个带前导空格的 token 出现，`7B` 被拆成 `7` 和 `B`，句号也有自己的 token。

![真实 tokenizer 输出的三种视角](03-infographic-real-tokenizer.png)

*同一段输入，可以分别从可读文本、token 显示形式和 token ID 三个角度观察。图片仅展示 5 个 token 作为示例，实际该句共 14 个 token。*

再看一句纯中文：

```text
今天天气真好，适合出去玩
→ 6 个 token
```

这 6 个 token 分别对应：`今天`、`天气`、`真好`、`，`、`适合`、`出去玩`。

这就解释了标题里的“奇怪碎片”：token 的边界不按人类的词语划线，它留下的是训练语料和合并规则共同作用的痕迹。

回头看开头那道题，用本文的 tokenizer 看一眼：

```text
strawberry
→ st / raw / berry
```

模型接收到的是几个 token 片段，并非一张逐字母展开的清单。分词方式能解释一部分直觉落差，但它并不能单独解释模型为什么会数错；后面的推理过程同样关键。这个坑先留个预告，等讲到推理时再展开。

## ⑤ 切法不同，为什么会影响使用？

模型每读一段文字，都要先把它变成 token。token 越多，意味着：

- 同一个上下文窗口里能放的原文更少；
- 生成同样内容，需要处理更多离散单位；
- 按 token 计量的 API，用量也会增加。

但“几个字等于一个 token”没有固定答案。

中文短语可能被合并成一个 token；英文常见词也可能整体保留；代码、数字、罕见符号则更容易被拆细。下面三个字符串看起来长度差不多，token 数可能完全不同：

```text
中文说明
Python 函数
7B + UTF-8
```

所以调试长上下文问题时，光数字符不够，数“有多少个词”也不够。真正进入模型的是 token 序列；切得越细，同一段文字就会占掉越多位置。

这也是 API 文档总在提醒你“按 token 计费”的原因。具体价格会随模型和服务变化，下一篇先记住一个判断方法：**先数 token，再估算上下文和用量。**

## ⑥ BPE 只是其中一种分词方法

分词器不全用 BPE。常见路线有三种：

- **BPE**：每轮找出最高频的相邻片段，把它们合并。
- **WordPiece**：选择更有助于提升语言模型概率的片段。
- **Unigram**：先准备一张较大的候选词表，再不断删掉不重要的片段。

工程上还会叠加 byte-level、预分词和特殊 token 规则。

这些方法的路线不同，但目标很接近：**让常见内容短一点，让罕见内容也能被表示。**

## 🔄 回到开头

AI 为什么把一句话切成奇怪的碎片？

因为 tokenizer 只认得统计规律。BPE 从字符或字节开始，数哪些片段经常相邻，再把它们逐轮合并成 token。训练完成后，tokenizer 按固定的词表和 merge rules，把新文本变成 token ID。

把整条链路串起来：

```text
文字
  ↓ 预处理 / 预分词
字节或初始片段
  ↓ BPE 合并规则
token
  ↓ 查词表
token ID
  ↓ 嵌入矩阵
向量
```

下一篇要接着问：一个 token 拿到 ID 之后，怎么变成模型能计算的高维坐标？答案是词嵌入。

## 📌 一句话总结

**BPE 会根据训练语料里的频率合并相邻片段：常见片段变成大块，罕见内容保留小块，最后每个 token 查表得到一个 ID。**

<!-- 配图 05：文字 → BPE token → ID → embedding 的系列承接图 -->

![从文字到向量的完整链路](04-flowchart-token-to-vector.png)

*下一篇词嵌入会接着解释：token ID 如何查出模型可计算的向量。*

---

📖 **大模型原理**（本系列 · 第 1/10 篇）
① BPE分词：AI为什么把文字切成碎片？（本篇）→ ② 词嵌入是什么？5万个0怎么变成一串坐标（07/15）→ ③ 位置编码怎么工作？词序一错意思全变（07/17）→ ④ 注意力机制是什么？别再当数据库查询（07/19）→ ⑤ FFN → ⑥ 归一化与残差 → ⑦ Transformer → ⑧ [预训练](https://mp.weixin.qq.com/s/XoGHVycQHR5Tp-BWPac9Hg) → ⑨ RLHF → ⑩ 推理加速

🔥 **DeepSeek 技术解密**（账单与工程）
① [AI上下文为什么越长越慢](https://mp.weixin.qq.com/s/PLVRS0TTHXHDve1Z3r6M7Q) → ② [MoE混合专家入门](https://mp.weixin.qq.com/s/QdkD0CR2fD-HfY77-gX3Ug) → ③ MLA（待发布）

📖 **深度学习基础**（已完结）
① [梯度下降](https://mp.weixin.qq.com/s/V6mGvCVFpTvmC51pNtxiTw) → ② [损失函数](https://mp.weixin.qq.com/s/zIWqYqYVzEaF1e8P6fcTfw) → ③ [反向传播](https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g) → ④ [Softmax](https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw) → ⑤ [残差连接](https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg) → ⑥ [Adam优化器](https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA)

每 2 天更新一篇，把大模型从输入到生成的链路讲到不用回头查。关注「数解AI」，下一篇第一时间推给你。

---

*如果这篇帮到了你，点个「在看」让更多朋友看到。*你在调用大模型时，遇到过「明明没写多少字，token 却涨得很快」的情况吗？当时输入的是中文、代码，还是中英混合——你觉得哪个更「烧 token」？评论区聊聊。


