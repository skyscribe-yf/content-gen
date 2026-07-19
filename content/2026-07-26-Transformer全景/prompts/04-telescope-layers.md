# 04-telescope-layers — Attention telescope: shallow local → deep global (English prompt)

IMPORTANT: This must be a node-graph visualization, NOT a text-highlighting diagram. Do not generate paragraphs of filler text. Use 7 labeled nodes connected by lines of varying brightness.

CHINESE TEXT REQUIRED ON IMAGE:
- Title: 注意力就像望远镜
- Layer labels: 第 1 层：短焦, 第 14 层：中焦, 第 28 层：长焦
- Node labels (exactly these 7 Chinese tokens): 这篇文章, 用, 一句话, 走, 完, Transformer, 全过程
- Side annotation (vertical, left): 层越深 → 视野越广 → 关注越精准
- Bottom source note: 基于 Qwen3-1.7B 实测注意力数据
- Right labels per layer: 逐字阅读, 锁定主题词, 全局语义锚定

LAYOUT (top to bottom, 3 rows):

Each row = one layer, showing a circular "telescope lens" frame. Inside each circle, 7 small labeled nodes arranged left to right, connected by colored lines. Line brightness = attention weight (brighter = higher attention).

**Row 1 — Layer 1 (Short focus)**
Color theme: Blue (#4A90D9)
Inside the circle: 7 nodes labeled 这篇文章, 用, 一句话, 走, 完, Transformer, 全过程. Each node has a bright self-loop. Each node also has a moderately bright connection line to its immediate left neighbor (e.g., 用 connects to 这篇文章). All other cross-node connections are very dim or absent. This creates a strong diagonal + near-diagonal pattern.
Right label: 逐字阅读

**Row 2 — Layer 14 (Medium focus)**
Color theme: Cyan (#2E9CCA)
Inside the circle: Same 7 nodes. The first node (这篇文章) glows much brighter than others. Every other node (用 through 全过程) has a thick bright line pointing back to 这篇文章. Self-loops are weaker than in Layer 1. Nodes still have some moderate connections to their neighbors, but the dominant pattern is "all arrows → first node."
Right label: 锁定主题词

**Row 3 — Layer 28 (Long focus)**
Color theme: Purple (#8B5CF6)
Inside the circle: Same 7 nodes. The first node (这篇文章) is extremely bright, almost radiating. Every other node has a very thick, bright line pointing exclusively to 这篇文章. Self-loops and neighbor connections are nearly invisible. The pattern is "everything locks onto the first node."
Right label: 全局语义锚定

VISUAL STYLE:
- Deep dark background (#0a0a1a to #1a1a2e gradient)
- Circular frames have a thin glowing border matching each layer's color
- Nodes are small circles (approximately 12px diameter) with the Chinese label next to each
- Connection lines between nodes are curved arcs with glow effect, thickness and brightness proportional to attention weight
- Left side: vertical Chinese text annotation with down-arrows connecting the three layers
- All Chinese text must be legible at 1024×1024 resolution — use clean sans-serif font, white or light text on dark background
- Top title "注意力就像望远镜" in large glowing cyan/blue text

DO NOT:
- Generate paragraphs of placeholder Chinese text instead of the node graph
- Use human figures, faces, or realistic photography
- Include any English text (only the Chinese labels specified above)
- Add logos or brand marks
- Make the nodes unreadable or overlapping
