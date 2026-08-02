---
illustration_id: 02
type: flowchart
style: editorial-flat-vector
palette: warm-technical
---

RLVR 训练闭环 - 奖励来源与策略更新分离

LAYOUT: 方形画布内从左上到右下的闭环流程；左侧是“奖励来源”区域，右侧是“策略更新”区域，中间用虚线分界。箭头形成闭环，不要做成线性清单。

ZONES:
- 奖励来源区域：问题、策略生成答案或轨迹、编译器/测试/沙箱 verifier、可验证奖励。
- 策略更新区域：PPO、GRPO、策略更新、下一轮采样。
- 中间桥接：奖励箭头从 verifier 指向策略更新；更新箭头回到策略生成。

LABELS: 问题，策略生成，答案或轨迹，编译器，测试，沙箱验证，可验证奖励，策略更新，PPO，GRPO。只使用这些中文标签，不要添加其他文字、数字或英文。

VISUAL RELATIONSHIPS: verifier 是奖励来源模块，PPO/GRPO 是更新模块；两者不能画成同一个节点。用深蓝表示策略，用薄荷绿表示验证成功，用珊瑚红表示验证失败，用紫色表示更新。

STYLE: Clean editorial flat-vector flowchart, rounded cards, precise arrows, dark navy outlines, warm cream background, no gradients, no photorealism, generous white space, clear hierarchy.

COLOR CONSTRAINT: Color values and color names are rendering guidance only — do NOT display color names, hex codes, or palette labels as visible text.

ASPECT: 1:1, 1K, square composition.
