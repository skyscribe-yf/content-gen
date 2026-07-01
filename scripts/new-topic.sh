#!/bin/bash
# 新建选题脚手架
# 用法: ./new-topic.sh "梯度下降-蒙着眼下山"

TOPIC="$1"
DATE=$(date +%Y-%m-%d)
DIR="content/${DATE}-${TOPIC}"

if [ -z "$TOPIC" ]; then
    echo "用法: ./new-topic.sh \"主题名\""
    echo "例:   ./new-topic.sh \"梯度下降-蒙着眼下山\""
    exit 1
fi

mkdir -p "${DIR}/xiaohongshu"
mkdir -p "${DIR}/bilibili"
mkdir -p "${DIR}/assets"

# 创建初稿模板
cat > "${DIR}/draft.md" << 'TEMPLATE'
# [主题名]

## 🎯 开头钩子（100字）
> [反直觉问题/生活场景]

## 💡 直觉解释（400字）
> [生活类比，不许写公式]

类比：[X] 就像 [Y]，因为 [Z]

关键 insight：[一句话]

## 📐 数学形式化（400字）
> [公式 + 每条一句话解释]

## 🔧 代码实现（300字）
> [30行 Python 最小示例]

## 🌍 应用场景（200字）
1. [应用1]
2. [应用2]
3. [应用3]

## 📌 一句话总结
> [概念] = [直觉 + 数学一句话]
TEMPLATE

# 创建小红书文案模板
cat > "${DIR}/xiaohongshu/caption.txt" << 'XHS'
[核心概念一句话] 💡

[2-3句话直觉解释]

📌 收藏慢慢看

#数学 #AI科普 #人工智能 #[具体概念] #知识卡片
XHS

# 创建 B站脚本模板
cat > "${DIR}/bilibili/script.md" << 'BILI'
# 视频脚本：[主题名]
时长：3-5分钟

## 开头钩子（0:00-0:15）
## 直觉解释（0:15-1:00）
## 核心原理（1:00-2:30）
## 数学形式化（2:30-3:30）
## 代码演示（3:30-4:15）
## 应用场景（4:15-4:45）
## 总结（4:45-5:00）
BILI

echo "✅ 已创建选题文件夹: ${DIR}"
echo ""
echo "📝 下一步:"
echo "  1. 编辑 ${DIR}/draft.md 写深度稿"
echo "  2. 从深度稿拆解为小红书信息图"
echo "  3. 用 Manim 制作 B站动画"
echo "  4. 写知乎回答引流"
echo ""
echo "⚠️  完成后把 topic-tracker.md 中对应选题状态改为 ✅ 已写"
