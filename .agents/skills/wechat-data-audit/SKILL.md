---
name: wechat-data-audit
description: "Audit WeChat Official Account article data, extract performance metrics (reads, follows, shares, comments, traffic sources, eCPM, ad revenue), generate insights, and update project documentation with findings. Use when user asks to '检查公众号数据', '分析文章表现', 'wechat audit', '数据复盘', '运营分析', '公众号复盘', '查看文章数据', or after publishing a batch of articles."
---

# WeChat Data Audit

对公众号进行数据审计：采集文章表现数据 + 用户增长数据 + 流量主收入（eCPM）→ 生成洞察 → 写入项目文档。

**前置依赖**：[wechat-stats](../wechat-stats/SKILL.md) 的 Cookie 注入模式。

---

## 工作流

### Phase 0: 加载和保存本地审计历史

微信后台历史数据可见范围有限。数字事实必须先从本地 JSON 加载，采集后再追加到本地 JSON，不能只依赖后台当前页面或覆盖旧快照。

固定文件：

- 数字事实源：`docs/wechat-data-audit-log.json`
- JSON Schema：`docs/wechat-data-audit-log.schema.json`
- 操作脚本：`scripts/wechat_audit_log.py`
- 人读版日志：`docs/wechat-data-audit-log.md`

#### 审计开始前

1. 运行 `python scripts/wechat_audit_log.py validate`，确认本地日志未损坏。
2. 运行 `python scripts/wechat_audit_log.py latest`，加载最近一次快照作为对照基线。
3. 需要查看历史时，使用 `show --date YYYY-MM-DD` 或 `compare --from YYYY-MM-DD --to YYYY-MM-DD`，不要返回微信后台翻查已经不可见的旧数据。

#### 采集完成后

1. 把本次采集结果规范化为一个独立快照 JSON，写入 `/tmp/audit-snapshot.json`。
2. 快照必须包含 `collectedAt`、`dataThrough`、`periods`、`content`、`users`、`income`、`notes`。
3. 内容字段使用稳定英文键：`readers30d`、`daily`、`sources`、`articles`；用户字段使用 `channels`、`trend`；流量主广告位放在 `income.slots` 下，例如 `messageArea`、`bottom`、`inline`、`keyword`；文章发布后 7 日累计收入放在 `income.articleIncome`，按文章保存分广告位收入占比。
4. 无数据的曝光率、CTR 或 eCPM 使用 JSON `null`，不要写字符串 `-`；后台卡片和每日明细不一致时，两种口径都保留在 `notes` 或对应字段中。
5. 运行 `python scripts/wechat_audit_log.py append --input /tmp/audit-snapshot.json`。脚本会校验结构、拒绝重复 `collectedAt`，并使用原子替换保护历史文件。
6. 再运行 `python scripts/wechat_audit_log.py validate`。验证通过后，才更新 `docs/wechat-data-insights.md`、`docs/wechat-ops.md` 和 `docs/article-title-seo.md`。
7. 运行 `python scripts/wechat_audit_report.py` 生成 `docs/wechat-data-audit-report.html`。报告是展示产物，不是数字事实源；需要临时文件时使用 `--out`，需要历史快照时使用 `--date YYYY-MM-DD`。

JSON 是数字唯一事实源；Markdown 只保存人读版和分析结论。禁止直接删除或重写已有 `audits` 快照。

### Phase 1: Cookie 注入 + 登录

先按 `wechat-stats` 的流程注入 Cookie，确保登录态。

快速步骤：

1. 读取 `.env` 确认有 `WECHAT_COOKIE`
2. **前置时效检查**（2026-07-14 复盘新增）：Cookie 实测有效期 **≤ 2 天**（远短于 wechat-stats 文档所述 7–30 天）。若上次注入距本次审计 ≥ 2 天，直接按过期处理，跳到扫码降级流程，避免注入后仍在登录页打转浪费时间。注入后导航 `https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN`，用 `window.wx.uin > 0` 判定；uin=0 即过期。
2. 用 `agent_browser` `sessionMode=fresh` 打开 `https://mp.weixin.qq.com/`
3. 通过 CDP 注入 Cookie：`node scripts/wechat-cdp-cookie.mjs inject`（自动定位 `/tmp/agent-browser-chrome-*/DevToolsActivePort`，读 `.env` 的 `WECHAT_COOKIE`，在 weixin page tab 上调 `Network.setCookie`，domain `.qq.com`）
4. 导航到 `https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN` 验证登录：`node scripts/wechat-cdp-cookie.mjs status`（`uin > 0` 即成功；uin=0 → Cookie 过期）
5. 登录成功后**立即导出新 Cookie**：`node scripts/wechat-cdp-cookie.mjs export`（写回 `.env`，下次免扫码）

#### ⚠️ Cookie 过期时的处理

**第一步：检查当前模型是否支持视觉。** 读取 `~/.pi/agent/models.json`，检查当前模型的 `input` 数组是否包含 `"image"`。

**若模型支持视觉**（如 `gpt-5.6-luna`、`xopkimik26`）：

1. `agent_browser screenshot /tmp/wechat-qr.png`
2. `read /tmp/wechat-qr.png` → Pi TUI 会内联渲染二维码
3. 告知用户扫码，等待确认后用 `eval` 验证登录态

**若模型不支持视觉**（如 `deepseek-v4-pro`、`xopglm51`）：

> 🚫 **直接退出，不要继续。** 告诉用户：
>
> "Cookie 已过期，当前模型不支持视觉，无法展示二维码。请执行以下任一操作后重试：
> 1. 切换到支持图片的模型（如 `gpt-5.6-luna`、`xopkimik26`），然后重新运行
> 2. 或手动刷新 `.env` 中的 `WECHAT_COOKIE`（在浏览器中登录 mp.weixin.qq.com 后导出 cookie）"

**禁止**尝试任何 workaround（`open file://`、base64、`read` 代理描述等）——它们要么不可靠，要么会触发截图→读取的死循环。

### Phase 2: 采集内容分析数据

1. 点击导航栏「数据分析」→「内容分析」
2. 等待页面加载完成后，用 `agent_browser get text body` 获取全文
3. 从文本中解析以下数据：

**数据概况**（2026-08-20 实测更新）：卡片已从 3 指标扩展为 **5 指标**——阅读 / 点赞 / 分享 / 收藏 / 留言（昨日 `901 / 21 / 115 / 16 / 11`），但审计 schema 仍只存 `reads/shares/comments`，点赞/收藏写入 `notes`。
- 阅读（日/周）、分享（日/周）、留言（日/周）
- 阅读总人数
- 阅读人数趋势（近30天）

**流量来源构成**（解析百分比）：
- 聊天会话 / 推荐 / 朋友圈 / 公众号主页 / 其它 / 公众号消息 / 搜一搜

**单篇文章数据**（列表）：
- 文章标题
- 发表时间
- 阅读人数
- 阅读人数占比

### Phase 3: 采集用户分析数据

1. 从内容分析页点击「用户分析」
2. 用 `agent_browser get text body` 获取全文
3. 从文本中解析：

**用户增长**：
- 新关注人数（日/周/月）
- 取消关注人数
- 净增关注人数
- 累计关注人数

**渠道构成**：
- 文章页关注 / 搜一搜 / 扫描二维码 / 名片分享 等各渠道占比

**日新增趋势**（详细数据表格）：
- 每日新增关注 / 取消关注 / 净增关注 / 累计关注

> **⚠️ 后台延迟容错（2026-08-20 新增）**：`2026-08-19` 实测后台顶部提示“后台数据系统统计延迟”，最新一天累计关注在页面显示为 `0`（新增 55 但累计 0）。此时**不直接存 0**，按 `前一日累计 + 当日净增` 推算（如 `676+55=731`），在 `notes` 中同时保留“页面显示 0（延迟）+ 推算值”两种口径，并在 `periods.users.to` 仍标为 `2026-08-19`。

### Phase 3.5: 采集流量主收入数据（含 eCPM）

**前提**：已开通流量主且已有广告收入数据。若未开通则跳过本阶段。

#### Step 1: 导航到流量主概览页

从首页侧边栏：hover「收入变现」→ 展开子菜单 → 点击「流量主」。

执行方式：

```javascript
// agent_browser eval --stdin
// 找到 收入变现 菜单并 hover 展开子菜单
(() => {
  const income = [...document.querySelectorAll('*')].find(el => 
    el.textContent.trim() === '收入变现' && el.children.length === 0
  );
  if (!income) return 'INCOME_MENU_NOT_FOUND';
  const parent = income.closest('li, [role="menuitem"], .menu-item');
  parent.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
  // 等子菜单渲染后，点击 流量主 链接
  setTimeout(() => {
    const ll = [...parent.querySelectorAll('a, [role="menuitem"]')]
      .find(a => a.textContent.includes('流量主'));
    if (ll) ll.click();
  }, 500);
  return 'HOVER_TRIGGERED';
})()
```

等待 2-3 秒后确认页面加载。目标 URL 形如：
`https://mp.weixin.qq.com/cgi-bin/frame?t=ad_system%2Fcommon_frame&t1=publisher%2Fpublisher_overview&lang=zh_CN&token=...`

#### Step 2: 导航到数据统计（日报表）

概览页加载后，点击左侧「数据统计」子 tab。

```javascript
// 直接点击 A 标签（href 含 publisher_report）
(() => {
  const link = document.querySelector('a[href*="publisher_report"]');
  if (link) { link.click(); return 'CLICKED'; }
  return 'NOT_FOUND';
})()
```

页面 URL 变为：`…&t1=publisher%2Fpublisher_report&pos=1&…`。等待 3 秒让 iframe 内容渲染。

#### Step 3: 采集广告位数据（日报表）

确认当前在「广告位数据」tab 下（默认），用：

```
agent_browser get text body
```

输出应包含：

**关键数据卡片**（7 个指标）：
- 拉取量 / 曝光量 / 曝光率 / 点击量 / 点击率 / eCPM（元）/ 收入（元）

**每日数据明细表格**（每行一天）：
- 时间 / 拉取量 / 曝光量 / 曝光率 / 点击量 / 点击率 / eCPM（元） / 收入（元）

保存输出到 `/tmp/wechat-income-report.txt`。

#### Step 4: 切换到「文章收入」tab（可选）

「文章收入」tab 提供按文章维度的收入明细（账号较新、文章数少时可能与广告位数据相同）。

```javascript
// 点击 wxadcontainer 中的 文章收入 tab
(() => {
  const container = document.getElementById('wxadcontainer');
  if (!container) return 'NO_CONTAINER';
  const tab = [...container.querySelectorAll('*')]
    .find(el => el.textContent?.trim() === '文章收入');
  if (tab) { tab.click(); return 'CLICKED'; }
  return 'NOT_FOUND';
})()
```

等待 3 秒，再抓一次 `get text body`。与 Step 3 数据对比：
- 若表格内容不同 → 有文章级数据，单独保存
- 若与 Step 3 相同 → 文章级数据尚不可用（新账号正常现象）

#### Step 5: 采集概览页累计收入

概览页（`publisher_overview`）显示累计收入，口径可能与日报表不一致（概览含多广告位合计，日报表默认单一广告位）。

> **⚠️ 概览改版（2026-08-20 实测）**：页面已**移除“昨日增量”卡片**，仅显示累计/程序化/互选/带货四项。昨日增量需**自行推算**：取日报表最新一天三广告位收入合计（留言区+底部+文中，如 `0.59+0.41+1.34=2.34`），并与 `累计差值`（如 `50.21-47.79=2.42`）交叉验证，允许 0.08 元舍入差，写入 `income.overview.yesterdayIncrement`。

回到概览页获取「账户收入」卡片：
- 累计收入（元）
- 程序化广告收入（元）
- 昨日增量（若页面无卡片则按上条推算）
- 互选合作收入 / 带货与内容推广

#### 广告位说明

页面顶部的广告位切换按钮对应不同收入来源：
- **留言区广告** — 默认选中，底部广告位
- **底部广告** — 文章底部横幅
- **文中广告** — 文章正文内嵌（曝光率通常 2–3× 底部广告）
- **文中关键词广告** — 关键词触发
- **贴图底部推荐流广告位** — 图片消息底部
- **互选广告** — 品牌合作

默认采集「留言区广告」数据。若已启用文中广告，需额外点击「文中广告」按钮分别采集。

#### 注意事项

- 流量主页面使用 **iframe 架构**（`#mpIFrame`），内容渲染在 `#wxadcontainer` 容器中
- **禁止**直接 URL 导航到 `/cgi-bin/frame?...` ——`eval location.href=n` 不穿透 iframe
- 使用 `document.querySelector('a[href*="publisher_report"]').click()` 触发 iframe 内导航
- 概览页「昨日 +0.94」可能 ≠ 日报表当天收入合计——口径差异是正常的，运营决策以概览页累计为准，分析用日报表分日数据
- **2026-08-20 起**：概览页不再显示“昨日”卡片，6 日窗口（如 `08-13–08-18`）且滞后内容 1 天属正常；不要强行补 7 日或等待 08-19 收入，日明细合计与卡片合计 0.01 元舍入差需在 `notes` 保留两种口径

### Phase 4: 分析 + 生成洞察

将采集到的数据按以下维度分析：

#### 4a. 推广效果评估

- 计算推广流量占比：聊天会话% + 朋友圈%
- 对比推广日 vs 非推广日的新增关注（正常日应为 0-2，推广日可能 30-50+）
- 判断推广衰减：推广次日的新增是否回落

#### 4b. 标题表现评估

- 对比各文章的读数和吸粉数
- 识别高转化标题模式（痛点提问型 vs 文艺比喻型）
- 参考 `docs/article-title-seo.md` 的标题公式，看哪种公式实际数据好

#### 4c. SEO 健康度

- 搜一搜占比：< 2% → SEO 严重缺失，需要优化；5-10% → 一般；> 15% → 健康
- 检查已发文章的摘要是否含关键词

#### 4d. 系列文章回读

- 公众号主页占比高（> 15%）→ 系列策略有效，但需补交叉链接
- 占比低（< 5%）→ 读者不主动回读，需在文末强化导航

#### 4e. 留言互动

- 留言数 → 0 即为互动引导失效
- 有留言则分析留言质量

#### 4f. 流量主收入与 eCPM

- 计算收入效率：收入/阅读、收入/曝光、收入/日
- eCPM 波动评估：< 50 次日曝光 → 波动无统计意义，不用于决策
- 曝光率诊断：曝光率 = 曝光量 / 拉取量 —— 低于 10% 说明广告位可见性差（读者滚不到广告位）
- 点击率：0% 在当前阶段（< 500 曝光/日）属正常，不是内容问题
- 收入瓶颈定位：判断核心瓶颈是「阅读量 → 拉取量」还是「拉取量 → 曝光量 → eCPM」
- 广告位对比：若多广告位有数据，对比底部/文中广告的曝光率和 eCPM

关键判断标准：

| 指标 | 🟢 健康 | 🟡 关注 | 🔴 行动 |
|------|---------|---------|---------|
| 日曝光量 | > 500 | 100–500 | < 100 |
| 曝光率 | > 15% | 8–15% | < 8% |
| eCPM | 5–15 元 | 2–5 / 15–30 | < 2 或 > 30 |
| CTR | > 0.5% | 0.1–0.5% | < 0.1% 且曝光 > 500 |

注意：上表阈值仅在日曝光量 > 200 时适用。低于 200 曝光/日时只看**曝光率**和**拉取量趋势**，不分析 eCPM 和 CTR。

### Phase 5: 将洞察写入项目文档

根据分析结果更新以下文件：

**更新 `docs/wechat-data-insights.md`**（如果不存在则创建）：
- 数据采集日期
- 推广效果数据（推广流量占比、推广日 vs 非推广日对比）
- 标题表现数据（各标题风格的表现对比）
- SEO 数据（搜一搜占比）
- 留言数据
- 提炼的执行规则

**更新 `docs/wechat-ops.md`**：
- 在「发布节奏」section 追加 `**数据验证**` 段落
- 在「互动引导」section 追加 `**数据验证**` 段落
- 在「文章末尾关注引导」的系列化部分追加回读数据

**更新 `docs/article-title-seo.md`**：
- 在「反面示例 → 正面示例」后追加标题表现数据表
- 记录已验证有效的标题公式和无效的标题风格

**更新 `AGENTS.md`**：
- 引用最新的 `docs/wechat-data-insights.md`

**更新热门文章列表（每次审计必做）**：
- 从 `docs/wechat-data-audit-log.json` 聚合各文章历史最高阅读量（跨快照取 max）
- **过滤贴图**（`item_show_type=8`，优先参考 `branding/style-corpus/publish-data*.json`；若标题在 publish-data 中缺失（新文 08-12 后的高维、严重过拟合等），回退到 `branding/style-corpus/tietu-corpus-summary.json` 的贴图清单：命中则判 `8`，未命中则暂判 `0`（文章）。`严重过拟合的Deepseek，和魔幻的价格` 在 08-18 人读版已明确为贴图，需按 `8` 过滤）
- 按阅读量降序取前 5 篇文章，同步更新 `content/navigation/menu-config.md` 的「热门文章」表和 `docs/wechat-menu.md`
- 文章链接缺失时从 `branding/style-corpus/publish-data*.json` 的 `content_url` 提取，仍缺失则从 `branding/style-corpus/wechat-published-index.json` 提取，再缺失则向作者索要
- 账号菜单子菜单数受限时（当前仅支持 2 个），文档维护完整前 5，实际配置取前 N 篇

---

## 关键参考

- 公众号后台地址：`https://mp.weixin.qq.com/`
- 内容分析页面：`https://mp.weixin.qq.com/misc/appmsganalysis?action=report&type=daily_v2&lang=zh_CN`
- 用户分析页面：`https://mp.weixin.qq.com/misc/useranalysis?lang=zh_CN`
- 流量主概览页（需通过菜单进入，禁止直接 URL）：hover「收入变现」→「流量主」→ URL 形如 `.../cgi-bin/frame?t=ad_system/common_frame&t1=publisher/publisher_overview...`
- 流量主数据统计页（日报表）：概览页点击「数据统计」→ URL 形如 `...&t1=publisher/publisher_report&pos=1...`
- Cookie 注入方式详见 `wechat-stats` skill

## 常见问题

**Q: 内容分析页面显示"请重新登录"**
A: 从首页通过导航菜单点进去，不要直接 URL 访问。直接访问 analytics 页面会触发额外鉴权。

**Q: 导航栏点击没反应**
A: 先执行 `snapshot -i` 获取最新 refs，再从新 snapshot 里找到对应 ref 点击。跨页面导航后 refs 会失效。

**Q: 数据不全（只有近7天）**
A: 默认显示近7天。30天数据通常在页面下方有选择按钮，但不是所有账号权限都支持。

**Q: 流量主页面点击「数据统计」tab 没反应**
A: 用 `querySelector('a[href*="publisher_report"]').click()` 直接点 A 标签，不要点 LI 的 onclick。页面是 iframe 架构，内容在 `#wxadcontainer` 中渲染。

**Q: 「文章收入」和「广告位数据」显示相同数据**
A: 新账号 / 文章数少时正常。文章级收入明细需要足够的文章数和曝光量才会出现单独表格。

**Q: 概览页「昨日收入」和日报表当天合计不一致**
A: 概览页可能含多广告位汇总（留言区 + 底部 + 文中广告等），日报表默认只显示单一广告位数据。**运营决策用概览页累计收入**，**分析趋势用日报表分日分广告位数据**。

**Q: 日报表只显示 4-7 天数据**
A: 默认近 7 天。可通过页面上的日期选择器调整范围。新开通流量主可能只有开通后的数据。

**Q: 为什么 `read` 二维码截图只返回文字描述、看不到图片？**
A: 当前模型不支持视觉输入（`input` 不含 `"image"`），`read` 工具会自动降级到讯飞 Kimi 代理。切换到 `gpt-5.6-luna` 或 `xopkimik26` 等视觉模型即可内联显示。
