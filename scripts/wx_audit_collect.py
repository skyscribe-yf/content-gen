#!/usr/bin/env python
"""WeChat backend audit collector — CDP against the live-profile browser (port 9335).

Session source: a *copy* of the user's main Chrome profile (`/tmp/wx-live-profile`),
so Chrome itself decrypts the v11 libsecret cookies. Falls back to nothing — if the
session dies the user must re-scan the QR via `scripts/wx_audit_browser.py`.

Every collector returns a dict; `main` dumps them all to /tmp/audit-raw.json.
"""

import json
import re
import sys
import time

PORT = 9335
TOKEN = "1451619008"


def connect():
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    b = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}", timeout=20000)
    return pw, b, b.contexts[0]


def open_page(ctx, url, wait=9000):
    pg = ctx.new_page()
    pg.goto(url, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(wait)
    return pg


def check_login(pg):
    return bool(pg.evaluate("() => (window.wx && window.wx.uin) || 0"))


# ---------------------------------------------------------------- 内容分析
def collect_content(ctx):
    out = {"url": None, "error": None}
    pg = open_page(
        ctx,
        f"https://mp.weixin.qq.com/misc/appmsganalysis?action=report&type=daily_v2"
        f"&lang=zh_CN&token={TOKEN}",
    )
    try:
        out["url"] = pg.url
        out["uin"] = pg.evaluate("() => (window.wx && window.wx.uin) || 0")
        # ---- 数据概况 (yesterday cards)
        cards = pg.evaluate(
            """() => [...document.querySelectorAll('.yesterday-all__item')].map(it=>({
                 title: it.querySelector('.yesterday-all__title')?.innerText.trim(),
                 count: it.querySelector('.yesterday-all__count')?.innerText.trim(),
                 deltas: [...it.querySelectorAll('.yesterday-all__content_list')].map(c=>c.innerText.trim().replace(/\\s+/g,''))
               }))"""
        )
        out["overview"] = cards
        # ---- 流量来源 (30d pie)
        out["sources"] = pg.evaluate(
            """() => {
                 const el=[...document.querySelectorAll('*')].find(e=>/阅读总人数/.test(e.textContent) && e.querySelector?.('svg'));
                 const t=document.body.innerText;
                 const m=t.match(/推荐\\s*([\\d.]+)%[\\s\\S]*?公众号消息\\s*([\\d.]+)%[\\s\\S]*?聊天会话\\s*([\\d.]+)%[\\s\\S]*?其它\\s*([\\d.]+)%[\\s\\S]*?公众号主页\\s*([\\d.]+)%[\\s\\S]*?搜一搜\\s*([\\d.]+)%[\\s\\S]*?朋友圈\\s*([\\d.]+)%/);
                 const tot=t.match(/阅读总人数：([\\d,]+)人/);
                 return {total30d: tot? tot[1]:null,
                         pct: m? {推荐:+m[1],公众号消息:+m[2],聊天会话:+m[3],其它:+m[4],公众号主页:+m[5],搜一搜:+m[6],朋友圈:+m[7]} : null};
               }"""
        )
        # ---- Top10 table (30d cumulative)
        rows = pg.evaluate(
            """() => {
                 const t=[...document.querySelectorAll('table')].find(x=>/内容标题/.test(x.innerText) && x.querySelectorAll('tbody tr').length>3);
                 if(!t) return [];
                 return [...t.querySelectorAll('tbody tr')].map(tr=>{
                   const tds=[...tr.querySelectorAll('td')].map(td=>td.innerText.trim().replace(/\\s+/g,' '));
                   return tds;
                 }).filter(td=>td.length>=2 && !/^x/.test(td[0]));
               }"""
        )
        arts = []
        for td in rows:
            first = td[0]
            m = re.search(r"发表时间：([\d/]+)", first)
            title = first.split("发表时间")[0].strip()
            reads = td[1] if len(td) > 1 else None
            share = td[2] if len(td) > 2 else None
            if not title or title == "x":
                continue
            arts.append({"title": title, "date": m.group(1) if m else None,
                         "reads30d": reads, "share30d": share})
        # dedupe (outer+inner rows)
        seen, ded = set(), []
        for a in arts:
            if a["title"] in seen:
                continue
            seen.add(a["title"])
            ded.append(a)
        out["top10_30d"] = ded[:10]
        # ---- download link for daily sources
        out["tendency_link"] = pg.evaluate(
            "() => { const a=document.querySelector('a[href*=download_summary_tendency]'); return a? a.href : null; }"
        )
    finally:
        pg.close()
    return out


# ---------------------------------------------------------------- 首页近期发表
def collect_recent_publish(ctx, n=12):
    pg = open_page(ctx, f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token={TOKEN}", wait=11000)
    try:
        data = pg.evaluate(
            """() => {
                 const tbls=[...document.querySelectorAll('table')].filter(t=>t.querySelectorAll('tbody tr').length>0);
                 let best=null;
                 for(const t of tbls){ const h=t.innerText||''; if(/流形假设|已发表|全部发表记录|近期发表/.test(h)) { best=t; break; } }
                 if(!best) return {err:'no recent table', n: tbls.length};
                 return {head:[...best.querySelectorAll('th')].map(x=>x.innerText.trim().filter(Boolean)),
                         rows:[...best.querySelectorAll('tbody tr')].map(tr=>[...tr.querySelectorAll('td')].map(td=>td.innerText.trim().replace(/\\s+/g,' ')))};
               }"""
        )
        return data
    finally:
        pg.close()


# ---------------------------------------------------------------- 用户分析
def collect_users(ctx):
    pg = open_page(
        ctx,
        f"https://mp.weixin.qq.com/misc/useranalysis?action=useranalysis&lang=zh_CN&token={TOKEN}",
        wait=10000,
    )
    try:
        return {
            "url": pg.url,
            "text": pg.evaluate("() => document.body.innerText")[:6000],
        }
    finally:
        pg.close()


# ---------------------------------------------------------------- 流量主
def collect_income(ctx):
    pg = open_page(ctx, f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token={TOKEN}", wait=10000)
    try:
        # enter 收入变现 -> 流量主 via menu click (iframe arch, no direct URL nav)
        pg.evaluate(
            """() => {
                 const el=[...document.querySelectorAll('*')].find(e=>e.textContent.trim()==='收入变现' && e.children.length===0);
                 if(!el) return 'no menu';
                 const p=el.closest('li,[role=menuitem],.menu-item')||el.parentElement;
                 p.dispatchEvent(new MouseEvent('mouseenter',{bubbles:true}));
                 return 'hovered';
               }"""
        )
        pg.wait_for_timeout(2500)
        pg.evaluate(
            """() => {
                 const a=[...document.querySelectorAll('a')].find(a=>a.textContent.includes('流量主'));
                 if(a){a.click(); return 'clicked';} return 'no link';
               }"""
        )
        pg.wait_for_timeout(8000)
        frames = [f.url for f in pg.frames]
        body = ""
        for f in pg.frames:
            try:
                t = f.evaluate("() => document.body ? document.body.innerText : ''")
                if t and len(t) > len(body):
                    body = t
            except Exception:
                pass
        return {"url": pg.url, "frames": frames, "text": body[:5000]}
    finally:
        pg.close()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "content"
    pw, b, ctx = connect()
    try:
        fn = {
            "content": collect_content,
            "recent": collect_recent_publish,
            "users": collect_users,
            "income": collect_income,
        }[which]
        print(json.dumps(fn(ctx), ensure_ascii=False, indent=1))
    finally:
        b.close()
        pw.stop()