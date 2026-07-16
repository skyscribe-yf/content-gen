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
function findDevTools() {
  const dirs = fs.readdirSync('/tmp')
    .filter(d => d.startsWith('agent-browser-chrome-'))
    .map(d => ({ d, p: `/tmp/${d}/DevToolsActivePort`, m: 0 }))
    .filter(x => fs.existsSync(x.p));
  if (!dirs.length) throw new Error('未找到 /tmp/agent-browser-chrome-*/DevToolsActivePort，请先 agent_browser open mp.weixin.qq.com');
  // 取最新修改的目录
  for (const x of dirs) try { x.m = fs.statSync(x.p).mtimeMs; } catch {}
  dirs.sort((a, b) => b.m - a.m);
  const port = fs.readFileSync(dirs[0].p, 'utf8').split('\n')[0].trim();
  return { port, dir: dirs[0].d };
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
  const { port, dir } = findDevTools();
  const tab = await findWeixinTab(port);
  console.log(`[inject] Chrome dir: ${dir}`);
  console.log(`[inject] page tab: ${tab.url.slice(0, 60)}`);
  const { ws, send } = connect(tab.webSocketDebuggerUrl);
  await new Promise(r => { ws.onopen = () => r(); });
  await send('Network.enable');
  let ok = 0, fail = 0;
  for (const c of cookies) {
    try { const r = await send('Network.setCookie', c); (r && r.success) ? ok++ : fail++; }
    catch { fail++; }
  }
  ws.close();
  console.log(JSON.stringify({ injected: ok, failed: fail, total: cookies.length }));
  console.log('[inject] 接下来 agent_browser navigate https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN 验证');
}

async function exportCookies() {
  const { port, dir } = findDevTools();
  const tab = await findWeixinTab(port);
  console.log(`[export] Chrome dir: ${dir}`);
  console.log(`[export] page tab: ${tab.url.slice(0, 60)}`);
  const { ws, send } = connect(tab.webSocketDebuggerUrl);
  await new Promise(r => { ws.onopen = () => r(); });
  const r = await send('Network.getAllCookies');
  ws.close();
  const keep = r.cookies.filter(c => c.domain.includes('weixin') || c.domain.includes('qq.com'));
  // 去重：同名保留最后一个
  const map = new Map();
  for (const c of keep) map.set(c.name, c);
  const cookieStr = writeEnvCookie([...map.values()]);
  console.log(JSON.stringify({ saved: cookieStr.length, cookieCount: map.size, names: [...map.keys()] }));
  console.log(`[export] 已写回 ${ENV_PATH}`);
}

async function status() {
  const { port, dir } = findDevTools();
  const tab = await findWeixinTab(port);
  const { ws, send } = connect(tab.webSocketDebuggerUrl);
  await new Promise(r => { ws.onopen = () => r(); });
  const res = await send('Runtime.evaluate', {
    expression: `JSON.stringify({ uin: window.wx && window.wx.uin, url: location.href, hasMenu: !!document.querySelector('.weui-desktop-menu'), bodyStart: document.body.innerText.slice(0,60) })`,
    returnByValue: true,
  });
  ws.close();
  const v = JSON.parse(res.result.value);
  console.log(JSON.stringify({ ...v, loggedIn: Number(v.uin) > 0, dir }, null, 2));
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