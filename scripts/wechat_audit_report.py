#!/usr/bin/env python3
"""Generate a self-contained HTML report from the local WeChat audit log."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import wechat_audit_log as audit


DEFAULT_LOG = ROOT / "docs" / "wechat-data-audit-log.json"
DEFAULT_OUT = ROOT / "docs" / "wechat-data-audit-report.html"

SOURCE_LABELS = {
    "recommendation": "推荐",
    "accountHome": "公众号主页",
    "chatSession": "聊天会话",
    "officialMessage": "公众号消息",
    "other": "其他",
    "moments": "朋友圈",
    "search": "搜一搜",
}
CHANNEL_LABELS = {
    "articlePage": "文章页",
    "other": "其他",
    "cardShare": "名片分享",
    "search": "搜一搜",
    "qrCode": "二维码",
}
SLOT_LABELS = {
    "messageArea": "留言区广告",
    "bottom": "底部广告",
    "inline": "文中广告",
    "keyword": "文中关键词广告",
}


def _stamp(snapshot: dict) -> dt.datetime:
    return dt.datetime.fromisoformat(snapshot["collectedAt"].replace("Z", "+00:00"))


def select_snapshot(log: dict, date: str | None = None) -> dict:
    snapshot = audit.snapshot_for_date(log, date) if date else audit.latest_snapshot(log)
    if snapshot is None:
        label = f" on {date}" if date else ""
        raise ValueError(f"no audit snapshot{label}")
    return snapshot


def previous_snapshot(log: dict, current: dict) -> dict | None:
    current_time = _stamp(current)
    candidates = [snapshot for snapshot in log.get("audits", []) if _stamp(snapshot) < current_time]
    return max(candidates, key=_stamp) if candidates else None


def compute_deltas(previous: dict | None, current: dict) -> dict[str, dict[str, Any]]:
    if previous is None:
        return {}
    values = {
        "readers30d": (
            previous["content"]["readers30d"],
            current["content"]["readers30d"],
        ),
        "dailyNewFollowers": (
            previous["users"]["daily"]["new"],
            current["users"]["daily"]["new"],
        ),
        "programmaticRevenue": (
            previous["income"]["overview"]["programmaticRevenue"],
            current["income"]["overview"]["programmaticRevenue"],
        ),
    }
    result = {}
    for key, (old, new) in values.items():
        delta = new - old
        result[key] = {
            "from": old,
            "to": new,
            "delta": round(delta, 2) if isinstance(delta, float) else delta,
        }
    return result


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _int(value: int | None) -> str:
    return "—" if value is None else f"{value:,}"


def _money(value: float | int | None) -> str:
    return "—" if value is None else f"¥{value:,.2f}"


def _number(value: float | int | None, suffix: str = "") -> str:
    return "—" if value is None else f"{value:g}{suffix}"


def _pct(value: float | int | None) -> str:
    return "—" if value is None else f"{value:g}%"


def _date(value: str) -> str:
    return _esc(value)


def _periods(snapshot: dict) -> str:
    periods = snapshot["periods"]
    names = (("content", "内容"), ("users", "用户"), ("income", "收入"))
    return " · ".join(
        f"{label} {_date(periods[key]['from'])} 至 {_date(periods[key]['to'])}"
        for key, label in names
    )


def _delta_text(metric: dict[str, Any], money: bool = False) -> str:
    value = metric["delta"]
    if money:
        text = _money(value)
    else:
        text = _int(value)
    class_name = "positive" if value > 0 else "negative" if value < 0 else "neutral"
    prefix = "+" if value > 0 and not money else ""
    if money and value > 0:
        text = "+" + text
    return f'<span class="delta {class_name}">{prefix}{text}</span>'


def _metric_card(label: str, value: str, detail: str = "") -> str:
    return (
        '<article class="metric-card">'
        f'<div class="metric-label">{_esc(label)}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-detail">{detail}</div>'
        "</article>"
    )


def _section(title: str, subtitle: str, body: str) -> str:
    return (
        '<section class="panel">'
        f'<div class="section-heading"><div><h2>{_esc(title)}</h2><p>{_esc(subtitle)}</p></div></div>'
        f"{body}"
        "</section>"
    )


def _comparison(previous: dict | None, deltas: dict[str, dict[str, Any]]) -> str:
    if previous is None:
        return '<div class="empty-state">暂无基线。当前日志只有这一条快照，后续审计追加后会自动显示变化。</div>'
    labels = {
        "readers30d": ("近 30 天阅读人数", False),
        "dailyNewFollowers": ("昨日新增关注", False),
        "programmaticRevenue": ("程序化广告收入", True),
    }
    rows = []
    for key, (label, money) in labels.items():
        metric = deltas[key]
        old = _money(metric["from"]) if money else _int(metric["from"])
        new = _money(metric["to"]) if money else _int(metric["to"])
        rows.append(
            f"<tr><th>{_esc(label)}</th><td>{old}</td><td>{new}</td><td>{_delta_text(metric, money)}</td></tr>"
        )
    return (
        '<div class="baseline-note">对照快照：'
        f"{_date(previous['collectedAt'])}</div>"
        '<div class="table-wrap"><table><thead><tr><th>指标</th><th>上次</th><th>本次</th><th>变化</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _sources(sources: dict[str, float]) -> str:
    rows = []
    for key, value in sorted(sources.items(), key=lambda item: item[1] or 0, reverse=True):
        label = SOURCE_LABELS.get(key, key)
        width = max(0, min(100, value or 0))
        rows.append(
            '<div class="bar-row">'
            f'<div class="bar-label">{_esc(label)}<span>{_pct(value)}</span></div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width:g}%"></div></div>'
            "</div>"
        )
    return "".join(rows)


def _articles(articles: list[dict]) -> str:
    rows = [
        f'<tr><td>{_date(article["date"])}</td><th>{_esc(article["title"])}</th>'
        f'<td class="number">{_int(article["reads"])}</td><td class="number">{_pct(article["share"])}</td></tr>'
        for article in articles
    ]
    return (
        '<div class="table-wrap"><table><thead><tr><th>日期</th><th>文章</th><th>阅读</th><th>占比</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _user_trend(trend: list[dict]) -> str:
    rows = [
        f'<tr><td>{_date(row["date"])}</td><td class="number">{_int(row["new"])}</td>'
        f'<td class="number">{_int(row["cancelled"])}</td><td class="number">{_int(row["net"])}</td>'
        f'<td class="number">{_int(row["total"])}</td></tr>'
        for row in trend
    ]
    return (
        '<div class="table-wrap compact"><table><thead><tr><th>日期</th><th>新增</th><th>取消</th><th>净增</th><th>累计</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _channels(channels: dict[str, dict]) -> str:
    rows = [
        f'<tr><th>{_esc(CHANNEL_LABELS.get(key, key))}</th><td class="number">{_int(value["count"])}</td>'
        f'<td class="number">{_pct(value["share"])}</td></tr>'
        for key, value in sorted(channels.items(), key=lambda item: item[1]["count"], reverse=True)
    ]
    return (
        '<div class="table-wrap"><table><thead><tr><th>来源</th><th>人数</th><th>占比</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _summary_metrics(summary: dict) -> str:
    metrics = (
        ("拉取", _int(summary["pulls"])),
        ("曝光", _int(summary["impressions"])),
        ("曝光率", _pct(summary["exposureRate"])),
        ("点击", _int(summary["clicks"])),
        ("CTR", _pct(summary["ctr"])),
        ("eCPM", _money(summary["ecpm"])),
        ("收入", _money(summary["revenue"])),
    )
    return '<div class="mini-metrics">' + "".join(
        f'<div><span>{_esc(label)}</span><strong>{value}</strong></div>' for label, value in metrics
    ) + "</div>"


def _income_day_table(rows: list[dict]) -> str:
    if not rows:
        return '<div class="empty-state">暂无每日明细</div>'
    body = []
    for row in rows:
        body.append(
            f'<tr><td>{_date(row["date"])}</td><td class="number">{_int(row["pulls"])}</td>'
            f'<td class="number">{_int(row["impressions"])}</td><td class="number">{_pct(row["exposureRate"])}</td>'
            f'<td class="number">{_int(row["clicks"])}</td><td class="number">{_pct(row["ctr"])}</td>'
            f'<td class="number">{_money(row["ecpm"])}</td><td class="number">{_money(row["revenue"])}</td></tr>'
        )
    return (
        '<div class="table-wrap compact"><table><thead><tr><th>日期</th><th>拉取</th><th>曝光</th><th>曝光率</th>'
        '<th>点击</th><th>CTR</th><th>eCPM</th><th>收入</th></tr></thead>'
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )


def _income_slots(slots: dict[str, dict]) -> str:
    sections = []
    for key, slot in slots.items():
        summary = slot["summary"]
        detail_note = f'每日明细合计 {_money(slot["dailyRevenueTotal"])}'
        sections.append(
            '<article class="slot-card">'
            f'<h3>{_esc(SLOT_LABELS.get(key, key))}</h3>'
            f'<p class="slot-note">关键数据卡收入 {_money(summary["revenue"])} · {detail_note}</p>'
            f"{_summary_metrics(summary)}"
            f"{_income_day_table(slot['daily'])}"
            "</article>"
        )
    return "".join(sections)


def _article_income(article_income: dict | None) -> str:
    if not article_income:
        return '<div class="empty-state">暂无文章级广告收入明细</div>'
    rows = []
    for article in article_income["articles"]:
        slots = " · ".join(
            f"{_esc(SLOT_LABELS.get(key, key))} {_money(values['revenue'])} ({_pct(values['share'])})"
            for key, values in article["slots"].items()
        ) or "暂无分广告位明细"
        rows.append(
            f'<tr><td>{_date(article["date"])}</td><th>{_esc(article["title"])}</th>'
            f'<td class="number">{_money(article["revenue"])}</td><td>{slots}</td></tr>'
        )
    return (
        f'<p class="slot-note">{_esc(article_income["scope"])}</p>'
        '<div class="table-wrap"><table><thead><tr><th>发布日期</th><th>文章</th><th>累计收入</th><th>分广告位收入</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _safe_json(snapshot: dict) -> str:
    return (
        json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def _styles() -> str:
    return """
:root { --ink:#17212b; --muted:#6b7785; --line:#e5e9ee; --paper:#f5f7fa; --card:#fff; --accent:#16a085; --accent-dark:#0f766e; --warm:#e67e22; --danger:#c0392b; }
* { box-sizing:border-box; }
body { margin:0; color:var(--ink); background:var(--paper); font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; }
main { max-width:1280px; margin:0 auto; padding:28px 22px 56px; }
.hero { color:#fff; background:linear-gradient(135deg,#153c46,#117c74 62%,#2c9a85); border-radius:22px; padding:34px 38px; box-shadow:0 14px 35px #0f766e22; }
.eyebrow { margin:0 0 8px; color:#b8f0df; font-size:12px; letter-spacing:.12em; text-transform:uppercase; }
h1,h2,h3,p { margin-top:0; } h1 { margin-bottom:12px; font-size:clamp(28px,4vw,48px); letter-spacing:-.04em; } h2 { margin-bottom:4px; font-size:21px; } h3 { margin-bottom:4px; font-size:17px; }
.hero-meta { display:flex; flex-wrap:wrap; gap:10px 22px; color:#d5f5ed; } .hero-meta span { white-space:nowrap; }
.metric-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:14px; margin:18px 0; } .metric-card,.panel,.slot-card { background:var(--card); border:1px solid var(--line); border-radius:16px; box-shadow:0 7px 20px #17212b0a; }
.metric-card { padding:18px 19px; min-height:126px; } .metric-label { color:var(--muted); font-size:13px; } .metric-value { margin:9px 0 3px; font-size:29px; font-weight:700; letter-spacing:-.04em; } .metric-detail { color:var(--muted); font-size:12px; }
.panel { margin:18px 0; padding:24px; } .section-heading { display:flex; justify-content:space-between; gap:16px; margin-bottom:18px; } .section-heading p { margin-bottom:0; color:var(--muted); }
.two-col { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:18px; } .two-col > .panel { margin:0; }
.bar-row { margin:13px 0; } .bar-label { display:flex; justify-content:space-between; margin-bottom:5px; } .bar-label span { color:var(--muted); } .bar-track { height:9px; background:#edf1f3; border-radius:99px; overflow:hidden; } .bar-fill { height:100%; background:linear-gradient(90deg,var(--accent),#67d3a8); border-radius:99px; }
.table-wrap { overflow-x:auto; } table { width:100%; border-collapse:collapse; min-width:560px; } th,td { padding:10px 9px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; } thead th { color:var(--muted); font-size:12px; font-weight:600; white-space:nowrap; } tbody th { font-weight:600; } .number { text-align:right; white-space:nowrap; } .compact table { min-width:650px; }
.baseline-note,.slot-note { color:var(--muted); font-size:13px; margin:0 0 12px; } .empty-state { padding:18px; color:var(--muted); background:#f7f9fa; border-radius:10px; }
.delta { font-weight:700; white-space:nowrap; } .positive { color:var(--accent-dark); } .negative { color:var(--danger); } .neutral { color:var(--muted); }
.slot-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; } .slot-card { padding:18px; } .mini-metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin:15px 0; } .mini-metrics div { padding:8px 9px; background:#f7f9fa; border-radius:9px; } .mini-metrics span { display:block; color:var(--muted); font-size:11px; } .mini-metrics strong { display:block; margin-top:2px; font-size:15px; }
.note-list { margin:0; padding-left:20px; } .footnote { color:var(--muted); font-size:12px; }
@media (max-width:900px) { .metric-grid { grid-template-columns:repeat(3,minmax(0,1fr)); } .two-col,.slot-grid { grid-template-columns:1fr; } }
@media (max-width:580px) { main { padding:14px 11px 35px; } .hero { padding:25px 22px; border-radius:17px; } .metric-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; } .metric-card { padding:14px; min-height:105px; } .metric-value { font-size:23px; } .panel { padding:17px 14px; } .mini-metrics { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media print { body { background:#fff; } main { max-width:none; padding:0; } .hero,.metric-card,.panel,.slot-card { box-shadow:none; } .hero { color:#000; background:#fff; border:2px solid #153c46; } .eyebrow,.hero-meta,.section-heading p,.metric-label,.metric-detail,.slot-note,.baseline-note,.footnote { color:#444; } .panel,.slot-card { break-inside:avoid; } }
"""


def render_report(log: dict, date: str | None = None) -> str:
    current = select_snapshot(log, date)
    previous = previous_snapshot(log, current)
    deltas = compute_deltas(previous, current)
    content = current["content"]
    users = current["users"]
    income = current["income"]
    daily_content = content["daily"]
    daily_users = users["daily"]
    overview = income["overview"]

    metric_grid = "".join(
        (
            _metric_card("近 30 天阅读人数", _int(content["readers30d"]), "内容数据窗口"),
            _metric_card("昨日阅读", _int(daily_content["reads"]), f"分享 {_int(daily_content['shares'])} · 留言 {_int(daily_content['comments'])}"),
            _metric_card("累计关注", _int(daily_users["total"]), f"昨日新增 {_int(daily_users['new'])} · 净增 {_int(daily_users['net'])}"),
            _metric_card("推荐流量", _pct(content["sources"].get("recommendation")), "内容来源占比"),
            _metric_card("累计广告收入", _money(overview["cumulativeRevenue"]), f"昨日增量 {_money(overview['yesterdayIncrement'])}"),
        )
    )
    comparison = _comparison(previous, deltas)
    generated = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")
    title = f"{_esc(log['account'])} · 微信公众号审计报告"
    snapshot_json = _safe_json(current)

    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{_styles()}</style>
</head>
<body>
<main>
<header class="hero">
  <p class="eyebrow">WECHAT DATA AUDIT / STATIC REPORT</p>
  <h1>{title}</h1>
  <div class="hero-meta">
    <span>采集：{_date(current['collectedAt'])}</span>
    <span>数据截至：{_date(current['dataThrough'])}</span>
    <span>{_periods(current)}</span>
  </div>
</header>
<section class="metric-grid">{metric_grid}</section>
{_section("审计变化", "只比较稳定的核心指标，不修正后台原始口径。", comparison)}
<div class="two-col">
  {_section("流量来源", "近 30 天内容来源占比。", _sources(content["sources"]))}
  {_section("用户渠道", f"渠道合计 {_int(users['channelTotal'])}；累计关注 {_int(daily_users['total'])}，两种口径原样保留。", _channels(users["channels"]))}
</div>
{_section("文章表现", "按后台采集顺序保留单篇阅读和占比。", _articles(content["articles"]))}
<div class="two-col">
  {_section("用户增长趋势", "用户分析页面的每日新增、取消、净增和累计。", _user_trend(users["trend"]))}
  {_section("收入概览", "账户概览收入与广告位日报属于不同报告口径。", _summary_metrics({"pulls": 0, "impressions": 0, "exposureRate": None, "clicks": 0, "ctr": None, "ecpm": None, "revenue": overview["programmaticRevenue"]}) + '<p class="footnote">累计收入 ' + _money(overview["cumulativeRevenue"]) + ' · 程序化广告 ' + _money(overview["programmaticRevenue"]) + ' · 互选 ' + _money(overview["mutualSelectionRevenue"]) + ' · 商业推广 ' + _money(overview["commerceRevenue"]) + '</p>')}
</div>
{_section("流量主广告位", "关键数据卡与每日明细分别保留，差异不做人工合并。", '<div class="slot-grid">' + _income_slots(income["slots"]) + '</div>')}
{_section("文章广告收入", "只展示后台提供的文章发布后 7 日内累计收入和分广告位占比。", _article_income(income.get("articleIncome")))}
{_section("审计备注", "来自后台采集时的口径说明。", '<ul class="note-list">' + ''.join(f'<li>{_esc(note)}</li>' for note in current["notes"]) + '</ul>')}
<p class="footnote">报告生成时间：{_esc(generated)} · 数字事实源：docs/wechat-data-audit-log.json · 本 HTML 为展示产物。</p>
</main>
<script type="application/json" id="audit-data">{snapshot_json}</script>
</body>
</html>
'''


def generate_report(log_path: Path = DEFAULT_LOG, out_path: Path = DEFAULT_OUT, date: str | None = None) -> Path:
    log = audit.load_log(log_path)
    errors = audit.validate_log(log)
    if errors:
        raise ValueError("invalid log:\n" + "\n".join(errors))
    output = render_report(log, date)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output, encoding="utf-8")
    return out_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--date")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        output = generate_report(args.log, args.out, args.date)
        print(f"generated {output}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
