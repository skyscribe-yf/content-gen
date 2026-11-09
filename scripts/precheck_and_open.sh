#!/usr/bin/env bash
# precheck_and_open.sh — 作者编辑门禁（2026-11-08 作者口径）
#
# 流程：机器质检 → 用 VS Code 打开 weixin.md 等作者改 → 作者改完后
#       AI 复跑本脚本（--no-open 只复检）→ 通过才存公众号草稿箱。
#
# 用法:
#   bash scripts/precheck_and_open.sh content/<日期>-<slug>          # 质检 + 打开 VS Code
#   bash scripts/precheck_and_open.sh content/<日期>-<slug> --skip-voice # 第一轮质检：不管原声
#   bash scripts/precheck_and_open.sh content/<日期>-<slug> --no-open # 只复检（作者改完后）
#   bash scripts/precheck_and_open.sh content/<日期>-<slug> --no-open --published # 发布后回拉模式
#   bash scripts/precheck_and_open.sh content/<日期>-<slug>/weixin.md # 也可直接给文件
#
# 质检两轮口径（2026-11-07 作者定）：第一轮 --skip-voice（作者正在 VS Code 填原声占位符）；
# 终检 --no-open 不带 --skip-voice（原声 ≥5 逐字在场 + 占位符清零才准存草稿箱）。
#
# 质检脚本二轨（2026-11-07 通用化）：
#   新篇（目录有 quality_check.json）→ scripts/quality_check.py（通用版 + 每篇配置）
#   旧篇（目录有本地副本）          → 沿用本地副本（历史文章冻结行为）
#   两者皆无                        → 通用版降级（只跑通用门禁，提示跳过定制项）
#
# 退出码非 0 = 质检未过：修好或作者明确拍板豁免后才允许存草稿箱。
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARG="${1:?用法: bash scripts/precheck_and_open.sh <文章目录|weixin.md> [--no-open] [--published]}"
NO_OPEN=0
PUBLISHED=0
SKIP_VOICE=0
for a in "$@"; do
  [[ "$a" == "--no-open" ]] && NO_OPEN=1
  [[ "$a" == "--published" ]] && PUBLISHED=1
  [[ "$a" == "--skip-voice" ]] && SKIP_VOICE=1
done

if [[ -d "$ARG" ]]; then DIR="${ARG%/}"; MD="$DIR/weixin.md"; else DIR="$(dirname "$ARG")"; MD="$ARG"; fi
[[ -f "$MD" ]] || { echo "❌ 找不到 $MD"; exit 1; }
DIR="$(cd "$DIR" && pwd)"; MD="$DIR/$(basename "$MD")"
cd "$DIR"
rc=0
PUB_FLAG=""
[[ $PUBLISHED -eq 1 ]] && PUB_FLAG="--published"
[[ $SKIP_VOICE -eq 1 ]] && PUB_FLAG="$PUB_FLAG --skip-voice"

echo "════════ 机器质检：$DIR ════════"
if [[ -f "$DIR/quality_check.json" ]]; then
  python3 "$ROOT/scripts/quality_check.py" "$DIR" $PUB_FLAG || rc=1
elif [[ -f quality_check.py ]]; then
  python3 quality_check.py $PUB_FLAG || rc=1
else
  python3 "$ROOT/scripts/quality_check.py" "$DIR" $PUB_FLAG || rc=1
fi
if [[ -f 00-cover.png && ! -f "$DIR/quality_check.json" ]]; then
  # 新篇的封面门禁已由通用 quality_check.py 内嵌执行；旧篇本地副本不一定带，补跑一次
  echo "── 封面叠字核验 ──"
  python3 "$ROOT/scripts/check_cover.py" "$DIR" || rc=1
fi
echo "── 微信链接溯源 ──"
python3 "$ROOT/scripts/check_wechat_links.py" "$MD" || rc=1
echo "════════════════════════════════"

if [[ $rc -ne 0 ]]; then
  echo "⛔ 质检未过（见上）。修好或作者拍板豁免后再继续；未过不得存草稿箱。"
  exit 1
fi
echo "✅ 机器质检全部通过"

if [[ $NO_OPEN -eq 1 ]]; then
  echo "（--no-open 复检模式：未打开 VS Code）"
  exit 0
fi

# 开 content-gen 文件夹工作区（.vscode/settings.json 的 MPE 自动预览开关才生效）。
# 关键事实（2026-11-07 实测）：① code 多路径时只有首个文件会被激活，故单独传 weixin.md；
# ② MPE 自动预览只挂 onDidChangeActiveTextEditor，目标文件若已是激活标签则无事件；
# ③ 冷启动第二次 IPC 在窗口就绪前会被吞，故就绪前只发一次、就绪后再补切换。
SWITCH_FILE="$ROOT/AGENTS.md"   # 跳板：非目标 markdown，用来制造一次编辑器切换
code "$ROOT" "$MD" || { echo "⚠️ 'code' 命令失败，请手动用 VS Code 打开: $MD"; exit 1; }
sleep 5                            # 等窗口就绪 + MPE 激活（冷启动约 +2s）
code "$ROOT" "$SWITCH_FILE" 2>/dev/null || true   # 切到跳板
sleep 1
code "$ROOT" "$MD" 2>/dev/null || true            # 切回 weixin.md → 切换事件 → 自动预览
cat <<EOF

📝 VS Code 已打开 content-gen 文件夹并定位: $MD
   Markdown Preview Enhanced 预览应已自动弹出（.vscode/settings.json 开关；
   没弹的话焦点在编辑器里按 Ctrl+Shift+V）。
   作者直接在 VS Code 里改；改完回复「改好了」，
   AI 复跑: bash scripts/precheck_and_open.sh $DIR --no-open
   通过后才走 baoyu-post-to-wechat 存草稿箱（grace + blue）。
EOF
