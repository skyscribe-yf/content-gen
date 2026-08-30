# 图 03: 截断 SVD 重建误差

## Prompt
A line chart showing reconstruction error vs number of singular values kept. X-axis: number of singular values kept (0 to 100), Y-axis: reconstruction error (log scale, from 10^-8 to 1). The curve decreases rapidly as more singular values are kept. At k=10, error is about 0.01 (1%). At k=50, error is about 10^-6. Title: "Truncation Error vs k". Clean white background, minimalist design. Show the trade-off between compression and accuracy.

## 备注
- 位置：§三"低秩近似"之后
- 用途：展示截断误差
- 数据：误差 = √(Σ_{i=k+1}^{100} 0.9^{2i})
- 风格：简洁的科学图表
