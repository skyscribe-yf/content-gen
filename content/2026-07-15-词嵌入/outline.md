---
type: infographic
density: rich
style: sketch-notes
palette: macaron
image_count: 6
---

## Illustration 1

**Position**: ① 第一步：把词变成编号 — 分词结果展示之后
**Purpose**: 可视化分词过程，让读者直观看到文本→token ID的映射
**Visual Content**: 输入句子"今天天气真好"被切成6个token块，每块标注ID编号，像标签贴纸一样
**Type Application**: infographic — 数据映射可视化
**Filename**: 01-infographic-tokenization.png

## Illustration 2

**Position**: ② One-hot — "猫和狗的距离 = 猫和汽车的距离"之后
**Purpose**: 展示one-hot向量的正交性，所有向量互相垂直、距离相等
**Visual Content**: 3个one-hot向量[1,0,0][0,1,0][0,0,1]在3D空间中互相垂直，用虚线标注"距离全等"
**Type Application**: infographic — 概念对比
**Filename**: 02-infographic-onehot-orthogonal.png

## Illustration 3

**Position**: ③ 嵌入矩阵 — "129,280 × 7,168 ≈ 9.27 亿"之后
**Purpose**: 可视化嵌入矩阵的规模和查表操作
**Visual Content**: 巨大的表格（行=token，列=维度），高亮一行表示查表抽出，one-hot向量×矩阵=行向量的数学操作
**Type Application**: infographic — 数据结构可视化
**Filename**: 03-infographic-embedding-matrix.png

## Illustration 4

**Position**: ④ 中药柜隐喻 — "语义空间 = 不是老中医设计的"之后
**Purpose**: 用中药柜隐喻可视化嵌入训练过程
**Visual Content**: 中药柜抽屉图，当归和川芎的抽屉用箭头连在一起（近义词），大黄的抽屉被拉开远离（不相关），机器齿轮表示训练调整
**Type Application**: infographic — 隐喻可视化
**Filename**: 04-infographic-herb-cabinet.png

## Illustration 5

**Position**: ⑤ 余弦相似度 — "搜苹果手机能找到iPhone"之后
**Purpose**: 可视化余弦相似度的三个场景（同向/垂直/反向）和语义空间中的邻居关系
**Visual Content**: 2D坐标空间中，"开心"和"高兴"方向一致（cos≈1），"猫"和"汽车"垂直（cos≈0），"苹果手机"和"iPhone"是邻居
**Type Application**: infographic — 概念可视化
**Filename**: 05-infographic-cosine-similarity.png

## Illustration 6

**Position**: ⑥ Word2Vec延伸 — "vec(国王)−vec(男人)+vec(女人)≈vec(女王)"之后
**Purpose**: 可视化语义算术和Word2Vec vs 上下文嵌入的升级
**Visual Content**: 左侧：向量算术 国王−男人+女人≈女王 的箭头运算；右侧：Word2Vec固定身份证 vs Transformer穿不同衣服的对比
**Type Application**: infographic — 概念对比+算术可视化
**Filename**: 06-infographic-word2vec-arithmetic.png
