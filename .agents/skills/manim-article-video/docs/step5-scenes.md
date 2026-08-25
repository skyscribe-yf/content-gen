# Step 5 写 Manim 场景 scenes.py

## ⛔ 时序门禁（硬性）：先声音，后动画（用户拍板 2026-08-17）

动画设计（内容、出现时间、滞留时间）必须在配音/录音**完成并确认后**才开始：

1. **声音就绪**：TTS 模式 = 切分验证通过 + VOICE_DUR 实测值；口播模式 = `voice_process.py` 完成 + 门禁 4/5 通过 + `tts/pauses.json` 生成。**禁止用预估时长设计动画**（按预估排 at() → 实录时长变化 → 全部节点重排返工）
2. **时间轴完全对应（硬性）**：每个动画元素的**出现时间 = 对应台词字幕的起始时间戳**（`self.at(t)` 精确挂接）；**滞留时间 = 字幕结束 / 下一句字幕开始**（FadeOut 不得晚于下一句字幕出现，也不得早于本句讲完）
3. **锚点来源**：字幕时间线 = `tts/pauses.json`（口播，静音结束点 = 下一句语音起点）或 `full.subtitle.json`（TTS 句子时间戳）；scenes.py 的每个 `at(t)` 必须能从字幕时间线逐条回溯
4. **校验**：写完 scenes.py 逐场景核对——每个 `at(t)` 对应一条字幕边界；元素 FadeOut 时刻与下一句字幕开始对齐；最后一个 play 结束 ≥ 配音 80%（QA 清单 A14 自动核查）

**通用工具全部在 `scripts/manim_helpers.py`（模块化，2026-08-17 起，勿再复制进文章目录）**：
竖屏 config/颜色/t()/_card()/boxed()/boxrow()/fit()/sup()/sub()/sigma_term()/gaussian_curve()/type_in()/cnode()/edge_pt()/arc_curve()/layout_page()/page_stack()/_Base 全家桶（at/pad_to_voice/footer/bg/play_red_cross/play_mark/build_balance/tilt_balance/play_scroll_unroll/grow_bar）。**页面布局必须先 `page_stack()` 组整页稳定 box，再 `layout_page()` 居中（见下「整页规划」）。**
新文章直接用模板 `scripts/manim_scene_template.py`（cp 到 shipinhao/ 改 VOICE_DUR + 写场景类即可，模板自动向上查找 scripts/）。核心骨架：

```python
import pathlib, sys

def _scripts_dir() -> str:          # 向上查找项目 scripts/（模板已内置，勿删）
    p = pathlib.Path(__file__).resolve().parent
    for _ in range(6):
        cand = p / "scripts"
        if (cand / "manim_helpers.py").exists():
            return str(cand)
        p = p.parent
    raise RuntimeError("找不到 scripts/manim_helpers.py")

sys.path.insert(0, _scripts_dir())
from manim_helpers import *         # config/颜色/t/_card/boxed/fit/type_in/arc_curve/layout_page/page_stack/_Base 全部就位

config.background_color = "#0F1A30"  # 可选：覆盖默认 #16213E
VOICE_DUR = {"S1": 24.28, ...}     # ffprobe 实测（口播为 voice_process.py 输出），场景类所在模块自动读取
TAIL = 2.5                          # 渲染用缓冲（build 时会截掉，只留 0.1s）

class S1(_Base):
    def construct(self):
        ...
        self.pad_to_voice()   # ← 必加，否则场景时长 < 配音时长
```

- **每段一个 Scene 类（S1..SN），`construct` 末尾必须 `self.pad_to_voice()`**
- **动画节奏 = 台词时间轴（硬性）**：写 scenes.py 前先把该段配音稿每句按字数比例切出起止时间（与 build 脚本字幕分配同一逻辑，如 20s 配音讲 5 句，每句约 4s）；每个 `self.play` 对应一句台词，用 `self.at(t)` 排到该句起始节点，动作密度铺满整段。**禁止**把动作全挤前 1/3 然后 `pad_to_voice` 长等——画面静止等语音是「动画和语音速度差距大」的直接根因（FP4 实测：25s 配音只用了 ~8s 动作，后 2/3 僵住）
- **末尾 pad 上限**：`pad_to_voice` 静止等待 ≤ 配音时长 20%（25s 配音最多 pad 5s）；动作应覆盖 ≥80% 配音时长；渲染前自查：最后一个 `self.play` 结束时刻 ≥ 配音时长 80%
- 配色：背景 `#16213E`，主强调黄 `#FFD54A`（与字幕黄一致），青/绿辅助
- **字幕约定（与 build 脚本一致，勿单改）**：黄色、**字号 75**（缩放后 ≈69px，一行约 13 字）、拆句阈值 26（防折 3 行）、**MarginV=210**（品牌条上方，safe_margin 缩放后文字底部距底 ≈236px）、**整行一次出现 + 150ms 快速淡入**（默认 `{\fad(150,80)}`，`--typewriter` 可切回逐字）
- **品牌尾卡（最后一个场景）**：建议列表淡出 → `ImageMobject("avatar-sjai-round.png")`（圆角透明版，`scale_to_fit_width(3.6)`）→ 图下黄色「关注「数解AI」」→ **当期文章标题**（《…》，白/黄加粗，= `weixin.md` frontmatter `title` 一字不差）→「查看公众号文章」引导（绿）→ 下一篇预告（MUTED，可选）

**视频号发布封面（2026-08-13 拍板）**：归档 `<标题>-封面.png` 默认用 **yairouter** 出 1080×1920（`scripts/yairouter_img.py`），不要用 Manim 单帧当发布封面（FFN / 归一化用户否「不要 manim 版封面」）。Manim `Cover` 场景可作结构稿，禁止覆盖正式封面。关键内容仍须落在 **3:4 安全区**（视频号主页从 9:16 居中裁 1080×1440）：像素 y∈[240,1680]，即 frame y∈[-5.33, +5.33]；标题限宽 `frame_width*0.8`，禁止贴边（2026-08-11 事故：manim 封面「位」字被裁）。⚠️ **若 shell / `.env` 找不到 `YAI_API_KEY`，先 `source ~/.bash_env` 再重试**（作者全局密钥文件），不要直接退回 Manim Cover 或报「缺 key」。

## 整页规划（2026-08-16 用户拍板：最高优先级，所有页面必须先规划再摆元素）

> 禁止「第一条放在中间/顶上，其余元素依次向下平铺」的接龙式排布。每次换页都当作**一次完整屏幕的最大输出内容**来做整页 layout。

**两段式流程：**

1. **先算整页 box**：把该页全部元素的**最终稳定状态**组装起来——数字用终值占位（如 `Rectangle` 占位后 `_cnt().move_to(ph)`）、公式用最终公式尺寸、卡片/图形/曲线/概念图全部按完成后尺寸；然后 `page_stack(*mobs, buff=...)` 定页内相对位置。
2. **再放整页**：`layout_page(page)` 把整页 box 放入显示带并垂直居中，**上下边界留白严格相等**。元素位置全部由整页 box 派生，不再逐条 `next_to(head, DOWN)` 从标题往下接。

**矮页自动排版（2026-08-26 用户拍板：1-4 行文字页必须用 `page_auto`，禁止大 buff 撑高）：**

> 多行文字页（标题行 + 1-3 行正文）此前靠 `buff=5.9~6.4` 把行距撑到显示带 80%，导致**两句话各挂上下两端、中间巨大留空**（KDA 00:36 / 01:09 实测，2026-08-26 用户指出）。矮页一律改用 `page_auto(*mobs)`：
> - 超宽行自动按**逗号 / 分号 / 箭头（→）**等语义标点拆成多行（无标点长句按字数硬拆、空格回溯断行、行尾标点不孤行）；
> - 整组高度不足 → 元素等比放大（字号视觉变大，上限 1.5×）；
> - 行距紧凑（0.42）、整组垂直居中、上下留白均分 —— **无中间空洞**；
> - 换页清除/入场动画与全屏页同惯例（逐个 type_in）。

```python
line1 = t("新 token：旧 K、V 不重算，存进 KV 缓存", 44, WHITE, "BOLD")
line2 = t("省了重做旧题，没省掉查完整段历史", 44, YELL, "BOLD")
page = page_auto(line1, line2)          # 自动拆行 + 放大 + 居中
# 内部 = _wrap_text_mob(拆行) → 元素 scale → Group.arrange(DOWN, buff=0.42) → layout_center
```

矮页与全屏模式的选择：**1-4 行纯文字/结论页 → `page_auto`；多元素/图表/卡片页 → `page_stack + layout_page`**。同一场景内可混用。

**显示带与硬性比例（已在 `scripts/manim_helpers.py` 固化）：**

| 常量 | 值 | 含义 |
|---|---|---|
| `PAGE_TOP` | `FH * 0.32` | 显示带上边界（标题下方） |
| `PAGE_BOTTOM` | `-FH * 0.292` | 显示带下边界（距底 ≈400px，字幕上方） |
| `PAGE_BAND` | `PAGE_TOP - PAGE_BOTTOM` | 整页可用高度 |
| `MAX_PAGE_MARGIN` | `0.10` | 上下留白各 ≤ 显示带 10%（2026-08-19 用户拍板，原 30%） |
| `MIN_PAGE_FILL` | `1 - 2×0.10 = 0.80` | 内容高度 ≥ 显示带 80% |

- 内容高度不足 80% → `layout_page()` 直接 `ValueError`。**必须放大元素、增加页内 buff 或补真实视觉内容**，不能用透明占位撑高度（透明占位只用于数字终值定位）。
- 内容高度超过 100% 显示带 → `layout_page()` 等比缩小；正常设计应先删内容/拆页，不依赖缩小。
- **闪烁/强调类装饰不参与整页 box**：`play_red_cross`、`circumscribe`、`indicate`、`breathe`、数字滚动过程都按稳定后的几何计算，不占留白预算。

```python
# 正确：先组装本页全部稳定元素，再整页放版
line = t("把同一道题生成多份答案", 30, WHITE)
chips = VGroup(*[Rectangle(...) for _ in range(8)]).arrange_in_grid(2, 4, buff=0.2)
num_ph = Rectangle(width=2.2, height=0.8, fill_opacity=0, stroke_opacity=0)
page = page_stack(line, chips, num_ph, buff=0.8)
layout_page(page)
# 动画只负责“出现”，不负责改位置：
self.play(type_in(line, run_time=0.9))
self.play(FadeIn(chips, shift=DOWN * 0.05))
num = self.counter_value(0, 64, suffix=" 个", ...).move_to(num_ph)  # 或定位先行版 _cnt

# 错误：从标题往下接龙，页面重心随元素增多漂移
line.next_to(head, DOWN, buff=4.5)
chips.next_to(line, DOWN, buff=0.4)
```

## 布局规范（硬性，违反必须返工）

0. **通用参考**：Manim API 详细用法（mobjects/grouping/positioning/动画/LaTeX/CLI 等）查 `.agents/skills/manimce-best-practices/rules/`。**冲突时以本规范为准**——外部示例默认横屏 16:9（frame 8×4.5），本项目画布是竖屏 `8×14.222`（config 已覆盖，勿照抄外部示例尺寸）
1. **整页规划优先 + VGroup 原子化**：先 `page_stack()` 组页，再 `layout_page()` 放版；组内 `arrange(RIGHT/DOWN/arrange_in_grid, buff=...)`。**禁止散落硬编码绝对坐标**（如 `move_to(UP * 2.2)` 魔法数字）
2. **页内锚点链只表达相对关系**：`next_to(prev, DOWN/UP/RIGHT, buff=...)` 只能用于组内元素互锚（标签↔对应条、箭头两端↔卡片）；整页位置一律交给 `layout_page()`。**禁止 `next_to(head, DOWN, buff=4.x)` 作为页面起点**——那正是“元素挤在上半屏”和留白不等的根因
3. **网格**：≥2 行的重复元素（GPU 块、列表项）用 `arrange_in_grid(rows, cols, buff, cell_alignment=LEFT)`，禁止手算格子宽度
4. **安全区与留白**：整页 box 必须在 `PAGE_TOP..PAGE_BOTTOM` 显示带内，横向 `|x| ≤ config.frame_width/2 - 0.4`；页末内容最低点距底 399~800px（<399 撞两行 75 号字幕，>800 画面空）。**在此基础上，上下留白必须相等且各 ≤ 显示带 10%**（2026-08-19 用户拍板，原 30%；`layout_page` 自动保证并校验）；含 ImageMobject/曲线等 bbox 含透明边的页面，以整页 bbox 为规划依据，抽帧复核可见内容不越安全区
5. **内容占屏**：整页内容高度 ≥ 显示带 80%（`layout_page` 硬校验，2026-08-19 用户拍板收紧，原 40%），多数页 85-95%。短页手段：大字号（单卡页标题字可到 40+、爆点字 56-88）、卡片加高（单卡横幅可到 3.6 高）、间距 buff 1.0-1.9、图表/柱体加大；禁止透明占位撑高度
6. **溢出控制**：长文本/宽图表先 `set_width(config.frame_width * 0.8)` 或 `scale_to_fit_width(...)`，禁止超界截断。Manim Text 实际宽度常比估算宽 20-30%，不要凭字数估算宽度
7. **比例坐标**：确需绝对定位时用画布比例（如 `UP * config.frame_height * 0.3`），保证换分辨率不崩
8. **叠放顺序**：用 `z_index=` 控制，不依赖 add 顺序
9. **框内文字自适应（硬性，事故率最高）**：固定尺寸框内放文字，必须 `txt.set_width(框宽×0.72~0.85)` 限宽——长英文（Transformer/WordPiece/Python）与长中文（9 字以上描述）溢出是高频事故（2026-08-10 BPE 视频 6 处）；统一用 `boxed()` 工具，token 块文字 ≤ 框宽 78%。**嵌套框（`VGroup(Rectangle, VGroup(标题, 副标))`）内文字同样逐一限宽**（2026-08-10 事故：只修了平铺框，嵌套结构漏网）；写完 grep 复查所有 `Rectangle(` 与相邻 `t(` 组合。⚠️ **`set_width` 只缩小不放大**（2026-08-11 事故：Q/K/V/追/猫/qᵢ 等短字符被无条件放大到框宽 78%，字形顶出边框 4 处）——`boxed()`/`fit()` 必须 `if mob.width > limit: mob.set_width(limit)`
10. **VGroup 内元素必须排布**：`VGroup(w, a, b)` 不 arrange 时所有子元素中心重叠（S2 id_card 事故）。箭头自适应：先 `VGroup(两端).arrange(RIGHT, buff)` 定好两端位置，再 `Arrow(左端.get_right(), 右端.get_left())`
11. **动画中间态也是画面**（用户暂停逐帧看）：FadeIn `shift` 位移 ≤0.1；验证抽帧必须覆盖「动画中帧」（每场景 30%/60% 时间点）+「页末帧」（90%），不只抽页末
12. **禁止假占位符**：数据展示不全用「…」块（MUTED 色）或只放真实元素，禁止 [—] 等凑数元素（用户原话「非常丑陋」）
13. **长链路分两行蛇形**：≥5 节点（如 7 步链路）排两行（4+3），行间用黄色折线箭头（`Arrow(行1底部, 行2顶部)`），禁止单行硬塞
14. **弧线方向与遮挡**：`CurvedArrow` 的 `angle` 正负决定弧凸向——start 在右、end 在左时 `angle=-PI/2` 弧向**下**凸，`+PI/2` 向上凸。循环弧放元素**下方**：`CurvedArrow(右端.get_bottom()+DOWN×0.3, 左端.get_bottom()+DOWN×0.3, angle=-PI/2)`，标签在弧下方，后续元素全部 `next_to` 到标签之下；弧线扫过的区域禁止任何元素（会「遮挡」）
15. **标签对齐（硬性，2026-08-11 事故）**：多个标签对应多个元素（如 token 标签↔权重条）时，**逐个 `next_to` 对准对应元素**（`t("token 2").next_to(bars[0], UP)`），禁止整组 arrange 后居中（组中心与条中心不重合）
16. **公式符号禁止 Text 直渲染**（2026-08-11 事故：`√d` 的 √ 与 d 分离不连贯 3 处）：系统无 LaTeX 时用 `sqrt_group()`（模板内置）——**√ 字形自带顶部横线但只到字形右缘**，手绘横线必须从 √ 右缘（`0.48*ws`）**向右延伸**覆盖 d、用**细线**（`d_size/16`）；⚠️ 横线画在 √ 字形上方会叠成粗杠（被用户否）；纯线条画法缺尖角也被否 3 版；**曲线必须配坐标轴**（`Axes` + `axes.plot`，禁止裸 `FunctionGraph` 悬空）；**换页 FadeOut 必须包含本页全部元素**（2026-08-11 事故：S4 页2 加 Axes 后 FadeOut 漏了它，坐标轴残留到页3）
17. **弧线角度用 arctan2 精确计算**（2026-08-11 事故：拍脑袋 angle=0.5 画过头，弧线未连接 q 与 k₁）：`start_angle=arctan2(q_y, q_x)`、`angle=arctan2(k_y, k_x)-start_angle`；⚠️ **`Arc` 定位必须用 `arc_center=` 参数**（`move_to()` 移动的是弧线 bbox 中心而非圆心，会把弧线整体平移错位）
18. **next_to 到非居中父元素后必须 `set_x(0)`**（2026-08-11 事故：rowlab 对齐到 ell 偏移中心 + fit 不缩放 → 右端超界被裁「打分」二字）：fit 过的宽文字 next_to(ell/curve/箭头等 bbox 中心≠0 的元素) 后强制水平居中
19. **否定/纠错视觉（用户拍板 2026-08-11）**：用 `play_red_cross()`（两条粗红线 GrowFromCenter 交叉 + 弹跳，模板内置）盖住被否定的元素，**文字本身用 WHITE**——禁止红色文字 + 单条斜线（红叉已表达否定，文字红色与叉撞色）
20. **方框入场默认拉幕（用户拍板 2026-08-14）**：`boxed()` 卡片 / 列表项 / 信息条用 `play_scroll_unroll(grp)`——框保持全高、宽度从左缘向右摊开，文字在框铺开后再淡入。同组多框必须等宽。禁止用 `FadeIn`/`GrowFromEdge` 替代（后者会连带压扁高度，不是拉幕）。不用拉幕的仅限：单字爆点（Flash/Indicate）、已在场上的红叉对象、封面静帧、成组小徽章一次排开
21. **裸文字默认打字机（用户拍板 2026-08-17）**：所有画面上单独出现的文字（标题/正文/标签）用 `type_in()` 逐字入场，**禁止一次性 FadeIn 整段文字**（用户否过）；节奏放慢：标题 1.1s、正文 0.8-1.0s、标签 0.5s（×1.6 倍速），拉幕 ×1.5 慢速——「文字出现速度不能太快」。保留 FadeIn 的仅：公式 formula、天平 rig/pans、圆形节点、徽章组、logo、✔✗ 标记
22. **闭环弧线箭头不穿圆（2026-08-17 拍板，v7→v8 事故）**：循环流程图用 `arc_curve()`（manim_helpers）——贝塞尔曲线，端点放圆外缘 1.15 倍半径处、控制点沿外法向+切向延伸（曲线全程不穿圆），箭头从终点指向终点圆心、尖端恰好落在圆周上（不插进圆）。**禁用 `CurvedArrow`**（弧线路径会穿进圆，RLHF v7 实测 pg 圆内 3009 像素）。验证：渲染后像素级检查弧线色像素到各圆心距离 ≥ 圆半径（排除文字抗锯齿）。圆形节点用 `cnode()`（彩色描边+半透明填充+限宽文字）
23. **换页 FadeOut 对账含「段内换页」（2026-08-17 S7 事故）**：不止场景切换，**段2→段3 的段内换页也必须带走前一段全部元素**（S7 的 lab「看重事实」段2 起一直残留到 notfixed/shortcuts，与后文叠压 5s；shortcuts 同样未在边界线换页时清除，与 b_lab 叠压）。对账清单：每处 FadeOut 与该页 `play`/`add` 过的 mobject 逐一核对（含 Arrow/Axes/装饰/上页残留）
24. **箭头留缝 + 居中 + 换页带走（2026-08-13 归一化/Transformer）**：箭头与框/轴至少留 0.15 空隙，禁止贴框、贴地、穿过方框；两端连接箭头的中线对准两端中点（竖箭头垂直居中）。换页 `FadeOut` 必须带走本页全部 `Arrow`/`Line`，禁止箭头残留数秒贴在下一页元素上
25. **屏幕小字说明，不改音轨（三片都改过）**：开场 3 秒内加一行 MUTED 小字点明「本片以 XX 模型为例」；后向引用 / 精度补充 / 实验范围用小字停 ≥2s。台词提到公式时画面必须出组装公式（上标锚在对应字母 UR），禁止只剩汉字描述
26. **手绘坐标图（预训练柱状图 4 轮）**：先 `move_to` 定 origin，再挂轴名/刻度/柱；柱与 Y 轴缝 ≥0.4；末柱不贴箭头；趋势线过全部柱顶；数值标签不得与刻度重叠
27. **容器包住子元素；代码框贴合行数并居中；下面有空别挤两行（归一化 02:53/03:26/03:46）**：外框 bbox 必须覆盖全部内框；伪代码框高度贴合行数、水平居中，禁止框下大片留白；同屏两行文字若下方仍有安全区，加大 buff
28. **转折/爆点画面只留关键词（预训练 01:05/02:15）**：提醒只留 ≤2 字 + 一次 Flash（「注意」不是「但注意。」+⚠+Indicate）；短句爆点只留该词并可闪烁（「没崩！」），不要复述整句
29. **卡片默认实心 + 轻微圆角（2026-08-16 GRPO 用户拍板）**：所有文本方框统一走 `_card()`/`boxed()`：实心填充 `CARD_FILL=#2C3F60`（中性石板蓝，默认色），`fill_opacity=1.0`；`RoundedRectangle(corner_radius=0.18)`，禁止普通 `Rectangle` 文本方框。高亮色（黄/青/绿/红）只用于标题、关键词、强调卡和状态条，不与默认卡片底色混淆；`play_scroll_unroll()` 同步改为圆角拉幕
30. **首轮设计必须先过预检器**：在渲染前运行 `python scripts/check_manim_scene.py <shipinhao-dir> --strict`。它会检查 `at()` 时间回退、动作越过下一字幕边界、`pad_to_voice()`、动态槽位/并行 reveal 提示，以及高卡小字。预检器只报错不自动改时间点；修正后再渲染。
31. **动态值先占位后动画**：同一行的静态标签和数字必须先用 `dynamic_slot()` + `stable_row()` 完成最终几何，再把 `counter_value(..., anchor=slot)` 放入槽位。禁止动态元素先在 ORIGIN 出现、随后用 `next_to()` 追赶静态元素。
32. **多项 reveal 同拍**：同一层级的列表/柱/卡片要在一个 `self.play(...)` 或 `self.play_parallel(...)` 中并行；纵向列表先 `page_stack()`，再统一 reveal。连续调用多个会播放的 helper 会触发预检提示，必须明确这是有意的时序还是合并为并行动画。
33. **高卡文字优先换行**：固定框文字统一走 `_card()` 的 `fit_text_in_box()`，按布局后的实际宽高动态增大字号，再在全局 `CARD_TEXT_MAX_FS` 上限内优先换行；多行使用统一 `CARD_TEXT_LINE_SPACING`，不能靠单行极小字体“填满”高框，也不要在场景里硬编码换行/字号补丁。仍放不下时拆卡/拆页。

首轮设计门禁的详细说明和示例见 [`docs/manim-scene-preflight.md`](../../../docs/manim-scene-preflight.md)。
