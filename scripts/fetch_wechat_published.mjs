#!/usr/bin/env node
// fetch_wechat_published.mjs — 抓取公众号「发表记录」全部条目（文章/贴图）索引
//
// 依赖：agent-browser 正在运行且 mp.weixin.qq.com 已登录
// 输出：branding/style-corpus/wechat-published-index.json
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'branding', 'style-corpus', 'wechat-published-index.json');
const WS = globalThis.WebSocket;

function findDevTools() {
  const dirs = fs.readdirSync('/tmp')
    .filter(d => d.startsWith('agent-browser-chrome-') && fs.existsSync(`/tmp/${d}/DevToolsActivePort`))
    .map(d => ({ d, m: fs.statSync(`/tmp/${d}/DevToolsActivePort`).mtimeMs }))
    .sort((a, b) => b.m - a.m);
  if (!dirs.length) throw new Error('未找到 agent-browser Chrome DevToolsActivePort');
  const port = fs.readFileSync(`/tmp/${dirs[0].d}/DevToolsActivePort`, 'utf8').split('\n')[0].trim();
  return { port, dir: dirs[0].d };
}

async function connect(port) {
  const tabs = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const tab = tabs.find(t => t.type === 'page' && /weixin\.qq\.com/.test(t.url || '')) || tabs.find(t => t.type === 'page');
  if (!tab) throw new Error(`未找到页面 tab: ${tabs.map(t => t.url).join(' | ')}`);
  const ws = new WS(tab.webSocketDebuggerUrl);
  ws.binaryType = 'arraybuffer';
  let id = 0;
  const pending = new Map();
  ws.onmessage = async ev => {
    let raw = ev.data;
    if (raw instanceof ArrayBuffer) raw = Buffer.from(raw).toString('utf8');
    else if (raw && typeof raw === 'object' && raw.text) raw = await raw.text();
    const msg = JSON.parse(raw);
    if (msg.id && pending.has(msg.id)) {
      const { res, rej } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? rej(new Error(msg.error.message)) : res(msg.result);
    }
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const mid = ++id;
    pending.set(mid, { res, rej });
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
  await new Promise(r => { ws.onopen = () => r(); });
  return { ws, send };
}

async function evalJS(send, expression) {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const { port } = findDevTools();
  console.log(`[fetch-wechat-published] CDP port ${port}`);
  const { ws, send } = await connect(port);
  const token = await evalJS(send, `(location.href.match(/token=(\\d+)/)||[])[1] || ''`);
  if (!token) throw new Error('当前页面无 token，请先打开 mp.weixin.qq.com 后台');

  const seen = new Map();
  for (let begin = 0; begin < 200; begin += 20) {
    const url = `https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&begin=${begin}&count=100&token=${token}&lang=zh_CN`;
    await evalJS(send, `location.href = ${JSON.stringify(url)}; 'ok'`);
    await sleep(3500);
    const items = await evalJS(send, `(()=>{
      const out=[];
      document.querySelectorAll('a').forEach(a=>{
        const h=a.href||'';
        if(h.includes('/s/')) out.push({title:(a.innerText||'').trim().replace(/\\s+/g,' '), url:h});
      });
      return out;
    })()`);
    if (!items || !items.length) break;
    let added = 0;
    for (const it of items) {
      if (!seen.has(it.url)) { seen.set(it.url, it); added++; }
    }
    console.log(`[fetch-wechat-published] begin=${begin} items=${items.length} new=${added} total=${seen.size}`);
    if (added === 0) break;
  }
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify([...seen.values()], null, 2) + '\n');
  console.log(`[fetch-wechat-published] saved ${seen.size} items -> ${OUT}`);
  ws.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
