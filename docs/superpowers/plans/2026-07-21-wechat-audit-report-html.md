# 微信公众号审计报告 HTML 实现计划

> **执行说明：** 按测试驱动开发执行：先写会失败的测试，再实现最小功能，最后运行完整验证。

## 目标

新增一个 Python 标准库生成器，把 `docs/wechat-data-audit-log.json` 的最新或指定日期快照渲染为单文件静态 HTML；页面同时提供管理看板和完整明细。

## 步骤

### 1. 写报告生成器测试

文件：`tests/test_wechat_audit_report.py`

- 测试默认选择最新快照。
- 测试指定日期选择当天 `collectedAt` 最新快照。
- 测试前一快照变化计算和无基线行为。
- 测试 HTML 包含账号、日期、核心指标、文章和广告位内容。
- 测试用户输入文本会被 HTML 转义。
- 测试输出可由标准库 `html.parser` 解析。

验证：`python -m unittest discover -s tests -p 'test_wechat_audit_report.py' -v`，先确认因模块不存在而失败。

### 2. 实现最小生成器

文件：`scripts/wechat_audit_report.py`

- 复用 `scripts.wechat_audit_log` 的加载和日期选择逻辑。
- 增加目标日期、前一快照和稳定指标变化计算。
- 使用标准库 `html.escape`、字符串模板、内嵌 CSS 横条和安全 JSON 快照。
- 提供 `--log`、`--date`、`--out` 参数。
- 输出目录自动创建，使用 UTF-8 写入。

验证：报告测试转绿，命令行可生成默认报告和自定义输出。

### 3. 集成文档与生成产物

文件：`.agents/skills/wechat-data-audit/SKILL.md`、`AGENTS.md`、`docs/wechat-data-audit-report.html`

- 在审计流程中加入追加 JSON 后生成报告的命令。
- 说明 HTML 是展示产物，不是数字事实源。
- 生成当前 2026-07-21 报告。

### 4. 完成验证

- `python -m unittest discover -s tests -v`
- `python scripts/wechat_audit_log.py validate`
- 生成默认 HTML 并用 `html.parser` 解析。
- 检查报告不引用外部资源。
- `git diff --check`
