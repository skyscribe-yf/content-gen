---
name: wechat-data-audit
description: "Audit WeChat Official Account article data, extract performance metrics, generate insights, and update project documentation with findings. Use when user asks to '检查公众号数据', '分析文章表现', 'wechat audit', '数据复盘', '运营分析', '公众号复盘', '查看文章数据', or after publishing a batch of articles."
---

# WeChat Data Audit

对公众号进行数据审计：采集文章表现数据 + 用户增长数据 → 生成洞察 → 写入项目文档。

**前置依赖**：[wechat-stats](../wechat-stats/SKILL.md) 的 Cookie 注入模式。

---

## 工作流

### Phase 1: Cookie 注入 + 登录

先按 `wechat-stats` 的流程注入 Cookie，确保登录态。

快速步骤：

1. 读取 `.env` 确认有 `WECHAT_COOKIE`
2. 用 `agent_browser` `sessionMode=fresh` 打开 `https://mp.weixin.qq.com/`
3. 通过 CDP 注入 Cookie（用 Node.js 脚本连 DevTools port，调用 `Network.setCookie`，domain 设 `.qq.com`）
4. 导航到 `https://mp.weixin.qq.com/` 验证登录（`window.wx.uin > 0` 即为成功）

### Phase 2: 采集内容分析数据

1. 点击导航栏「数据分析」→「内容分析」
2. 等待页面加载完成后，用 `agent_browser get text body` 获取全文
3. 从文本中解析以下数据：

**数据概况**：
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

---

## 关键参考

- 公众号后台地址：`https://mp.weixin.qq.com/`
- 内容分析页面：`https://mp.weixin.qq.com/misc/appmsganalysis?action=report&type=daily_v2&lang=zh_CN`
- 用户分析页面：`https://mp.weixin.qq.com/misc/useranalysis?lang=zh_CN`
- Cookie 注入方式详见 `wechat-stats` skill

## 常见问题

**Q: 内容分析页面显示"请重新登录"**
A: 从首页通过导航菜单点进去，不要直接 URL 访问。直接访问 analytics 页面会触发额外鉴权。

**Q: 导航栏点击没反应**
A: 先执行 `snapshot -i` 获取最新 refs，再从新 snapshot 里找到对应 ref 点击。跨页面导航后 refs 会失效。

**Q: 数据不全（只有近7天）**
A: 默认显示近7天。30天数据通常在页面下方有选择按钮，但不是所有账号权限都支持。
