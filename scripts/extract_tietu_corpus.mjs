#!/usr/bin/env node
// extract_tietu_corpus.mjs — 从发表记录原始 JSON 提取「贴图」类内容及其手敲文本
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const DATA_DIR = path.join(ROOT, 'branding', 'style-corpus');
const OUT_DIR = path.join(DATA_DIR, 'tietu-raw');

function unescape(s) {
  return (s || '').replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
}

function decodePoster(buf) {
  if (!buf) return '';
  try {
    const s = Buffer.from(buf, 'base64').toString('utf8');
    if (!s.trim()) return '';
    try {
      const o = JSON.parse(s);
      const found = [];
      const walk = v => {
        if (typeof v === 'string') found.push(v);
        else if (Array.isArray(v)) v.forEach(walk);
        else if (v && typeof v === 'object') Object.values(v).forEach(walk);
      };
      walk(o);
      return found.join('\n');
    } catch {
      return s.replace(/[^\x20-\x7E\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\n]/g, ' ').replace(/\s+/g, ' ').trim();
    }
  } catch { return ''; }
}

function slugify(s) {
  return (s || 'untitled')
    .replace(/[\\/:*?"<>|#%&\s]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60);
}

function main() {
  const files = fs.readdirSync(DATA_DIR).filter(f => /^publish-data-\d+\.json$/.test(f)).sort((a, b) =>
    Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]));
  const items = [];
  for (const f of files) {
    const data = JSON.parse(fs.readFileSync(path.join(DATA_DIR, f), 'utf8'));
    for (const entry of data.publish_list || []) {
      const info = JSON.parse(unescape(entry.publish_info) || '{}');
      const time = info.sent_info?.time || info.create_time || 0;
      for (const a of info.appmsg_info || []) {
        const showType = a.item_show_type ?? a.show_types?.[0];
        if (showType !== 8) continue;
        const images = (a.share_imageinfo || []).map(img => ({
          cdn: (img.cdn_url || '').replace(/\\\//g, '/'),
          prompt: img.ai_pic_prompt || '',
          picText: img.pic_text || '',
          poster: decodePoster(img.text_poster_data_buf),
        }));
        items.push({
          title: a.title || '',
          url: a.content_url || '',
          time,
          date: time ? new Date(time * 1000).toISOString().slice(0, 10) : null,
          digest: a.digest || '',
          images,
        });
      }
    }
  }
  items.sort((a, b) => b.time - a.time);
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const summary = [];
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const pad = String(i + 1).padStart(2, '0');
    const file = `${pad}-${slugify(it.title)}.md`;
    const lines = [
      `# ${it.title}`,
      '',
      `> url: ${it.url}`,
      `> 发布时间: ${it.date}`,
      '',
      '## 手敲文本（digest）',
      '',
      it.digest || '（无）',
      '',
      '## 图片及文案',
      '',
    ];
    it.images.forEach((img, idx) => {
      lines.push(`### 图 ${idx + 1}`);
      if (img.prompt) lines.push(`- 生成文案（ai_pic_prompt）: ${img.prompt}`);
      if (img.picText) lines.push(`- 图片文字（pic_text）: ${img.picText}`);
      if (img.poster) lines.push(`- 海报文本（text_poster_data_buf）: ${img.poster}`);
      lines.push('');
    });
    fs.writeFileSync(path.join(OUT_DIR, file), lines.join('\n'));
    summary.push({
      index: i + 1,
      date: it.date,
      title: it.title,
      digestChars: it.digest.length,
      imageCount: it.images.length,
      promptCount: it.images.filter(x => x.prompt).length,
      posterChars: it.images.reduce((n, x) => n + x.poster.length, 0),
      file,
    });
  }
  fs.writeFileSync(path.join(DATA_DIR, 'tietu-corpus-summary.json'), JSON.stringify(summary, null, 2) + '\n');
  for (const s of summary) {
    console.log(`[${String(s.index).padStart(2, '0')}] ${s.date} ${s.title.slice(0, 26)} digest=${s.digestChars} imgs=${s.imageCount} prompts=${s.promptCount} poster=${s.posterChars}`);
  }
  console.log(`\n[tietu] ${items.length} items -> ${OUT_DIR}`);
}

main();
