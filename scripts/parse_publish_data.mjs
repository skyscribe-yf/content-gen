#!/usr/bin/env node
// parse_publish_data.mjs — 解析发表记录原始 JSON，归一化为每篇条目清单
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const DATA_DIR = path.join(ROOT, 'branding', 'style-corpus');
const OUT = path.join(DATA_DIR, 'published-items.json');

function unescape(s) {
  return (s || '').replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
}

function parseInfo(raw) {
  try { return JSON.parse(unescape(raw)); } catch { return null; }
}

function main() {
  const files = fs.readdirSync(DATA_DIR).filter(f => /^publish-data-\d+\.json$/.test(f)).sort((a, b) =>
    Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]));
  const items = [];
  const seen = new Set();
  for (const f of files) {
    const data = JSON.parse(fs.readFileSync(path.join(DATA_DIR, f), 'utf8'));
    for (const entry of data.publish_list || []) {
      const info = parseInfo(entry.publish_info);
      if (!info) continue;
      const time = info.sent_info?.time || info.create_time || 0;
      for (const a of info.appmsg_info || []) {
        if (seen.has(a.content_url)) continue;
        seen.add(a.content_url);
        const contentHtml = typeof a.content === 'string' ? a.content : '';
        const text = contentHtml
          .replace(/<br\s*\/?>/gi, '\n').replace(/<\/p>/gi, '\n').replace(/<[^>]+>/g, ' ')
          .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
          .replace(/\s+/g, ' ').trim();
        items.push({
          title: a.title || '',
          url: a.content_url || '',
          appmsgid: a.appmsgid || null,
          publishType: entry.publish_type,
          time,
          date: time ? new Date(time * 1000).toISOString().slice(0, 10) : null,
          digest: a.digest || '',
          showType: a.item_show_type ?? a.show_types?.[0] ?? null,
          hasContent: !!text,
          chars: text.length,
          content: text || null,
          imageCount: (contentHtml.match(/<img/gi) || []).length,
        });
      }
    }
  }
  items.sort((a, b) => b.time - a.time);
  fs.writeFileSync(OUT, JSON.stringify(items, null, 2) + '\n');
  const withText = items.filter(i => i.hasContent);
  console.log(`[parse] total=${items.length} withContent=${withText.length} noContent=${items.length - withText.length}`);
  console.log(`[parse] sample keys: ${Object.keys(items[0] || {}).join(', ')}`);
  console.log(`[parse] saved -> ${OUT}`);
}

main();
