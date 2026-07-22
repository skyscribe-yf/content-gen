# 微信公众号审计静态 HTML 报告设计

## 背景

公众号审计数字已固化在 `docs/wechat-data-audit-log.json`。需要一个无需服务器、无需网络依赖、双击即可打开的静态报告，兼顾管理复盘和原始数据核查。

## 目标

- 从本地 JSON 自动生成最新或指定日期的审计报告。
- 上半部分提供核心指标、趋势、变化和异常提示。
- 下半部分保留文章、用户趋势、广告位和每日明细。
- 所有 CSS 和当前快照数据内嵌到单个 HTML 文件。
- 没有上一次快照时显示“暂无基线”，不编造变化值。
- 支持中文、响应式布局和打印样式。

## 非目标

- 不使用 CDN、图表库、构建工具或本地服务器。
- 不让 HTML 在运行时通过 `fetch` 读取 JSON，避免 `file://` 跨域问题。
- 不在报告中重新计算或修正后台口径差异。

## 文件与命令

- `scripts/wechat_audit_report.py`：读取 JSON、选择快照、生成 HTML。
- `docs/wechat-data-audit-report.html`：默认生成的最新报告，不作为数字事实源。
- `tests/test_wechat_audit_report.py`：测试快照选择、变化计算、HTML 关键内容和 HTML 转义。

```bash
python scripts/wechat_audit_report.py
python scripts/wechat_audit_report.py --date 2026-07-21
python scripts/wechat_audit_report.py --date 2026-07-21 --out /tmp/wechat-report.html
```

默认读取 `docs/wechat-data-audit-log.json`，默认输出 `docs/wechat-data-audit-report.html`；`--log` 可覆盖输入路径。

## 页面结构

1. **页头**：账号名称、审计日期、数据截止日期、各数据周期。
2. **核心指标卡**：近 30 天阅读人数、昨日阅读/分享/留言、累计关注、昨日新增、累计程序化广告收入。
3. **变化和结论**：与前一个快照比较阅读、关注和收入；无前一快照时显示“暂无基线”。
4. **内容与流量**：来源横条、单篇文章表格，突出推荐、主页和搜一搜等关键渠道。
5. **用户增长**：新增/取消/净增趋势表，关注渠道表。
6. **流量主**：广告位对比卡片和每日明细；明确累计账户收入与日报广告位收入不是同一口径。
7. **备注**：原始口径差异和文章收入页状态。

图形使用 CSS 横条和表格，避免第三方库。所有展示数据使用 HTML 转义后写入模板，原始快照以安全 JSON 形式内嵌。

## 变化计算

报告只计算以下稳定指标：

- `content.readers30d`
- `users.daily.new`
- `income.overview.programmaticRevenue`

变化显示 `当前值`、`上次值` 和 `差值`；收入差值保留两位小数。前一快照按采集时间排序，选择目标快照之前最近的一条。

## 验证

- Python 标准库单元测试覆盖默认输出、指定日期输出、无基线、变化值、HTML 转义和关键标题。
- 生成 HTML 后检查文件非空，包含账号、审计日期和核心指标，不包含外部 `http://` 或 `https://` 资源引用。
- 使用 `python -m html.parser` 验证生成文档可解析。
