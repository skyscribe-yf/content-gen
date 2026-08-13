#!/usr/bin/env node
// extract_publish_data.mjs — 从发表记录页脚本提取完整 publish_page 对象并落盘
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const OUT_DIR = path.join(ROOT, 'branding', 'style-corpus');
const WS = globalThis.WebSocket;

function findDevTools() {
  const dirs = fs.readdirSync('/tmp')
    .filter(d => d.startsWith('agent-browser-chrome-') && fs.existsSync(`/tmp/${d}/DevToolsActivePort`))
    .map(d => ({ d, m: fs.statSync(`/tmp/${d}/DevToolsActivePort`).mtimeMs }))
    .sort((a, b) => b.m - a.m);
  if (!dirs.length) throw new Error('未找到 agent-browser Chrome DevToolsActivePort');
  const port = fs.readFileSync(`/tmp/${dirs[0].d}/DevToolsActivePort`, 'utf8').split('\n')[0].trim();
  return { port };
}

async function connect(port) {
  const tabs = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const tab = tabs.find(t => t.type === 'page' && /weixin\.qq\.com/.test(t.url || '')) || tabs.find(t => t.type === 'page');
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

async function main() {
  const { port } = findDevTools();
  const { ws, send } = await connect(port);
  const token = await (async () => {
    const r = await send('Runtime.evaluate', {
      expression: `(location.href.match(/token=(\\d+)/)||[])[1] || ''`,
      returnByValue: true,
    });
    return r.result.value;
  })();
  if (!token) throw new Error('当前页面无 token');

  fs.mkdirSync(OUT_DIR, { recursive: true });
  let total = 0;
  for (let begin = 0; begin < 200; begin += 10) {
    await send('Runtime.evaluate', {
      expression: `location.href = ${JSON.stringify(`https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&begin=${begin}&count=10&token=${token}&lang=zh_CN`)}; 'ok'`,
      returnByValue: true,
    });
    await new Promise(r => setTimeout(r, 3000));
    const scriptR = await send('Runtime.evaluate', {
      expression: `(()=>{let s=''; document.querySelectorAll('script').forEach(x=>{const t=x.textContent||''; if(t.includes('publish_page')) s=t;}); return s;})()`,
      returnByValue: true,
    });
    const scriptText = scriptR.result.value;
    if (!scriptText) break;
    await send('Runtime.evaluate', {
      expression: `eval(${JSON.stringify(scriptText + '\n; window.__PP__ = publish_page;')}); 'ok'`,
      returnByValue: true,
    });
    const jsonR = await send('Runtime.evaluate', {
      expression: 'JSON.stringify(window.__PP__)',
      returnByValue: true,
    });
    const data = JSON.parse(jsonR.result.value);
    const n = Array.isArray(data.publish_list) ? data.publish_list.length : 0;
    total += n;
    fs.writeFileSync(path.join(OUT_DIR, `publish-data-${begin}.json`), JSON.stringify(data, null, 2) + '\n');
    console.log(`[extract] begin=${begin} items=${n} total_count=${data.total_count}`);
    if (!n) break;
  }
  console.log(`[extract] done, ${total} entries -> ${OUT_DIR}/publish-data-*.json`);
  ws.close();
}

main().catch(e => { console.error(e.message); process.exit(1); });
