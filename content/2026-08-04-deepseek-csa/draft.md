# DeepSeek-V4 注意力工作稿

正文版本见 [`weixin.md`](weixin.md)。

本稿的技术依据、实验参数和开放问题记录在 [`outline.md`](outline.md)；`experiment.py` 只做机制计数，不代表官方 V4 性能。

写作时保留三条边界：

- DSA 是 V3.2 的 MLA 叠加模块，CSA/HCA 才是 V4 的混合注意力。
- 论文报告数字与社区 mini 实验分开写。
- `K = V`、Partial RoPE/de-RoPE 的完整推导留给第二篇。
