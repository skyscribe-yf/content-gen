---
type: infographic
style: notion
palette: warm
density: per-section
image_count: 8
language: zh
---

## Illustration 1
**Position**: Section "为什么不能直接取最大值" - softmax vs argmax 投票类比
**Purpose**: 展示 argmax 和 softmax 两种投票方式的区别——argmax 独裁 vs softmax 比例代表
**Visual Content**: 左边 argmax：一个人举牌，其他人0票；右边 softmax：所有人按比例分票，C拿97%但A和B各有2.7%和0.2%的残留
**Filename**: 01-voting-analogy.png

## Illustration 2
**Position**: Section "指数归一化" - softmax vs 直接归一化对比
**Purpose**: 对比直接除以sum（负数问题）和 e^z 归一化（指数放大差距）
**Visual Content**: 上半：直接归一化，负数变负概率（红色叉号）；下半：指数归一化，e^z 放大差距，z=[2.1,-0.3,5.7]→[2.7%,0.2%,97.1%]
**Filename**: 02-softmax-vs-norm.png

## Illustration 3
**Position**: Section "链式法则的魔法" - p-y梯度简化
**Purpose**: 展示 softmax+交叉熵 的梯度简化为 p-y，和 sigmoid+交叉熵 同一套魔法
**Visual Content**: 中间大箭头：复杂链式求导过程→简单 p-y 结果；两侧对比：sigmoid+CE 和 softmax+CE 共享同一公式
**Filename**: 03-chain-magic.png

## Illustration 4
**Position**: Section "温度参数" - 温度对分布形状的影响
**Purpose**: 展示 T=0.1/1.0/5.0 三种温度下 softmax 分布的形状变化
**Visual Content**: 三个并排的分布曲线图：T=0.1（尖峰，几乎只有1个类）、T=1.0（中等尖锐）、T=5.0（平坦均匀），物理类比标注：晶体/液体/气体
**Filename**: 04-temperature-shape.png

## Illustration 5
**Position**: Section "语言模型的输出层" - LLM 每步 softmax
**Purpose**: 展示语言模型生成一个词的全流程：输入→transformer→logits→softmax→采样→输出词
**Visual Content**: 流程图：输入序列→Transformer层→logits向量(129,280维)→softmax→概率分布→top-k/top-p采样→输出词。标注DeepSeek-V4 129,280词表
**Filename**: 05-llm-output.png

## Illustration 6
**Position**: Section "实测：温度 × 网络深度" - 温度对比结果表
**Purpose**: 可视化2/6/10层网络×T=0.1/1.0/5.0的90%准确率步数
**Visual Content**: 热力图/矩阵图：行=网络深度(2/6/10层)，列=温度(0.1/1.0/5.0)，单元格=步数，颜色深浅表示收敛速度。关键数据：2层T=0.1=3步✅，6层T=0.1=学不了❌，10层T=5=36步✅
**Filename**: 06-temperature-comparison.png

## Illustration 7
**Position**: Section "实测" - 深度×温度核心规律图
**Purpose**: 可视化"网络越深温度影响越大"的规律——2层/6层/10层的训练曲线对比
**Visual Content**: 三条训练曲线叠加：2层(3条线都收敛)、6层(T=0.1崩/其他收敛)、10层(只有T=5收敛)。梯度流动示意图：浅网络梯度畅通，深网络低温梯度消失
**Filename**: 07-depth-temperature.png

## Illustration 8
**Position**: Section "实测" - 梯度流向对比
**Purpose**: 展示 T=0.1/1.0/5.0 三种温度下梯度的实际流向（同一组logits, 真实类=第3个）
**Visual Content**: 三组梯度条形图：T=0.1(类别1≈0, 类别2≈0, 类别3=-10)、T=1.0(类别1=0.027, 类别2=0.002, 类别3=-0.971)、T=5.0(类别1=0.112, 类别2=0.034, 类别3=-0.146)
**Filename**: 08-gradient-flow.png
