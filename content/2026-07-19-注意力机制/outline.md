---
type: mixed
series: 大模型原理
style: notion
palette: warm
image_count: 6
size: "1:1"
resolution: "1k"
---

# 注意力机制配图计划

## Illustration 1
**Position**: 开头“向量之间，关系从哪里来”后。  
**Purpose**: 回顾 token 在进入注意力前已经带有词义与位置信息。  
**Visual Content**: “猫追老鼠”依次经过分词、词嵌入、位置编码，得到带位置标签的向量序列。  
**Filename**: 01-token-pipeline.png

## Illustration 2
**Position**: 数据库类比段落后。  
**Purpose**: 对比“命中一条记录”和“按权重汇总”的计算差异。  
**Visual Content**: 左侧传统键值查找，右侧 Q/K/V 对允许位置打分并汇总 V。  
**Filename**: 02-roundtable-vs-database.png

## Illustration 3
**Position**: “关注”不是“只看一个”段落后。  
**Purpose**: 区分二元选择和 softmax 权重分配。  
**Visual Content**: 同一组 token 在“只选一个”和“0.7/0.2/0.1 分配”两种情形下的对比。  
**Filename**: 03-look-vs-distribute.png

## Illustration 4
**Position**: 点积几何直觉段落后。  
**Purpose**: 说明向量方向与匹配分数的关系。  
**Visual Content**: Q 与 K₁ 方向接近、与 K₂ 近乎正交的二维坐标示意。  
**Filename**: 04-dot-product-geometry.png

## Illustration 5
**Position**: 随机初始化注意力权重示例后。  
**Purpose**: 展示因果 mask 产生的上三角零值，以及每行权重和为 1。  
**Visual Content**: 4×4 因果注意力热力图，token 为猫、追、老、鼠。  
**Filename**: 06-attention-heatmap.png

## Illustration 6
**Position**: Qwen3-8B GQA 段落后。  
**Purpose**: 说明 32 个 Q 头如何共享 8 组 KV，为什么减少 KV Cache。  
**Visual Content**: MHA 与 GQA 并排结构图，标明 32、8、每 4 个 Q 头共享 1 组 KV。  
**Filename**: 05-gqa.png
