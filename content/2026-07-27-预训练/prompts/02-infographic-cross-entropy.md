---
illustration_id: 02-cross-entropy
type: infographic
style: vector-illustration
palette: warm
---

Cross Entropy Decomposition - H(p) + D_KL

Central infographic titled "交叉熵分解" showing the mathematical relationship between cross-entropy, entropy, and KL divergence.

LAYOUT: Top-to-bottom flow with three connected zones.

TOP ZONE: Cross-entropy equation shown as a large container:
"交叉熵 H(p,q) = −Σ p(x) · log q(x)"
Visual: A vertical bar divided into two colored segments.

MIDDLE ZONE: The decomposition arrow splits into two parallel containers:
LEFT: "H(p) = 真实分布的熵" (Entropy of true distribution)
- Label: "固定不变，模型控制不了" (Fixed, model cannot change)
- Visual: A locked padlock icon
RIGHT: "D_KL(p‖q) = KL散度" (KL Divergence)
- Label: "模型要最小化的目标" (What model minimizes)
- Visual: A downward trending arrow icon

BOTTOM ZONE: Conclusion box:
"最小化交叉熵 = 最小化 KL 散度"
Subtitle: "让模型分布 q 逼近真实分布 p"

COLORS: Soft Peach background (#FFECD2), H(p) segment in Warm Orange (#ED8936), D_KL segment in Terracotta (#C05621), conclusion in Golden Yellow (#F6AD55), Deep Brown (#744210) for text

ELEMENTS: Black outlines, rounded containers, bold Chinese labels, connecting arrows between zones, simple icons (lock, target,_equals sign)

STYLE: Clean vector illustration, generous white space, centered composition

ASPECT: 1:1
