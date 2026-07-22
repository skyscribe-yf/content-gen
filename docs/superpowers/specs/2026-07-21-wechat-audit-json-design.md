# 微信公众号审计 JSON 日志设计

## 背景

微信公众平台的历史数据可见范围有限，不能作为长期数据仓库。项目需要把每次审计采集到的数字保存到本地，并支持后续加载、查询和区间对照。

## 目标

- 保存每次审计的原始数字快照。
- 用 JSON Schema 固化字段、类型和必填项。
- 使用 Python 标准库实现保存、校验、加载和对照查询。
- 下一次审计开始前可读取最近一次快照；采集完成后追加新快照。
- 保留后台原始口径差异，不自动平账或合并不同时间范围的数据。

## 非目标

- 本轮不接管浏览器采集流程。
- 本轮不自动把 JSON 渲染成 Markdown。
- 本轮不新增第三方依赖或数据库。

## 文件

- `docs/wechat-data-audit-log.json`：唯一的数字事实源，按采集日期保存历史快照。
- `docs/wechat-data-audit-log.schema.json`：JSON Schema，约束日志结构。
- `scripts/wechat_audit_log.py`：标准库 CLI。
- `docs/wechat-data-audit-log.md`：人读版当前日志；数字以 JSON 为准。
- `docs/wechat-data-insights.md`：分析、判断和执行规则，不作为原始数字唯一来源。

## JSON 结构

顶层字段：

- `schemaVersion`：整数，当前为 `1`。
- `account`：公众号名称。
- `audits`：按采集时间保存的审计快照数组。

每个快照包含：

- `collectedAt`：带时区的 ISO 8601 采集时间。
- `dataThrough`：内容和用户日结的后台数据截止日期。
- `periods`：分别记录内容、用户和流量主数据的起止日期，避免把 30 日内容窗口与 7 日广告日报混为一谈。
- `content`：近 30 天阅读人数、指定日阅读/分享/留言、流量来源和单篇文章。
- `users`：指定日新增/取消/净增/累计关注、关注渠道和日新增趋势。
- `income`：概览累计收入、各广告位关键数据、各广告位每日明细、文章收入页状态，以及 `articleIncome` 中每篇文章发布后 7 日累计收入和分广告位占比。
- `notes`：口径差异或后台异常的文字说明数组。

金额、人数、次数使用 JSON number；无数据的比例或 eCPM 使用 `null`，不使用字符串 `-`。广告位和渠道使用对象键，便于脚本查询和未来增加新渠道。

## CLI

```text
validate                         校验 JSON 语法和当前 Schema 要求
append --input FILE              校验并追加一个快照；同一 collectedAt 拒绝重复
latest                            输出最近一次快照
show --date YYYY-MM-DD            输出该日期最新快照
compare --from DATE --to DATE     对照两个日期各自的最新快照
```

默认文件路径为 `docs/wechat-data-audit-log.json`，可通过 `--log` 覆盖。`show` 和 `compare` 按 `collectedAt` 的本地日期匹配；同一天重复审计时选择最新一条。命令只读操作不修改文件；`append` 先写临时文件，再原子替换日志，避免中途写坏历史数据。

## 数据流

1. 审计开始：运行 `latest`，读取最近快照作为对照基线。
2. 浏览器采集：按 `wechat-data-audit` 现有流程采集内容、用户和流量主数据。
3. 规范化：将本次数据整理为一个快照 JSON，不改写历史快照。
4. 保存：运行 `append --input ...`，脚本校验结构、日期和重复键后追加。
5. 验证：运行 `validate`。
6. 分析：对照 JSON 生成或更新 `wechat-data-insights.md`、`wechat-ops.md` 和 `article-title-seo.md`。

## 校验规则

- 日志必须是合法 JSON，顶层 `schemaVersion` 必须为 `1`。
- `audits` 必须是数组；每个快照必须有 `collectedAt`、`dataThrough`、`periods`、`content`、`users`、`income`。
- `collectedAt` 必须带时区；`dataThrough`、各周期日期和趋势日期使用 `YYYY-MM-DD`。
- 同一 `collectedAt` 不允许重复追加。
- 比例字段必须为 0–100 的 number 或 `null`。
- 人数、拉取量、曝光量、点击量必须为非负整数。
- 金额和 eCPM 必须为非负 number 或 `null`。
- 校验失败时不修改原日志。

Python 只使用标准库实现上述项目规则；JSON Schema 文件仍采用标准 Schema 格式，方便编辑器、CI 或未来引入 `jsonschema` 时复用。

## 验证

- 用 Python 标准库测试 `append`、重复日期拒绝、`latest`、`show`、`compare` 和 `validate`。
- 使用当前 2026-07-21 审计数字作为固定样本，验证读取出的核心指标与现有 Markdown 日志一致。
- 检查非法 JSON、缺字段、负数、超范围比例和重复快照不会破坏原日志。
