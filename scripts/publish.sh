#!/usr/bin/env bash
# publish.sh — 一键发布公众号
# 流程: markdown → Unicode 公式渲染 → baoyu 发布(含图片上传+主题) → 清理
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
echo "═══════════════════════════════════════"
echo ""

# ── Step 1: Unicode 渲染公式 ──
echo "📐 Step 1: 渲染公式 (Unicode + 样式)..."
UNICODE_FILE="${MD_FILE%.md}.unicode.md"
python3 scripts/unicode-preprocess.py "$MD_FILE"

if [[ ! -f "$UNICODE_FILE" ]]; then
  echo "❌ Unicode 预处理失败"
  exit 1
fi
echo ""

# ── Step 2: 确定封面图 ──
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

# ── Step 3: baoyu 发布到微信草稿箱 ──
echo "📤 Step 2: 发布到微信草稿箱 (baoyu + remote-api)..."

set -a
source <(grep -v '^#' .baoyu-skills/.env 2>/dev/null || true)
set +a

PUBLISH_CMD=(
  bun .agents/skills/baoyu-post-to-wechat/scripts/wechat-api.ts
  "$UNICODE_FILE"
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

# ── Step 4: 清理临时文件 ──
echo ""
echo "🧹 清理临时文件..."
rm -f "$UNICODE_FILE"

echo ""
echo "✅ 完成！去 https://mp.weixin.qq.com → 草稿箱 预览并发布"
