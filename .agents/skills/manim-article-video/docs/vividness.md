# 生动化三件套：概念图嵌入 + 数据动效 + 场景转场

纯文字卡片+裸文字的视频单调（PPO 2026-08-15 复盘：S6/S8/S9 图形 0、全片零插图、动画手段仅 type_in/scroll_unroll/FadeIn 三件套）。本文件给三类**可自动化、可沉淀**的生动化手段，供后续文章直接调用。

## 一、AI 概念图嵌入（双轨配图，最直观）

为比喻/场景类台词生成插图，Manim `ImageMobject` 嵌入（3B1B 风格里穿插插画的做法）。**零先例**——历史视频只有 avatar 尾卡用过 ImageMobject，本节把这个能力打开。

### 时机
- **Step 3 storyboard** 阶段规划「插图位」：哪些段落是比喻/场景（骑自行车、天平、学生交卷、拦截盾…）→ 配概念图；哪些是数字/结构/流程 → 配脚本画图（见下）
- **Step 5 前**生成（渲染前图必须就绪，和「先声音后动画」门禁同理：插图也是动画时间轴的素材）

### 生成：yairouter 统一风格流水线
```bash
source ~/.bash_env  # YAI_API_KEY（缺则先 source，见 AGENTS.md）
python3 scripts/yairouter_img.py \
  --prompt "<prompt>" --size 1024x1024 --quality high \
  --output-dir content/<日期>-<主题>/shipinhao/img --filename <slug>.png
```
⚠️ 上游 API 忽略 size 参数（2026-08-07 实测），输出以实际返回为准；尺寸不符用 PIL `resize((1080,1080), LANCZOS)` 放大到正方形后圆角处理。

**prompt 模板（统一深蓝风，复用）**：
```
扁平科技教育插画，深海军蓝背景(#16213E 系)，金黄/青/绿点缀，柔和辉光、微距质感、电影级光影、干净无噪点。
画面主体：<比喻物，如「一辆自行车向右倾斜」「一杆天平左低右高」>。
风格：3Blue1Brown 式极简、几何化、无文字或极少英文标签。
关键视觉元素居中，四周留 15% 留白。
```
**红线（AGENTS.md 双轨配图规则适用）**：
- AI 图**禁止承载数字/年份/公式**（AI 画数字必错）——数字、结构、流程必须用脚本画图（`grow_bar`/`counter_value`/`Create` 轨迹）
- prompt 内文字/数字/年份必须与正文一致（若必须放文字）
- 偏比喻/氛围，不承担信息密度

### 圆角透明处理（融合深蓝画布）
复用 `scripts/make_round_logo.py`（已支持任意图，不只 logo）：
```bash
python3 scripts/make_round_logo.py content/<日期>-<主题>/shipinhao/img/<slug>.png \
  --out content/<日期>-<主题>/shipinhao/img/<slug>-round.png
```
圆角半径默认 12% 边长；方形深底图直接 ImageMobject 会露方框边缘，圆角透明后自然融合。

### 嵌入（scenes.py）
```python
img = ImageMobject("img/<slug>-round.png")
img.scale_to_fit_width(5.5)            # ≤5.5 单位，避安全区
img.next_to(head, DOWN, buff=1.2)       # 锚点链，同卡片
self.play(FadeIn(img, shift=DOWN*0.05), run_time=0.7)  # 插图属 logo/图类，FadeIn 合规
cap = t("一句标注", 26, WHITE).next_to(img, DOWN, buff=0.6)
self.play(type_in(cap, run_time=0.8))   # 标注用打字机
```
- 插图页 = 图 + 1-2 行标注（别堆文字，图为主）
- 安全区同样适用：图宽 ≤5.5、底部 ≥399px、顶部避 1.5
- 换页 FadeOut 必须带走图（A3 对账，图也是 mobject）

### 数量
每片 3-5 张（类比场景优先），多了打断节奏、少了仍单调。封面不算在内（封面单独 yairouter 1080×1920）。

## 二、数据动效增强（helper 化，纯代码无外部依赖）

数字类台词禁止纯文字陈述，必须配动效。已沉淀进 `manim_helpers.py`：

### `counter_value`（数字滚动，2026-08-15 新增）
```python
n = self.counter_value(0, 32, suffix=" 组")   # 已播放滚动，返回 VGroup(数字, 后缀)
n.next_to(card, DOWN, buff=0.5)
# 参数：start, end, suffix="", decimals=0, size=64, color=YELL, run_time=0.9
```
适用：步数/分数/百分比/倍率/参数量。台词念「组大小 32」→ 画面 0→32 滚动；念「省 8 倍」→ 1→8 滚动。

> manim 0.21 起 `DecimalNumber` 默认 `mob_class=MathTex`（需 latex，系统无）——本 helper 已显式 `mob_class=Text` 规避，勿改回（见 [pitfalls.md](pitfalls.md)）。

### `grow_bar`（已有，柱状生长）
```python
bar = Rectangle(width=2.0, height=0.7, color=GREEN, fill_color=GREEN, fill_opacity=0.7)
bar.move_to(...)
tracker = ValueTracker(0)
self.grow_bar(bar, tracker, 2.0, run_time=0.7)   # 从左生长到宽 2.0
```

### 轨迹/链路逐步绘制（Create 分段，无需 helper）
```python
trace = VGroup(*[Rectangle(...) for _ in range(N)])   # N 段
trace.arrange(RIGHT, buff=0.1)
self.play(*[Create(seg) for seg in trace], run_time=1.2, lag_ratio=0.3)  # 逐段绘制
```
适用：200 步轨迹、工具调用链、流程箭头。「一条 N 步的轨迹」→ 画面逐段画出，不一次性出现。

### 数字台词动效清单（写 scenes.py 前自查）
台词含以下即必须配动效，禁止纯文字：
- 步数/次数/条数 → `counter_value` 或 `Create` 分段
- 百分比/倍率/分数 → `counter_value`
- 比较（A vs B）→ `grow_bar` 对比条
- 趋势/分布 → `gaussian_curve`（已有）或自绘坐标图

## 三、场景转场（`transition_out`，2026-08-15 新增）

段间硬切→统一滑出过渡，给下一场景干净入画起点。

```python
# construct 末尾、pad_to_voice() 前：
self.transition_out(head, footer_mob, <本场景全部可见元素>)  # 向右下滑出+淡出 0.6s
self.pad_to_voice()
```
- **必须传当前场景全部可见元素**（含 head / footer / 图 / 卡），漏传即残影（A3 对账）
- 占用 TAIL 缓冲（2.5s）中约 0.6s，剩余由 `pad_to_voice` 补齐——转场也算动作，动作覆盖 ≥80% 规则仍满足
- 全片统一用或不用（别某场景用某场景不用，节奏割裂）；多 agent 模式下 A17 检查全片一致性
- footer 引用：`_Base.footer()` 当前不返回 f，如需带走 footer，调用前先 `f = self.footer()` 改造或场景内自己存引用（TODO：可让 footer() 返回 f 便于转场）

## 四、动效库 v2：镜头语言 + 形变 + 连续运动 + 强调 + 呼吸（2026-08-18 新增；**2026-08-25 起限量使用**）

> ⚠️ **2026-08-25 用户拍板「动画设计过于复杂」**：本节动效从「可用」降级为「限量」——**每片 ≤3 处**（emphasize ≤5 次），只给爆点/公式；**每页只保留 1 个主视觉动效**，其余元素 FadeIn 静态出现即可；禁止在同一 2s 窗口内叠加多个动效。决策 #51，分镜阶段（Step 3）就标好哪些地方用。

PPO 复盘：动效词汇表只有 type_in/scroll_unroll/FadeIn/GrowFromCenter/Create/Flash 六种，全是「离散出现」，没有「连续运动」和「镜头语言」——这是呆板感的根因。以下五类已沉淀进 `manim_helpers.py` 的 `_Base`（基类已改 `MovingCameraScene`，现有场景不受影响）：

### `camera_zoom_to`（镜头推拉，3B1B 灵魂）
```python
self.camera_zoom_to(formula)          # 念公式时推近（默认 0.6 倍）
self.camera_zoom_to()                  # 讲完拉回全画布
```
- **必须成对使用**：推近后拉回，场景末帧相机必须全画布（QA A18）——漏拉回 = 下一场景开场就是放大状态
- 推近后内容仍须在安全区内（A5/A10 对缩放后帧同样适用）；推近目标选画面中上部，别把 footer 推出画外
- 时长计入 at() 排布

### `morph_to`（形变，3B1B 招牌）
```python
self.morph_to(card, curve)                    # 卡片→曲线（ReplacementTransform，默认）
self.morph_to(old, new, replace=False)        # A→B 对照（Transform，source 保留）
```
「A 平滑变成 B」比「A 消失、B 出现」高级一个量级。最适合讲「概念 → 数学表达」「旧状态 → 新状态」的转换。

### `trace_dot`（轨迹追踪点，连续运动）
```python
curve = gaussian_curve(0, 1, 1)
self.play(Create(curve), run_time=0.8)
dot = self.trace_dot(curve, run_time=2.0)     # 点沿曲线滑行 + 黄色拖尾
```
- 连续运动是「画面活着」的关键——比离散出现高级一个量级
- path 支持 ParametricFunction 或任意 VMobject；返回的 dot 换页必须 FadeOut 带走（QA A19）
- 适用：分布曲线讲解、轨迹/链路走查、流程推进

### `emphasize`（关键词强调）
```python
self.emphasize(kw)                    # indicate：抖动放大再缩回（最常用）
self.emphasize(kw, mode="circumscribe")  # 画圈圈住（强调「就是这个」）
self.emphasize(kw, mode="wiggle")       # 摇摆（否定/质疑语气）
```
与 `play_red_cross` 的分工：红叉是否定，emphasize 是肯定/聚焦。circumscribe 的圈是装饰，换页 FadeOut 带走。

### `breathe`（呼吸微动）
```python
self.breathe(card2, loops=2)          # 滞留元素轻微缩放起伏
```
- 幅度 ≤3%（scale ≤1.03），别抢台词注意力；仅用于滞留 >2s 的元素
- 占用台词时间，run_time×loops 计入 at() 排布

### 使用红线
- 镜头推拉必须成对；breathe 幅度 ≤3%；trace_dot 的 dot 换页带走
- 动效时长全部计入 at() 排布（先声音后动画门禁不变）
- 别每句台词都用 emphasize——强调是稀缺资源，用多了等于没强调
- **每片限量（2026-08-25 拍板）**：camera_zoom/morph/trace_dot/breathe 合计 ≤3 处，emphasize ≤5 次；每页仅 1 个主视觉动效；禁止同 2s 窗口多动效叠加。爆点/公式优先分配，日常陈述页只 FadeIn

## 五、emoji 不可用（实测 2026-08-15）

Manim 0.21 的 `Text(font="Noto Color Emoji")` 会丢彩色字形（CBDT/CBLC 位图），渲染只剩汉字、emoji 全消失。`👍📈⚙️🧠` 实测无输出。**禁用 emoji 当图标**——需要图标走概念图（上）或自绘矢量图形组合（`Circle`+`Line` 等 manim 原语）。

## 检查清单对应

- [qa-checklist.md](qa-checklist.md) A15（插图规范）、A16（数字动效）为本文件落地
- 多 agent 模式额外查 A17（跨场景一致性，见 [multi-agent-scenes.md](multi-agent-scenes.md)）