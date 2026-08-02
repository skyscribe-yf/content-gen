#!/usr/bin/env bash
# publish.sh — 一键发布公众号
# 流程: markdown → mdnice(MathJax→SVG) 渲染公式 → baoyu 发布(含图片上传+主题)
#
# 注：已禁用旧的 unicode-preprocess.py 路径。它能力有限（不支持 \text/\mathcal/
#     \in/\otimes/\underbrace/复合下标），会砍坏复杂 LaTeX。公式统一交给 mdnice
#     的 MathJax 引擎渲染为内联 SVG，与 docs/math-latex.md 规定一致。
#
# 用法:
#   bash scripts/publish.sh content/2026-07-03-梯度下降/weixin.md
#   bash scripts/publish.sh content/2026-07-03-梯度下降/weixin.md --cover path/to/cover.png

set -euo pipefail

# ── 项目根目录 ──
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ── 参数 ──
MD_FILE=""
COVER=""
THEME="grace"
COLOR="blue"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cover)  COVER="$2"; shift 2 ;;
    --theme)  THEME="$2"; shift 2 ;;
    --color)  COLOR="$2"; shift 2 ;;
    *)        MD_FILE="$1"; shift ;;
  esac
done

if [[ -z "$MD_FILE" ]]; then
  echo "用法: bash scripts/publish.sh <markdown文件> [--cover 封面图] [--theme 主题] [--color 颜色]"
  exit 1
fi

if [[ ! -f "$MD_FILE" ]]; then
  echo "❌ 文件不存在: $MD_FILE"
  exit 1
fi

echo "═══════════════════════════════════════"
echo "  数解AI 公众号一键发布"
echo "═════════════════════════"
echo ""

# ── Step 1: 确定封面图 ──
if [[ -z "$COVER" ]]; then
  ARTICLE_DIR="$(dirname "$MD_FILE")"
  if [[ -f "${ARTICLE_DIR}/imgs/cover.png" ]]; then
    COVER="${ARTICLE_DIR}/imgs/cover.png"
  elif [[ -f "$ROOT/content/gradient-series-ai/01-blindfold-descent.png" ]]; then
    COVER="$ROOT/content/gradient-series-ai/01-blindfold-descent.png"
  fi
fi

echo "🖼️  封面: ${COVER:-无（baoyu 会自动处理）}"
echo ""

# ── Step 2: baoyu 发布到微信草稿箱（mdnice 渲染 LaTeX→SVG） ──
echo "📤 Step 2: 发布到微信草稿箱 (baoyu + mdnice + remote-api)..."

set -a
source <(grep -v '^#' .baoyu-skills/.env 2>/dev/null || true)
set +a

PUBLISH_CMD=(
  bun .agents/skills/baoyu-post-to-wechat/scripts/wechat-api.ts
  "$MD_FILE"
  --theme "$THEME"
  --color "$COLOR"
  --remote
  --remote-host vps
  --remote-user root
)

if [[ -n "$COVER" ]]; then
  PUBLISH_CMD+=(--cover "$COVER")
fi

"${PUBLISH_CMD[@]}"

echo ""
echo "✅ 完成！去 https://mp.weixin.qq.com → 草稿箱 预览并发布"