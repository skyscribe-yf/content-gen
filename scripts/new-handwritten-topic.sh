#!/bin/bash
# 新建「手写稿直出」话题脚手架（2026-11-14）
#
# 与 new-raw-topic.sh（素材直出）的区别：素材即全文原稿，由作者在 VS Code
# 手写完成；AI 建稿 + 开 VS Code 后静默等作者说「好了」，再跑
# .agents/skills/handwritten-draft-to-wechat/SKILL.md 的管线。
#
# 用法: ./scripts/new-handwritten-topic.sh "话题slug"

TOPIC="$1"
DATE=$(date +%Y-%m-%d)
DIR="content/${DATE}-${TOPIC}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "$TOPIC" ] || [ "$TOPIC" = "-h" ] || [ "$TOPIC" = "--help" ]; then
    echo "用法: ./scripts/new-handwritten-topic.sh \"话题slug\""
    echo "例:   ./scripts/new-handwritten-topic.sh \"梯度下降-蒙着眼下山\""
    exit 1
fi

if [ -d "$DIR" ]; then
    echo "❌ 目录已存在: $DIR"
    exit 1
fi

mkdir -p "$DIR"

cat > "${DIR}/draft.md" << 'TEMPLATE'
---
title: ""          # 想自己起标题就写这里；空着则 AI 润色时按标题规则起（≤22 字、关键词前置）
author: "数解AI"
date: __DATE__
type: ""           # 原理篇 / 工程篇 / 观察篇 / 教程篇（空着 AI 补）
series: ""         # 所属合集；没有就空着
digest: ""         # 摘要（空着 AI 补）
keywords: ""       # 关键词，逗号分隔（空着 AI 补）
cover: ""
---

<!--
══════════ 手写稿约定（本注释块不进稿，AI 存草稿前会删掉）══════════
1. 全文手写，不用管结构。你的原话逐字保留，只修明显错别字。
   AI 默认不加任何段落——你写得顺的时候，桥接/过渡/总结段都属于
   画蛇添足，禁写。AI 只补：你没写的标题、公式和图前后的一句
   凡人话解释、项目规矩要的尾部（热门文章 + 话题标签）。
2. 凡是让 AI 补的地方都标「待补充」，冒号后说明补什么；标点随意
   （待补充 / 待补充： / 待补充， 都认），行内写或包进 HTML 注释都行。
   常见五种：
   - 公式：待补充：kaiming 初始化的公式
   - 配图：待补充：本节的概念图，图样是……；也可写【图样：一句话描述】
   - 表格：待补充：原报告 Table 1（AI 脚本重画，禁截图）
   - 前文索引：待补充：插入低秩/流形那两篇的公众号链接
     （没标 AI 也会按主题自动配 2-4 篇旧文内链，只放公众号 URL）
   - 事实/数据：待补充一个具体数字，如 DeepSeek v4.1 的权重数量
   AI 逐项处理、一个不落；补不了的列清单找你，不静默丢弃。
3. 承重数字（价格/版本号/参数规模/论文结论）尽量标出处；AI 先扫你的
   Obsidian 笔记索引找相关素材，再联网核实；查出错列清单等你裁决，
   不擅自改你的论断。
4. 篇幅默认约 2000 字。想写多长写多长——跟 AI 说一句「不要管文章长度」
   即豁免，AI 禁拿默认口径砍你的稿。
5. 写完跟 AI 说「好了」。AI 先校验稿件非空，然后跑全程：
   润色 → 查事实（Obsidian 素材 + 联网）→ 补公式 → 配图 → 内链 →
   事实查验（你裁决）→ 质量审查 → 封面 → 打开 VS Code 等你终审 →
   存草稿箱。中途任何时刻说「继续」，AI 就连跑剩余步骤，
   不再逐阶段停下来汇报。
-->

（从这里开始写。正文第一段直接写钩子，别用标题开场。）
TEMPLATE

sed -i "s/__DATE__/${DATE}/" "${DIR}/draft.md"

# 登记排期台账（建稿即登记，防发布时漏登——2026-11-14 GB300 篇教训）
SLUG="$(basename "$DIR")"
python3 "$ROOT/scripts/schedule.py" add "$SLUG" --title "$TOPIC" --status drafting \
    && echo "📋 台账已登记: ${SLUG} [drafting]" \
    || echo "⚠️ 台账登记失败，请手动: python3 scripts/schedule.py add ${SLUG} --title <标题> --status drafting"

echo "✅ 已创建手写稿: ${DIR}/draft.md"
echo ""
echo "📝 正在打开 VS Code（预览随文件自动弹出）……"

# 开 content-gen 文件夹工作区并定位 draft.md（与 precheck_and_open.sh 同款三段式：
# ① 开文件夹+目标文件；② 等窗口就绪后切到跳板制造编辑器切换事件；③ 切回目标文件
# 触发 MPE 自动预览——直接打开时若文件已是激活标签则无切换事件、预览不弹）。
SWITCH_FILE="$ROOT/AGENTS.md"   # 跳板：非目标 markdown，用来制造一次编辑器切换
code "$ROOT" "${DIR}/draft.md" || { echo "⚠️ 'code' 命令失败，请手动用 VS Code 打开: ${DIR}/draft.md"; exit 1; }
sleep 5                            # 等窗口就绪 + MPE 激活（冷启动约 +2s）
code "$ROOT" "$SWITCH_FILE" 2>/dev/null || true   # 切到跳板
sleep 1
code "$ROOT" "${DIR}/draft.md" 2>/dev/null || true # 切回 draft.md → 切换事件 → 自动预览

cat <<EOF

📝 VS Code 已打开 content-gen 文件夹并定位: ${DIR}/draft.md
   Markdown Preview Enhanced 预览应已自动弹出（.vscode/settings.json 开关；
   没弹的话焦点在编辑器里按 Ctrl+Shift+V）。
   按 draft.md 头部注释块的约定手写全文，写完告诉 AI：「好了」。
EOF
