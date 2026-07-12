---
type: mixed
density: per-section
style: hand-drawn educational infographic
palette: warm macaron
language: zh
image_count: 4
---

# BPE 文章配图规划

## Illustration 1
**Position**: 第①节“文字 → token 片段 → token ID”之后
**Purpose**: 把分词器、token 和整数编号的关系一次讲清
**Visual Content**: 示例文本经过分段，映射到 token，再映射到 ID；突出三段链路
**Filename**: 01-infographic-token-id.png

## Illustration 2
**Position**: 第②节 `low`、`lo w`、`low e r` 示例之后
**Purpose**: 把 BPE 的逐轮合并过程变成可视化流程
**Visual Content**: `(l, o)` 和 `(lo, w)` 依次合并，展示 `low`、`lower`、`lowest`
**Filename**: 02-flowchart-bpe-merge.png

## Illustration 3
**Position**: 第④节真实 tokenizer 输出与 byte-level 解释之后
**Purpose**: 区分可读文本、token 显示形式和 token ID
**Visual Content**: 混合句子 → byte-level token 显示 → token ID → 14 个 token
**Filename**: 03-infographic-real-tokenizer.png

## Illustration 4
**Position**: 结尾“把整条链路串起来”之后
**Purpose**: 承接下一篇词嵌入
**Visual Content**: 文字 → 字节或初始片段 → token → token ID → 向量
**Filename**: 04-flowchart-token-to-vector.png

## Existing assets

- `00-cover.png`: existing square cover
- `04-sam-altman.jpg`: opening story hook
- `05-strawberry.jpg`: placed after `st / raw / berry`
