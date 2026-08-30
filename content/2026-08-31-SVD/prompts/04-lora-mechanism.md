# 图 04: LoRA 机制示意图

## Prompt
An educational diagram showing how LoRA works. On the left: a large frozen weight matrix W (blue, with a lock icon). On the right: two small trainable matrices B and A (orange, with no lock). Arrows show that during forward pass, input x goes through both paths: x·W (frozen) and x·B·A (trainable). The outputs are added together. Clean white background, modern infographic style. Label the dimensions: W is d×k, B is d×r, A is r×k, with r << d,k.

## 备注
- 位置：§四"LoRA"之后
- 用途：解释 LoRA 的工作原理
- 风格：教育类信息图，强调冻结 vs 可训练的对比
