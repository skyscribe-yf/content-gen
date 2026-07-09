#!/usr/bin/env python3
"""
解析微信公众号后台的浏览器抓取数据

用法:
  python parse_wechat_stats.py <content_analysis.txt> <user_analysis.txt>
  python parse_wechat_stats.py --content <content.txt>    # 只解析内容数据
  python parse_wechat_stats.py --user <user.txt>          # 只解析用户数据
"""
import json
import re
import sys
from pathlib import Path


def parse_content_analysis(text):
    """解析内容分析页面文本"""
    result = {"overview": {}, "sources": {}, "articles": []}

    # 概况数据：阅读、分享、留言
    # 格式: "阅读\n6\n日\n33%\n周\n0\n日\n周"
    overview_match = re.search(r'阅读\n(\d+)\n日\n([-\d%]+)\n周', text)
    if overview_match:
        result["overview"]["reads_daily"] = int(overview_match.group(1))
        result["overview"]["reads_weekly_change"] = overview_match.group(2)

    share_match = re.search(r'分享\n(\d+)\n日', text)
    if share_match:
        result["overview"]["shares_daily"] = int(share_match.group(1))

    comment_match = re.search(r'留言\n(\d+)\n日', text)
    if comment_match:
        result["overview"]["comments_daily"] = int(comment_match.group(1))

    # 阅读总人数
    total_readers = re.search(r'阅读总人数：(\d+)人', text)
    if total_readers:
        result["overview"]["total_readers"] = int(total_readers.group(1))

    # 流量来源
    # 格式: "58.8%\n23.5%\n17.6%\n5.9%\n5.9%\n推荐\n其它\n公众号消息\n公众号主页\n搜一搜"
    source_percentages = re.findall(r'(\d+\.\d+)%', text)
    source_names_section = re.search(r'推荐\n(.+?)\n0%\n10%', text, re.DOTALL)
    if source_names_section:
        # 提取渠道名称（在百分比和坐标轴标签之间）
        source_block = text[text.find('推荐'):]
        source_lines = source_block.split('\n')
        sources = {}
        current_pct_idx = len(source_percentages) - 1  # 从后往前匹配
        for line in reversed(source_lines[:20]):
            line = line.strip()
            if line in ['推荐', '其它', '公众号消息', '公众号主页', '搜一搜',
                        '聊天', '朋友圈', '搜一搜', '公众号文章页关注', '名片分享',
                        '小程序关注', '他人转载', '微信广告', '视频号直播', '视频号']:
                if current_pct_idx >= 0:
                    sources[line] = source_percentages[current_pct_idx] + '%'
                    current_pct_idx -= 1
        result["sources"] = sources

    # 单篇文章数据
    # 格式: "损失函数：打分标准决定学习方向\n\n发表时间：2026/07/03\n\t12\t70.59%"
    article_pattern = re.compile(
        r'\n\n(.+?)\n\n发表时间：(\d{4}/\d{2}/\d{2})\n\t(\d+)\t([\d.]+)%',
        re.DOTALL
    )
    for match in article_pattern.finditer(text):
        title = match.group(1).strip()
        # 去掉前面可能附带的导航文字和空白
        title = title.split('\n')[-1].strip()
        # 去掉详情/近30天趋势等残留
        title = re.sub(r'^(详情近30天趋势)?', '', title)
        title = title.strip()
        if not title or len(title) > 50:
            # 如果标题异常长，说明匹配了多余内容，取最后一段
            parts = re.split(r'[\n\t]', title)
            title = parts[-1].strip()
        result["articles"].append({
            "title": title,
            "publish_date": match.group(2),
            "readers": int(match.group(3)),
            "percentage": float(match.group(4))
        })

    return result


def parse_user_analysis(text):
    """解析用户分析页面文本"""
    result = {"overview": {}, "daily": []}

    # 概况
    new_match = re.search(r'新关注人数\n(\d+)\n日', text)
    if new_match:
        result["overview"]["new_followers"] = int(new_match.group(1))

    cancel_match = re.search(r'取消关注人数\n(\d+)\n日', text)
    if cancel_match:
        result["overview"]["cancel_followers"] = int(cancel_match.group(1))

    net_match = re.search(r'净增关注人数\n(\d+)\n日', text)
    if net_match:
        result["overview"]["net_followers"] = int(net_match.group(1))

    cumulative_match = re.search(r'累计关注人数\n(\d+)\n日', text)
    if cumulative_match:
        result["overview"]["total_followers"] = int(cumulative_match.group(1))

    # 每日明细表格
    # 格式: "2026-07-05\n\t\n0\n\t\n0\n\t\n0\n\t\n1"
    daily_pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2})\n\t\n(\d+)\n\t\n(\d+)\n\t\n(\d+)\n\t\n(\d+)'
    )
    for match in daily_pattern.finditer(text):
        result["daily"].append({
            "date": match.group(1),
            "new": int(match.group(2)),
            "cancel": int(match.group(3)),
            "net": int(match.group(4)),
            "total": int(match.group(5))
        })

    return result


def generate_report(content_data, user_data):
    """生成结构化分析报告"""
    lines = []

    # 用户概况
    lines.append("## 📊 用户概况\n")
    ov = user_data.get("overview", {})
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 累计关注 | **{ov.get('total_followers', 'N/A')}** |")
    lines.append(f"| 近7天新增 | {ov.get('new_followers', 'N/A')} |")
    lines.append(f"| 近7天取关 | {ov.get('cancel_followers', 'N/A')} |")
    lines.append(f"| 净增 | {ov.get('net_followers', 'N/A')} |")

    # 内容分析
    cov = content_data.get("overview", {})
    lines.append("\n## 📖 内容分析\n")
    lines.append(f"| 指标 | 日 | 周 |")
    lines.append(f"|------|-----|-----|")
    lines.append(f"| 阅读 | {cov.get('reads_daily', 'N/A')} | {cov.get('reads_weekly_change', 'N/A')} |")
    lines.append(f"| 分享 | {cov.get('shares_daily', 'N/A')} | — |")
    lines.append(f"| 留言 | {cov.get('comments_daily', 'N/A')} | — |")
    if cov.get("total_readers"):
        lines.append(f"\n阅读总人数：**{cov['total_readers']}** 人")

    # 流量来源
    sources = content_data.get("sources", {})
    if sources:
        lines.append("\n### 流量来源\n")
        lines.append("| 渠道 | 占比 |")
        lines.append("|------|------|")
        for name, pct in sources.items():
            lines.append(f"| {name} | **{pct}** |")

    # 单篇数据
    articles = content_data.get("articles", [])
    if articles:
        lines.append("\n### 📰 单篇数据\n")
        lines.append("| 文章 | 发表时间 | 阅读人数 | 占比 |")
        lines.append("|------|---------|---------|------|")
        for a in articles:
            lines.append(f"| {a['title']} | {a['publish_date']} | **{a['readers']}** | {a['percentage']}% |")

    # 关键发现
    lines.append("\n## 🔍 关键发现 & 建议\n")
    suggestions = []

    # 基于数据自动生成建议
    total_followers = ov.get('total_followers', 0)
    if isinstance(total_followers, int) and total_followers < 100:
        suggestions.append("**冷启动阶段**：粉丝数极少，当前首要目标不是粉丝增长，而是内容质量 + 搜一搜排名，让每篇文章都能被搜索到。")

    if sources:
        search_pct = 0
        for name, pct in sources.items():
            if '搜一搜' in name:
                search_pct = float(pct.replace('%', ''))
        if search_pct < 10:
            suggestions.append(f"**搜一搜仅占 {search_pct}%**：标题关键词 SEO 有很大提升空间。确保标题前半段包含用户搜索的高频关键词，按教程/问答型标题公式。")

        recommend_pct = 0
        for name, pct in sources.items():
            if '推荐' in name:
                recommend_pct = float(pct.replace('%', ''))
        if recommend_pct > 40:
            suggestions.append(f"**推荐流量占 {recommend_pct}%**：内容被算法认可，但过度依赖推荐有风险。加强搜一搜和分享渠道，建立多元流量来源。")

    if articles:
        top = articles[0]
        if top['percentage'] > 50:
            suggestions.append(f"**「{top['title'][:15]}…」一骑绝尘**（{top['percentage']}%）：分析它的标题结构和关键词，后续文章复用成功模式。")

    total_readers = cov.get('total_readers', 0)
    if isinstance(total_readers, int) and isinstance(total_followers, int) and total_readers > 10 and total_followers > 0:
        conv_rate = total_followers / total_readers * 100
        if conv_rate < 5:
            suggestions.append(f"**关注转化率低**（{conv_rate:.1f}%）：{total_readers} 人阅读但关注增长不足。文章末尾加更醒目的关注引导和系列价值说明。")

    share_count = cov.get('shares_daily', 0)
    if isinstance(share_count, int) and share_count <= 1:
        suggestions.append("**分享极少**：传播力弱。在文章中加入社交钩子（「转发给学 AI 的朋友」），配图做成小红书风格卡片便于转发。")

    for i, s in enumerate(suggestions, 1):
        lines.append(f"{i}. {s}")

    if not suggestions:
        lines.append("数据量较小，暂无明确建议。持续产出高质量内容，积累更多数据后分析。")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="解析微信公众号后台数据")
    parser.add_argument("files", nargs="*", help="内容分析文本 和/或 用户分析文本")
    parser.add_argument("--content", help="内容分析文本文件")
    parser.add_argument("--user", help="用户分析文本文件")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    content_text = ""
    user_text = ""

    if args.content:
        content_text = Path(args.content).read_text()
    if args.user:
        user_text = Path(args.user).read_text()

    # 按位置参数
    for f in args.files:
        text = Path(f).read_text()
        # 用户分析页面特征更明确，优先匹配
        if '累计关注人数' in text and '净增关注人数' in text:
            user_text = text
        elif '阅读人数占比' in text or '内容分析' in text:
            content_text = text
        else:
            # 尝试按顺序分配
            if not content_text:
                content_text = text
            elif not user_text:
                user_text = text

    content_data = parse_content_analysis(content_text) if content_text else {}
    user_data = parse_user_analysis(user_text) if user_text else {}

    if args.json:
        print(json.dumps({"content": content_data, "user": user_data}, ensure_ascii=False, indent=2))
    else:
        print(generate_report(content_data, user_data))


if __name__ == "__main__":
    main()
