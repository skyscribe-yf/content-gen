# Manim 场景 writer 公共契约（2026-07-04-ai-memory-crash 视频号）

文章：《为什么AI上下文越长越慢？两道数学硬墙一次讲透》（DeepSeek 技术解密系列第一篇）
规格：竖屏 1080×1920（frame 8×14.2222）· 口播配音 · 烧录字幕 · 目标 5-6 分钟

## 产出要求

- 文件：`content/2026-07-04-ai-memory-crash/shipinhao/scenes_parts/S{n}.py`
- **只写 `class S{n}(_Base):` 完整定义**（construct 方法）。不写模块头部（import/config/VOICE_DUR/TAIL 由主 agent 合并时统一加）
- 局部 helper 命名必须带场景前缀（如 `S2_header`），禁止与其它场景重名
- 自验：`python3 -c "import ast; ast.parse(open('content/2026-07-04-ai-memory-crash/shipinhao/scenes_parts/S{n}.py').read())"` 通过即交付，**不渲染**

## helpers API（from manim_helpers import * 已提供）

- `t(text, size=34, color=WHITE, weight="NORMAL")` — 裸文字
- `_card(label, w, h, border, txt_fill, fs=28, fill=CARD_FILL, weight="NORMAL")` — 统一卡片（实心 CARD_FILL + 圆角 0.18 + 文字限宽 76% 只缩不放）
- `boxed(label, w, h, color, fs=28, fill=0.12, wc=None, weight="NORMAL")` — 兼容旧调用，返回 _card 风格
- `boxrow(labels, w, h, colors, fs=28, fill=CARD_FILL, left=True, gap=0.55, weight="NORMAL")` — 竖排卡片组
- `fit(mob, frac=0.85)` — 宽内容守卫（只缩小不放大）
- `sup(base, sup_str, size=30, sup_size=17, ...)` / `sub(base, sub_str, ...)` — 上下标
- `type_in(mob, run_time=0.6)` — 逐字打字入场
- `cnode(lab, col, radius=0.95, fs=24)` — 圆形节点
- `layout_page(block)` / `page_stack(*mobs, buff=0.55)` — 整页规划（见下）
- `_Base` 方法：
  - `at(t)` — 推进到配音时间轴绝对时刻（动画挂台词节点）
  - `pad_to_voice()` — construct 末尾必加
  - `footer(text="数解AI · 大模型原理")` — 底部品牌条（本片用默认文案）
  - `bg()` — 背景
  - `play_red_cross(target, run_time=0.65)` — 动态大红叉（否定）
  - `play_mark(label, target, color=GREEN, ...)` — ✔ 标记
  - `play_scroll_unroll(grp, run_time=1.5)` — 卡片拉幕入场（×1.5 慢速）
  - `grow_bar(rect, tracker, target, run_time=0.7)` — 柱状生长
  - `counter_value(start, end, suffix="", decimals=0, size=64, color=YELL, run_time=0.9, anchor=None)` — 数字滚动（anchor=占位 mobject 时自动定位）
  - `transition_out(*mobs, run_time=0.6)` — 场景转场（全片统一用，传全部可见元素含 head/footer）
  - `camera_zoom_to(target=None, scale=0.6, run_time=1.0)` — 镜头推拉（必须成对，末帧拉回）
  - `morph_to(source, target, run_time=1.0, replace=True)` — 形变
  - `trace_dot(path, color=YELL, radius=0.09, ...)` — 轨迹追踪点（dot 换页必须 FadeOut 带走）
  - `emphasize(target, mode="indicate", color=YELL, ...)` — 关键词强调
  - `breathe(target, scale=1.03, run_time=1.2, loops=2)` — 呼吸微动（≤3%）

## 样式常数

- 颜色：`YELL=#FFD54A`（主强调，与字幕黄一致）/ `CYAN=#5FC4E8` / `GREEN=#7ED7A0` / `RED=#FF7B72` / `MUTED=#9AA7BD` / `WHITE=#F2F5FA` / `CARD_FILL=#2C3F60`（卡片默认实心）/ `CARD_FILL2=#223450` / `CARD_BORDER=#5C769D` / `TXT_HL=#8FB4E6`
- 背景 `#16213E`；字号体系：head 36-42、正文 26-32、强调 32-44、爆点 56-88
- 概念图：`ImageMobject("img/<name>-round.png")`，`scale_to_fit_width(≤5.5)`，FadeIn 入场（shift≤0.1），图为主 + 1-2 行标注

## 布局规范（硬性）

1. **整页规划**：每页先组装全部元素的最终稳定状态 → `page_stack(*mobs, buff=...)` → `layout_page(page)` 垂直居中。禁止 `next_to(head, DOWN)` 接龙式排布
2. **留白（2026-08-19 用户拍板）**：上下留白各 ≤ 显示带 **10%**，内容高度 ≥ 显示带 **80%**（layout_page 硬校验，不足 ValueError → 放大元素/加大 buff）
3. 安全区：横向 `|x| ≤ 3.6`；内容最低点距底 399-800px（优先贴近 399-600px）
4. 入场：裸文字 `type_in`（标题 1.1s、正文 0.8-1.0s、标签 0.5s）；卡片 `play_scroll_unroll`；FadeIn 仅限：公式/图/圆节点/徽章组/✔✗/logo
5. **FadeOut 对账**：换页（含段内换页）必须带走本页全部元素（含箭头/Axes/装饰/概念图/动态数字/红叉），禁止残留
6. 数字台词必配动效（counter_value/grow_bar/Create 轨迹），禁止纯文字
7. 否定用 `play_red_cross` + 白字（禁红字）；爆点只留关键词 + 一次强调
8. 卡片统一 `_card`/`boxed`（实心圆角），禁裸 Rectangle 文本框
9. 动画节奏：`at(t)` 必须锚契约包锚点表（禁止预估）；动作覆盖 ≥80% 配音时长；construct 末尾 `pad_to_voice()`
10. 场景末尾 `transition_out(head, footer_mob, 全部可见元素)` 统一转场（footer 先 `f = self.footer()` 存引用再传）
11. 数字对比先旧后新：先出旧值（淡化标签），再 counter 滚动到新值

## 风格参考（RLVR 篇模式，可仿写带前缀）

```python
def S2_header(text: str):
    return fit(t(text, 31, YELL, "BOLD"), 0.86).to_edge(UP, buff=1.12)

def S2_fit_text(text, size=30, color=WHITE, weight="NORMAL"):
    return fit(t(text, size, color, weight), 0.84)

def S2_row(*mobs, buff=0.28):
    return Group(*mobs).arrange(RIGHT, buff=buff)

def S2_col(*mobs, buff=0.28, aligned_edge=ORIGIN):
    return Group(*mobs).arrange(DOWN, buff=buff, aligned_edge=aligned_edge)

def S2_page(*mobs, buff=0.55):
    page = page_stack(*mobs, buff=buff)
    layout_page(page)
    return page

def S2_placeholder(label, size, color):
    mob = t(label, size, color, "BOLD"); mob.set_opacity(0.0); return mob

def S2_clear(scene, page, *extras, run_time=0.34):
    # 按叶子交集反查 Scene 顶层组，完整带走同一批对象（RLVR 同款）
    targets = [page, *extras]
    target_ids = set()
    for mob in targets:
        target_ids.add(id(mob))
        target_ids.update(id(leaf) for leaf in mob.submobjects or [])
    roots = []
    for root in list(scene.mobjects):
        root_ids = {id(root)}
        root_ids.update(id(leaf) for leaf in root.submobjects or [])
        if root_ids & target_ids:
            roots.append(root)
    if roots:
        scene.play(FadeOut(*roots), run_time=run_time)
        scene.remove(*roots)
```

## 每场景 storyboard 行

- **S1 开场钩子**：agent 修 bug 循环动图（读代码→跑测试→改文件）；进度条 200 步到顶崩掉；GLM-5.1 得分条 1.0 vs GLM-5.2 得分条 13.0（counter_value，+1200% 爆点）；「失忆」疑问 → 两道墙剪影。无概念图
- **S2 墙一握手**：会议室概念图 `img/handshake-round.png`；10 人全连接图 45 条线（Create）→ 100 人密集连线爆点（点数 10→100、连线数 45→4950 counter_value）；「翻 N 倍 → 翻 N² 倍」标签；悬念结尾
- **S3 墙二笔记**：笔记山概念图 `img/notebooks-round.png`；KV cache 公式条 T×d×L×2；5 TB vs H100 80 GB 对比条（grow_bar，60 倍爆点）；两道墙叠压动画；「数学上跑不动」定格
- **S4 实测**：延迟增长曲线脚本画（1K→2K→4K 实测点 + 抛物线 Create，counter_value 0.10→0.38→1.53s）；32K 崩溃爆点：屏幕裂开/黑屏特效；「不是理论，是物理定律」白字定格 + 红叉否定「翻不过去？」。无概念图
- **S5 第一招 DSA**：Indexer 挑人概念图 `img/indexer-round.png`；全连接 → 漏斗筛选 → 只连 2048 个（结构脚本画：T 个点 → 漏斗 → k 个点）；「陷阱：Indexer 自己也是 O(T²)」红叉爆点卡
- **S6 第二招 IndexShare**：78 层 Transformer 堆叠脚本画（78 个小方块）→ 21 层点亮跑 Indexer、57 层复用（counter_value 78→21）；跨层相似度 >0.8 标签条；2.9× 收益 counter_value 爆点；悬念：存储那堵墙？无概念图
- **S7 第三招 MLA**：维度压缩脚本画：6144 宽条 → 512 窄条（morph，>10× 标签）；KV 总量 5 TB → 78 GB 对比（grow_bar 从爆表缩到 H100 边界）；三招协同三卡（DSA / IndexShare / MLA 各拆一道墙，CheckMark 依次点亮）；「缺一不可」强调。无概念图
- **S8 总结 + 尾卡**：翻墙概念图 `img/wall-jump-round.png`；三招回顾链（DSA→IndexShare→MLA 依次亮）；1.0 → 13.0 +1200% 回扣（counter_value）；尾卡：avatar 圆角图 + 黄色「关注「数解AI」」+ 当期文章标题《为什么AI上下文越长越慢？两道数学硬墙一次讲透》+「查看公众号文章」绿色引导 + 下一篇预告（推测解码）+ 开放式问题
