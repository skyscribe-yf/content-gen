---
illustration_id: 01
type: comparison
style: notion
palette: warm
---

Dense vs MoE 模型架构对比

Split comparison layout. Left-right split with vertical divider.

LEFT SIDE — "Dense 模型 (GPT-4o)":
- 一个病人（简笔画人物）站在中间
- 8 个科室窗口全部亮起（心内科、骨科、皮肤科、眼科、消化科、神经科、内分泌科、呼吸科）
- 标注"所有科室全看 / 每次激活 100% 参数"
- 8 条连线从病人指向所有窗口

RIGHT SIDE — "MoE 模型 (DeepSeek-V3)":
- 同样的病人
- 分诊台护士（简笔画）伸出手指向神经科和眼科
- 6 个科室灰色/休眠状态
- 标注"分诊制 / 每次激活 8/256 专家 = 3.1%"
- 2 条连线从护士指向选中的科室

BOTTOM: 大字标注 "671B 参数 → 每次推理只有 37B 在工作"

COLORS: Warm Cream background (#F5F0E8), black hand-drawn lines with slight wobble.
Dense side: Coral Red (#E8655A) for active windows, Deep Brown (#744210) for labels.
MoE side: Terracotta (#C05621) for active experts, Warm Orange (#ED8936) for gating,
Gray (#D4C5B9) for dormant experts.

Clean composition with generous white space. Simple or no background. Main elements centered.
Human figures: simplified stylized silhouettes. Hand-lettered Chinese labels.
Text should be large and prominent with handwritten-style fonts. Keep minimal, focus on keywords.
Color values (#hex) and color names are rendering guidance only — do NOT display hex codes as visible text.
ASPECT: 16:9
