# 多 agent 并行写 scenes.py（≥6 场景新写时推荐）

单 agent 串行写 9 个场景的痛点（PPO 2026-08-15 实测）：布局估算全靠脑内推导、FadeOut 对账/占屏/锚点错位靠 -ql 渲染+抽帧迭代、每轮修复等 20 分钟 QA 才反馈。多 agent 把「写」并行化 + 独立 review 兜底，墙钟时间下降、上下文聚焦出错率下降、review 视角独立不再自己写自己查。

**收益不在「多开 agent」本身，在「契约 + 循环」**：并行不提升单点质量（同模型同水平），提升的是 ①墙钟时间 ②上下文聚焦（writer 只背自己场景）③独立 review。一致性风险（视觉密度/at 锚点/FadeOut 对账漂移）只能靠统一契约 + review 循环兜底。

## 何时用 / 不用

- ✅ 用：新文章从零写 **≥6 场景**、场景独立性强（类之间零依赖、只经 helpers 通信）
- ❌ 不用：改 1-2 个既有场景、小修——单 agent 更快，编排成本反而亏
- ⚠️ 场景间有强耦合（如 S2 复用 S1 的变量）时不宜拆分，先重构解耦或单 agent

## 硬约束（用户拍板 2026-08-15）

- **最多 4 个并行 writer**（机器 16 核，更多会互相拖慢 + subagent 并发上限）
- **writer 只写代码，不渲染**——渲染留到主 agent 合并后统一做（避免 9 份各自渲染的 media 冲突 + 重复劳动）
- **review-fix 循环里 reviewer 只读不改**（保持独立），修复按「全局/局部」分类分发

## 5 阶段流程

### 阶段 0：主 agent 提取契约包（串行，~5 分钟）

为每个场景准备一份**契约包**，是 writer 的唯一输入（writer 不读原 json / 不读全片 storyboard，从源头消灭锚点漂移）：

1. **时间锚点表**：从 `tts/sentence-boundaries.json` 提取该场景的句级边界，直接塞进 task：
   ```bash
   python3 -c "
   import json
   b=json.load(open('content/<日期>-<主题>/shipinhao/tts/sentence-boundaries.json'))
   s=next(x for x in b['segments'] if x['id']=='s{n}')
   print(f\"VOICE_DUR_{s['id'].upper()}={s['duration']:.3f}\")
   for c in s['clips']: print(f\"  {c['start']:6.2f} - {c['end']:6.2f}  {c['text']}\")
   "
   ```
2. **该场景的 storyboard 行**（从 storyboard.md 取）
3. **helpers API 摘要**：`t/_card/boxed/boxrow/fit/sup/sub/type_in/cnode/arc_curve/_Base 全家桶` + `counter_value/transition_out`（见 [vividness.md](vividness.md)）的签名与用法
4. **样式常数**：配色（YELL/CYAN/GREEN/RED/MUTED/WHITE）、字号体系（head 36-42、正文 26-32、强调 32-44）、卡片（_card/boxed）、安全区（[step5-scenes.md](step5-scenes.md) 规范 4：内容最低点距底 399-800px、|x|≤3.6、顶避 1.5）、入场（type_in/scroll_unroll/FadeIn 白名单）、FadeOut 对账（含段内换页）、**先声音后动画门禁**（at() 必须锚句边界，禁止预估）
5. **参考样例片段**：从最近一篇同系列文章的 scenes.py 挑 1-2 段同类型场景作风格参考（如 RLHF 的天平/闭环弧线卡参考）

### 阶段 1：并行 writer ×≤4（只写不渲染）

每个 writer 产出 `scenes_parts/S{n}.py`，**只含 `class S{n}(_Base)` 类体**（不写模块头部 import / VOICE_DUR / config——这些主 agent 合并时统一加，避免 9 份重复定义冲突）。

writer 任务要点（写进 task）：
- 只写 `class S{n}(_Base):` 的 `construct` 方法（可含场景内局部 helper，但禁止改全局/动 helpers）
- `at(t)` 必须用契约包里的句边界，禁止预估；动作覆盖 ≥80% 配音时长
- `construct` 末尾必须 `self.pad_to_voice()`
- 入场/布局/FadeOut 对账/安全区严格按契约包（step5-scenes.md 整页规划 + 0-28 + qa-checklist A 组）；每页必须 `page_stack()` 组稳定 box → `layout_page()`，禁止 `next_to(head, DOWN)` 接龙
- **自验只做语法**，不渲染：`python3 -c "import ast; ast.parse(open('scenes_parts/S{n}.py').read())"` 通过即交付
- 产出路径：`content/<日期>-<主题>/shipinhao/scenes_parts/S{n}.py`

并行调度（pi-subagents `runs.all`，分批 4）：
```javascript
// workflowScript 示例：9 场景分 3 批，每批 4 并行
const scenes = ["S1","S2","S3","S4","S5","S6","S7","S8","S9"];
const batches = []; for (let i=0; i<scenes.length; i+=4) batches.push(scenes.slice(i,i+4));
const outputs = {};
for (const batch of batches) {
  const res = await runs.all(batch.map(k => ({
    key: k, agent: "worker",
    task: <契约包模板填入 k 对应的锚点表/storyboard 行>,
  })));
  Object.assign(outputs, res);  // 串行批次间，批内并行
}
return outputs;
```
> worker agent 须先 `subagent({action:"list"})` 确认可执行；writer 用通用 worker 即可（任务自含契约，不依赖 manim 专长 agent）。

### 阶段 2：主 agent 合并 + 全量 -ql 渲染 + 抽帧（串行）

1. 合并：生成 `scenes.py` = 头部（`_scripts_dir` + `from manim_helpers import *` + `config` + `VOICE_DUR` 9 项 + `TAIL`）+ 依次读入 9 个 `scenes_parts/S{n}.py` 的类体
2. 语法 + import 验证：`python3 -c "import ast; ast.parse(open('scenes.py').read())"`，再 import 确认 9 个 class 存在、无 NameError
3. 全量 -ql 渲染：`python3 -m manim render -ql --disable_caching scenes.py S1 S2 ... S9`
4. 抽帧：每场景 30/60/90% 三档 + 70% 边缘扫描帧（[step6-render.md](step6-render.md)）

### 阶段 3：派 manim-qa-reviewer（review-only）

派 `.pi/agents/manim-qa-reviewer` 对 -ql 渲染产物 + scenes.py 做 A 组检查 + **跨场景一致性检查**（见下方 A17）。reviewer **不改文件**，输出结构化问题清单：`文件:行号 + 问题 + 修复建议 + 全局/局部标记`。

### 阶段 4：修复循环（上限 2 轮，防震荡）

主 agent 拿到问题清单后**先分类**：

- **全局问题**（helpers 缺功能 / 规范理解偏差 / 多场景同款 bug）→ 主 agent 统一修（改 helpers 或统一指令），避免 9 个 writer 各修各的重复劳动
- **局部问题**（某场景独有）→ 按场景分发回**对应 writer** 修（writer 上下文还在、各改各的无文件冲突），并行 ≤4
- 修完 → 主 agent 合并 → 重渲染 -ql → 重派 reviewer
- **终止**：全 PASS 进阶段 5；**2 轮后仍有 FAIL** → 主 agent 接管收尾（不再甩给 writer，防 review-writer 互相甩锅震荡）

### 阶段 5：-qm 渲染 → QA B → build

同单 agent 流程（[step6-render.md](step6-render.md) / [step7-build.md](step7-build.md) / [step8-verify.md](step8-verify.md)）：crf14 重编码 → `manim_video_build.py` → QA B 组 → 归档。

## 跨场景一致性检查（reviewer 新增 A17）

多 agent 模式专属，单 agent 模式可跳过：

| 检查点 | 判据 |
|---|---|
| 字号体系统一 | head 全片一致（±2）、正文一致、强调一致 |
| 间距密度统一 | 同类页面（列表/对比/单元素）buff 量级一致，无某场景异常稀疏/密集 |
| 配色一致 | 主强调黄/辅助青绿/否定红/弱化 MUTED 全片同义同色 |
| 入场方式统一 | 卡片一律 scroll_unroll、裸文字一律 type_in、无某场景混用 FadeIn 整段文字 |
| 锚点精度统一 | 抽查 3 场景的 at() 是否都能从契约包锚点表回溯（非拍脑袋） |
| 尾卡/转场一致 | 最后场景尾卡四要素齐全；若用 transition_out 则全片统一用、且都传全部元素 |

## 防漂移机制

1. **契约包是 writer 唯一输入**——不读原 json / 全片 storyboard，锚点表预提取消灭拍脑袋
2. **独立文件产出**——`scenes_parts/S{n}.py` 类之间零依赖，合并无冲突
3. **reviewer 只读**——修复权在主 agent / writer，避免 reviewer 既当裁判又当运动员
4. **全局/局部分类**——全局问题统一修，局部问题分发修，避免重复劳动 + 风格漂移
5. **2 轮上限**——防震荡，超限主 agent 兜底

## 适用边界再强调

- 场景数 < 6：单 agent 更划算（编排成本 > 并行收益）
- 场景强耦合（变量跨场景引用）：先解耦或单 agent
- 改既有 scenes.py 的局部：单 agent
- 环境刚升级 manim（如 0.20→0.21）：先单场景冒烟确认兼容再大规模并行（见 [pitfalls.md](pitfalls.md) manim 版本坑）