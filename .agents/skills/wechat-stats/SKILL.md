---
name: wechat-stats
description: "Fetch and analyze WeChat Official Account (微信公众号) statistics. Supports two modes: API mode (requires verified service account) and Browser mode (QR code login, works for all account types). Use when user asks to '查看公众号数据', '分析公众号', 'wechat stats', '公众号后台数据', '运营数据', or '数据分析'."
---

# WeChat Official Account Stats

独立于 baoyu-wechat skills 的公众号数据分析工具。

## 架构说明

微信公众平台（mp.weixin.qq.com）有 **TLS 指纹检测** —— 纯 Python/Node `requests` 携带正确 cookie 也会被识别为非浏览器客户端，返回"请重新登录"（`wx.uin=0`）。

因此无论哪种模式，**数据抓取都必须通过 agent_browser（真实 Chromium）**。Cookie 的作用是**跳过首次扫码**，不能替代浏览器。

## 模式选择

| 模式 | 触发条件 | 效果 |
|------|---------|------|
| **Cookie 注入** (推荐) | `.env` 有 `WECHAT_COOKIE` 且未过期 | 免扫码，自动登录 |
| **Browser 扫码** | Cookie 不存在或已过期 | 用户扫一次，然后导出 cookie |
| API | 极少使用，权限受限 | 不需要浏览器 |

默认先尝试 Cookie 注入，失败降级到扫码。

---

## Cookie 模式工作流

### Step 1: 读取 .env 中的 cookie

```bash
grep WECHAT_COOKIE /home/skyscribe/srcs/content-gen/.env
```

### Step 2: Cookie 注入（通过 CDP）

因为 `document.cookie` 无法设置 httpOnly cookie，需要用 CDP：

```
agent_browser: open https://mp.weixin.qq.com/
agent_browser: eval --stdin
  // 将 .env 中的 cookie 通过 CDP 注入
  (async () => {
    const { CDP } = await import('chrome-remote-interface');
    const client = await CDP({ port: 42089 }); // 动态获取端口
    const { Network } = client;
    const cookies = process.env.WECHAT_COOKIE.split('; ').map(c => {
      const [name, ...rest] = c.split('=');
      return { name, value: rest.join('='), domain: '.qq.com', path: '/', httpOnly: true, secure: true };
    });
    for (const c of cookies) await Network.setCookie(c);
    await client.close();
    return 'injected ' + cookies.length;
  })()
```

**更简洁的方式**：如果浏览器已经用 `--remote-debugging-port` 启动，直接用 agent_browser 的 `batch` 模式：

```bash
# 先用 curl 注入 cookie
export PORT=$(cat /tmp/agent-browser-chrome-*/DevToolsActivePort 2>/dev/null | head -1)
WECHAT_COOKIE=$(grep WECHAT_COOKIE .env | cut -d= -f2-)
# 拆成 JSON 后用 CDP 注入
```

### Step 3: 验证登录态

```
agent_browser: navigate https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN
agent_browser: eval --stdin
  JSON.stringify({
    uin: window.wx?.uin,
    url: location.href,
    hasMenu: !!document.querySelector('#menu'),
    text: document.body.innerText.substring(0, 100)
  })
```

**判断**：
- uin > 0 且有 menu → Cookie 有效，继续
- uin=0 或跳转 loginpage → Cookie 失效，降级扫码

### Step 4-6: 数据抓取（与 Browser 模式共用）

见下方 "数据抓取" 章节。

### Step 7: 抓取成功后 → 导出并保存 cookie（如果尚未保存）

参考 "Cookie 导出" 章节。

---

## Browser 模式工作流

当 `.env` 中无 cookie，或 cookie 已过期时。

### Step 1: 打开登录页

```
sessionMode: fresh (或 auto)
args: open https://mp.weixin.qq.com/
```

### Step 2: 截图二维码（不依赖模型视觉能力，2026-08-29 修正）

二维码是给用户扫的，模型不需要「看」它——**截图保存到文件即可，任何模型都能走此流程**：

```
agent_browser: screenshot /tmp/wechat-qr.png
```

- 若模型支持视觉（`input` 含 `"image"`）：`read /tmp/wechat-qr.png` → Pi TUI 内联渲染，用户直接扫码
- 若模型不支持视觉：把截图路径 `/tmp/wechat-qr.png` 告诉用户，**用户自己打开文件扫码**（无需换模型、无需手动刷 Cookie）

**注意**：TLS 指纹绑定意味着用户必须在同一个 VPS 浏览器环境扫码。你从本地浏览器拷贝的 cookie 在 VPS 上无效。

### Step 3: 等待登录确认

**不要轮询**。告知用户扫码后回复确认，然后用 `eval` 验证登录态：

```
agent_browser: eval --stdin
  JSON.stringify({
    href: location.href,
    uin: window.wx?.uin,
    loggedIn: location.href.includes('/cgi-bin/home')
  })
```

`uin > 0` 且 `loggedIn: true` → 登录成功。仍在 `/cgi-bin/loginpage` → 让用户重扫。

### Step 4: 立即导出 cookie（扫码成功后必做）

**这步是关键** — 扫码成功后立刻保存 cookie，以后就不用再扫。

```
agent_browser: eval --stdin
  // 通过 CDP 获取完整 cookie（含 httpOnly）
  // 方法1: 如果有 CDP bridge
  (async () => {
    const resp = await fetch('http://localhost:42089/json');
    const tabs = await resp.json();
    // 找到 mp.weixin.qq.com tab 的 ws URL
    const tab = tabs.find(t => t.url.includes('mp.weixin.qq.com'));
    if (!tab) return 'NO_TAB';
    const ws = new WebSocket(tab.webSocketDebuggerUrl);
    return new Promise(resolve => {
      ws.onopen = () => {
        ws.send(JSON.stringify({id:1, method:'Network.getAllCookies'}));
      };
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.id === 1) {
          const relevant = data.result.cookies.filter(c =>
            c.domain.includes('weixin') || c.domain.includes('qq.com')
          );
          resolve(JSON.stringify(relevant));
          ws.close();
        }
      };
    });
  })()
```

### Step 5: 写入 .env

解析上面返回的 cookie 数组，生成 `WECHAT_COOKIE=key1=val1; key2=val2; ...` 写入 `.env`。

脚本辅助：

```bash
# 先把 CDP 输出保存为 cookies.json
python scripts/extract_wechat_cookies.py --cookie-json /tmp/cdp-cookies.json --auto-save-env
```

**提示用户**：
```
✅ Cookie 已保存到 .env。下次开始可以免扫码自动登录。
   有效期约 7-30 天，过期时需要重新扫码。
```

### Step 6-8: 继续数据抓取

---

## Cookie 导出方法（汇总）

从 VPS 浏览器导出有效 cookie 有三种方式：

### 方式 1: CDP getAllCookie（推荐，能获取 httpOnly）

```javascript
// 在 agent_browser eval --stdin 中执行
(async () => {
  const tabs = await (await fetch('http://localhost:{PORT}/json')).json();
  const tab = tabs.find(t => t.url.includes('mp.weixin.qq.com'));
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  return new Promise(resolve => {
    ws.onopen = () => ws.send(JSON.stringify({id:1, method:'Network.getAllCookies'}));
    ws.onmessage = e => {
      const d = JSON.parse(e.data);
      if (d.id === 1) {
        resolve(JSON.stringify(d.result.cookies.filter(c => 
          c.domain.includes('weixin') || c.domain.includes('qq.com')
        )));
        ws.close();
      }
    };
  });
})()
```

### 方式 2: 直接读 SQLite DB

文件在 `/tmp/agent-browser-chrome-{hash}/Default/Cookies`，但 value 被 AES 加密，
不足以直接还原（需要 Chrome 密钥环中的解密 key）。

### 方式 3: 从 Chrome DevTools 里用 Network 面板

手动从浏览器 Network 面板的 Request Headers 复制 Cookie 行。

---

## 最小 Cookie 集合

**结论**：最小 cookie 依赖于浏览器实现对 TLS/指纹的兼容性，推荐保存**完整 cookie**。

从你的 cookie 中，以下是最可能可以裁剪的：

| 类别 | Cookie | 安全可省 | 原因 |
|------|--------|---------|------|
| 统计 | `_clck`, `_clsk`, `ua_id`, `xid`, `pgv_pvid` | ✅ | Clarity/分析统计 |
| 认证核心 | `data_ticket`, `slave_sid`, `slave_user` | ❌ | 会话标识 |
| 业务 | `bizuin`, `data_bizuin`, `slave_bizuin` | ❌ | 公众号 ID |
| 其他 | `mm_lang`, `uuid`, `rand_info`, `wxuin` | ⚠️ | 大概率可省但需逐一验证 |

**风险**：由于 TLS 指纹检测，纯脚本无法有效做 cookie 最小化测试。建议在**浏览器内**逐一移除 cookie 来验证自动化。

---

## 数据抓取（Cookie/Browser 共用）

### Step 4: 抓取内容分析数据

```
agent_browser: navigate https://mp.weixin.qq.com/cgi-bin/appmsganalysis?action=all&begin_date=YYYY-MM-DD&end_date=YYYY-MM-DD&lang=zh_CN
agent_browser: snapshot -i
agent_browser: get text body
```

保存输出到 `/tmp/wechat-content-analysis.txt`。

### Step 5: 抓取用户分析数据

```
agent_browser: navigate 用户分析页面
agent_browser: get text body
```

保存到 `/tmp/wechat-user-analysis.txt`。

### Step 6: 解析数据

```bash
python scripts/parse_wechat_stats.py /tmp/wechat-content-analysis.txt /tmp/wechat-user-analysis.txt
```

### Step 7: 输出分析报告

根据解析结果生成结构化报告（见 `templates/report.md`）。

---

## API 模式

申请了认证的公众号作为备选：

```bash
python scripts/wechat_stats.py            # 默认近7天
python scripts/wechat_stats.py --days 30  # 近30天
python scripts/wechat_stats.py --json     # JSON 输出
```

API 权限说明：订阅号大部分 datacube API 不可用。

---

## 文件结构

```
wechat-stats/
├── SKILL.md                          # 本文件
├── scripts/
│   ├── wechat_stats.py               # API 模式脚本
│   ├── parse_wechat_stats.py         # 浏览器数据解析脚本
│   └── extract_wechat_cookies.py     # Cookie 提取脚本
└── templates/
    └── report.md                     # 分析报告模板
```
