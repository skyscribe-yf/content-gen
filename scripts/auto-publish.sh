#!/bin/bash
# 用法：bash scripts/auto-publish.sh content/2026-07-01-主题名/weixin.md
# 从 md 文件头部的 YAML 元数据自动读取标题、摘要，发布到微信草稿箱

MD_FILE="$1"
if [ -z "$MD_FILE" ]; then
  echo "用法: bash scripts/auto-publish.sh path/to/weixin.md"
  exit 1
fi

# 从 YAML 头部提取元数据
TITLE=$(sed -n '/^title: /p' "$MD_FILE" | head -1 | sed 's/^title: "//;s/"$//')
DIGEST=$(sed -n '/^digest: /p' "$MD_FILE" | head -1 | sed 's/^digest: "//;s/"$//')

echo "→ 发布: $TITLE"
npx wechat-official-publisher publish "$MD_FILE" \
  --title "$TITLE" \
  --digest "$DIGEST" \
  --author "数解AI" \
  --draft
