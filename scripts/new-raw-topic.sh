#!/bin/bash
# 新建「素材直出」话题脚手架
# 用法: ./scripts/new-raw-topic.sh "话题slug"

TOPIC="$1"
DATE=$(date +%Y-%m-%d)
DIR="content/${DATE}-${TOPIC}"

if [ -z "$TOPIC" ] || [ "$TOPIC" = "-h" ] || [ "$TOPIC" = "--help" ]; then
    echo "用法: ./scripts/new-raw-topic.sh \"话题slug\""
    echo "例:   ./scripts/new-raw-topic.sh \"opencode涨价观察\""
    exit 1
fi

if [ -d "$DIR" ]; then
    echo "❌ 目录已存在: $DIR"
    exit 1
fi

mkdir -p "$DIR"

cat > "${DIR}/raw.md" << 'TEMPLATE'
# 原始素材（话题：<话题名>）

> 把你想表达的一切都贴在这里，不需要整理，不需要结构。
> 可以包括：观点、吐槽、经历、数据、链接、随手记、语音转写、聊天记录。
> 越原生态越好——AI 的工作是整理，不是替你重新想。

## 素材


## 补充信息（可选）

- 发布日期：
- 目标读者：
- 想突出的重点：
- 不想写的：
TEMPLATE

echo "✅ 已创建话题文件夹: ${DIR}"
echo ""
echo "📝 下一步:"
echo "  1. 把想表达的内容全部贴进 ${DIR}/raw.md"
echo "  2. 告诉 AI：用「素材直出」工作流处理这个话题"
echo "  3. AI 整理完会停在检查点等你确认（结构 + 原声句 + 配图清单）"
