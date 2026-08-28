#!/usr/bin/env node
// wechat-cdp-cookie.mjs — 微信公众号 Cookie 的 CDP 注入 / 导出
//
// 用途：配合 wechat-data-audit / wechat-stats skill 的 Phase 1（Cookie 注入登录）。
// 通过裸 WebSocket 连 agent_browser 启动的 Chromium 的 CDP（page target），
//   - inject: 把 .env 的 WECHAT_COOKIE 注入浏览器（httpOnly，document.cookie 设不了）
//   - export: 登录成功后导出最新 cookie 写回 .env（下次免扫码）
//   - status: 检查当前 mp.weixin.qq.com 页面登录态
//
// 前提：agent_browser 已 open https://mp.weixin.qq.com/ （会话活着）。
// Chrome 目录 /tmp/agent-browser-chrome-{hash} 每次启动 hash 不同，自动 glob 定位。
//
// 用法：
//   node scripts/wechat-cdp-cookie.mjs inject    # 注入 .env cookie
//   node scripts/wechat-cdp-cookie.mjs export    # 导出 cookie 写回 .env
//   node scripts/wechat-cdp-cookie.mjs status    # 查登录态 (window.wx.uin)
//
// 依赖：Node ≥ 22（全局 WebSocket）。无第三方包。

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const WS = globalThis.WebSocket;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '..');
const ENV_PATH = path.join(PROJECT_ROOT, '.env');

// ── 定位 agent_browser 的 Chromium DevTools ──
// DevToolsActivePort 可能是已被清理实例的残留：逐个验证 /json/list 可达才算活会话
async function findLiveDevTools() {
  const dirs = fs.readdirSync('/tmp')
    .filter(d => d.startsWith('agent-browser-chrome-'))
    .map(d => ({ d, p: `/tmp/${d}/DevToolsActivePort`, m: 0 }))
    .filter(x => fs.existsSync(x.p));
  for (const x of dirs) try { x.m = fs.statSync(x.p).mtimeMs; } catch {}
  dirs.sort((a, b) => b.m - a.m);
  for (const x of dirs) {
    try {
      const port = fs.readFileSync(x.p, 'utf8').split('\n')[0].trim();
      const ctl = new AbortController();
      setTimeout(() => ctl.abort(), 2000);
      const tabs = await (await fetch(`http://localhost:${port}/json/list`, { signal: ctl.signal })).json();
      if (Array.isArray(tabs)) return { port, dir: x.d };
    } catch {}
  }
  throw new Error('没有活的 agent_browser Chromium（目录均在但 CDP 无响应），请先 agent_browser open https://mp.weixin.qq.com/');
}

async function findWeixinTab(port) {
  const tabs = await (await fetch(`http://localhost:${port}/json/list`)).json();
  const page = tabs.find(t => t.type === 'page' && /weixin\.qq\.com/.test(t.url || ''))
    || tabs.find(t => t.type === 'page');
  if (!page) throw new Error(`未找到 weixin page tab，现有 tabs: ${tabs.map(t => t.type + ':' + (t.url || '').slice(0, 50)).join(' | ')}`);
  return page;
}

function connect(wsUrl) {
  const ws = new WS(wsUrl);
  ws.binaryType = 'arraybuffer';
  let id = 0; const pending = new Map();
  ws.onmessage = async (ev) => {
    let raw = ev.data;
    if (raw instanceof ArrayBuffer) raw = Buffer.from(raw).toString('utf8');
    else if (raw && typeof raw === 'object' && raw.text) raw = await raw.text();
    const m = JSON.parse(raw);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id); pending.delete(m.id);
      m.error ? rej(new Error(m.error.message)) : res(m.result);
    }
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const mid = ++id; pending.set(mid, { res, rej });
    ws.send(JSON.stringify({ id: mid, method, params }));
    // CDP 命令 10s 无响应视为死会话（页面被杀 / target 失效），避免整条命令无限挂起
    setTimeout(() => {
      if (pending.has(mid)) { pending.delete(mid); rej(new Error(`CDP ${method} 10s 无响应，浏览器会话可能已失效，请 agent_browser open 重开`)); }
    }, 10000);
  });
  return { ws, send };
}

function readEnvCookie() {
  const env = fs.readFileSync(ENV_PATH, 'utf8');
  const line = env.split('\n').find(l => l.startsWith('WECHAT_COOKIE='));
  if (!line) throw new Error(`.env 无 WECHAT_COOKIE= 行: ${ENV_PATH}`);
  return line.replace(/^WECHAT_COOKIE=/, '').trim().replace(/^"|"$/g, '');
}

function parseCookieStr(str) {
  return str.split(';').map(c => {
    const seg = c.trim(); if (!seg) return null;
    const idx = seg.indexOf('=');
    return { name: seg.slice(0, idx), value: seg.slice(idx + 1), domain: '.qq.com', path: '/', httpOnly: true, secure: true };
  }).filter(Boolean);
}

function writeEnvCookie(cookies) {
  const env = fs.readFileSync(ENV_PATH, 'utf8');
  const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join('; ');
  let lines = env.split('\n');
  let found = false;
  lines = lines.map(l => {
    if (l.startsWith('WECHAT_COOKIE=')) { found = true; return `WECHAT_COOKIE=${cookieStr}`; }
    return l;
  });
  if (!found) lines.push(`WECHAT_COOKIE=${cookieStr}`);
  fs.writeFileSync(ENV_PATH, lines.join('\n'));
  return cookieStr;
}

// ── 子命令 ──
async function inject() {
  const cookies = parseCookieStr(readEnvCookie());
  const { port, dir } = await findLiveDevTools();
  const tab = await findWeixinTab(port);
  console.log(`[inject] Chrome dir: ${dir}`);
  console.log(`[inject] page tab: ${tab.url.slice(0, 60)}`);
  const { ws, send } = connect(tab.webSocketDebuggerUrl);
  await new Promise(r => { ws.onopen = () => r(); });
  await send('Network.enable');
  // 先清掉 qq.com/weixin 域全部旧 cookie：页面残留的 host-only 旧 sid 与注入的 .qq.com
  // 同名双份时，浏览器把 host-only（path 更精确）排在前面，服务端拿到旧 sid →「请重新登录」。
  const jar = await send('Network.getCookies', { urls: ['https://mp.weixin.qq.com/', 'https://qq.com/'] });
  let cleared = 0;
  for (const c of jar.cookies) {
    try { await send('Network.deleteCookies', { name: c.name, domain: c.domain, path: c.path }); cleared++; } catch {}
  }
  let ok = 0, fail = 0;
  for (const c of cookies) {
    try { const r = await send('Network.setCookie', c); (r && r.success) ? ok++ : fail++; }
    catch { fail++; }
  }
  ws.close();
  console.log(JSON.stringify({ injected: ok, failed: fail, total: cookies.length, clearedOld: cleared }));
  console.log('[inject] 直接跑 status 验证（内部会导航到后台首页做真实服务端验证）');
}

async function exportCookies() {
  const { port, dir } = await findLiveDevTools();
  const tab = await findWeixinTab(port);
  console.log(`[export] Chrome dir: ${dir}`);
  console.log(`[export] page tab: ${tab.url.slice(0, 60)}`);
  const { ws, send } = connect(tab.webSocketDebuggerUrl);
  await new Promise(r => { ws.onopen = () => r(); });
  const r = await send('Network.getAllCookies');
  ws.close();
  const keep = r.cookies.filter(c => c.domain.includes('weixin') || c.domain.includes('qq.com'));
  // 去重：同名可能有多份（旧会话残留 vs 新会话），保留最晚过期的一份
  const map = new Map();
  for (const c of keep) {
    const old = map.get(c.name);
    if (!old || (c.expires || 0) >= (old.expires || 0)) map.set(c.name, c);
  }
  const cookieStr = writeEnvCookie([...map.values()]);
  console.log(JSON.stringify({ saved: cookieStr.length, cookieCount: map.size, names: [...map.keys()] }));
  console.log(`[export] 已写回 ${ENV_PATH}`);
}

async function status() {
  const { port, dir } = await findLiveDevTools();
  const tab = await findWeixinTab(port);
  const { ws, send } = connect(tab.webSocketDebuggerUrl);
  await new Promise((r, rej) => {
    ws.onopen = () => r();
    setTimeout(() => rej(new Error('CDP ws 连接超时，浏览器会话可能已失效，请 agent_browser open 重开')), 5000);
  });
  // 主动导航到后台首页再读登录态：只读当前 DOM 会把注入前停留的
  // 「请重新登录」页误报成未登录（假阴性 → 误判 cookie 过期）。
  await send('Page.enable');
  await send('Page.navigate', { url: 'https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN' });
  const sendT = (method, params, ms = 3000) => Promise.race([
    send(method, params),
    new Promise((_, rej) => setTimeout(() => rej(new Error('timeout: ' + method)), ms)),
  ]);
  let uin = null, url = tab.url, hasMenu = false, bodyStart = '';
  let completeStreak = 0;
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 500));
    try {
      const res = await sendT('Runtime.evaluate', {
        expression: `JSON.stringify({ uin: window.wx && window.wx.uin, url: location.href, hasMenu: !!document.querySelector('.weui-desktop-menu'), ready: document.readyState, bodyStart: document.body ? document.body.innerText.slice(0,60) : '' })`,
        returnByValue: true,
      }, 2000);
      const v = JSON.parse(res.result.value);
      uin = v.uin; url = v.url; hasMenu = v.hasMenu; bodyStart = v.bodyStart;
      // 已登录，或确认被踢到登录/错误页，即可提前结束
      if (Number(v.uin) > 0 || /scanlogin|newlogin|action=login|请重新登录/.test(v.url + v.bodyStart)) break;
      if (v.ready === 'complete') { if (++completeStreak >= 2) break; } else completeStreak = 0;
    } catch {}
  }
  ws.close();
  console.log(JSON.stringify({ uin: String(uin ?? '0'), url, hasMenu, bodyStart, loggedIn: Number(uin) > 0, dir }, null, 2));
}

const cmd = process.argv[2];
try {
  if (cmd === 'inject') await inject();
  else if (cmd === 'export') await exportCookies();
  else if (cmd === 'status') await status();
  else {
    console.error('用法: node scripts/wechat-cdp-cookie.mjs <inject|export|status>');
    process.exit(1);
  }
} catch (e) {
  console.error('错误:', e.message);
  process.exit(1);
}