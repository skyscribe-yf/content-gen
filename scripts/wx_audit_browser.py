#!/usr/bin/env python
"""Dedicated WeChat-backend audit browser (CDP on fixed port).

Why a separate browser: the shared `agent-browser-chrome-wx` profile can serve a
"二维码加载失败" placeholder QR (extensions / stale state), while a clean profile
renders the login QR fine. This script boots an isolated persistent context with a
fixed DevTools port so every audit step can `connect_over_cdp` back into the SAME
session (cookies survive between steps, QR only has to be scanned once).

Usage:
  python scripts/wx_audit_browser.py start          # boot + screenshot QR
  python scripts/wx_audit_browser.py status         # login state
  python scripts/wx_audit_browser.py wait [secs]    # block until logged in
  python scripts/wx_audit_browser.py shot <path>    # full-page screenshot
  python scripts/wx_audit_browser.py export         # write cookies back to .env
  python scripts/wx_audit_browser.py stop
"""

import json
import os
import subprocess
import sys
import time

PORT = int(os.environ.get("WX_AUDIT_PORT", "9334"))
PROFILE = "/tmp/wx-audit-profile"
URL = "https://mp.weixin.qq.com/cgi-bin/loginpage?t=wxm2-login&lang=zh_CN"
CHROME = "/opt/google/chrome/chrome"


def _cdp():
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    try:
        b = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}", timeout=20000)
        ctx = b.contexts[0] if b.contexts else b.new_context()
        return pw, b, ctx
    except Exception:
        pw.stop()
        raise


def _page(ctx):
    for p in ctx.pages:
        if "weixin.qq.com" in p.url:
            return p
    return ctx.new_page()


def cmd_start():
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    time.sleep(1)
    subprocess.run(["rm", "-rf", PROFILE], check=False)
    subprocess.Popen(
        [
            CHROME,
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={PROFILE}",
            "--headless=new",
            "--no-sandbox",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=Translate,OptimizationHints",
            "--window-size=1280,900",
            URL,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # wait for devtools
    for _ in range(40):
        time.sleep(0.5)
        try:
            import urllib.request

            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
            break
        except Exception:
            continue
    time.sleep(3)
    return cmd_wait_qr()


def cmd_wait_qr():
    pw, b, ctx = _cdp()
    try:
        pg = _page(ctx)
        for _ in range(20):
            pg.wait_for_timeout(2000)
            if not pg.evaluate("() => document.body.innerText.includes('二维码加载失败')"):
                break
        else:
            return {"qrReady": False}
        el = pg.query_selector("img.login__type__container__scan__qrcode")
        if el:
            el.screenshot(path="/tmp/wechat-qr.png")
        else:
            pg.screenshot(path="/tmp/wechat-qr.png")
        return {"qrReady": True, "path": "/tmp/wechat-qr.png", "url": pg.url}
    finally:
        b.close()
        pw.stop()


def _state(pg):
    try:
        return {
            "uin": pg.evaluate("() => (window.wx && window.wx.uin) || 0"),
            "url": pg.url,
            "hasMenu": pg.evaluate("() => !!document.querySelector('.weui-desktop-menu')"),
        }
    except Exception as e:
        return {"error": str(e)}


def cmd_status():
    pw, b, ctx = _cdp()
    try:
        pg = _page(ctx)
        pg.goto("https://mp.weixin.qq.com/", wait_until="domcontentloaded", timeout=60000)
        for _ in range(7):
            pg.wait_for_timeout(2000)
            s = _state(pg)
            if s.get("uin", 0) and int(s.get("uin") or 0) > 0:
                break
        s = _state(pg)
        s["loggedIn"] = bool(
            (s.get("uin") and int(s["uin"]) > 0)
            or "token=" in s.get("url", "")
            or s.get("hasMenu")
        )
        print(json.dumps(s, ensure_ascii=False))
        return 0 if s["loggedIn"] else 1
    finally:
        b.close()
        pw.stop()


def cmd_wait(maxsecs=300):
    deadline = time.time() + maxsecs
    while time.time() < deadline:
        r = subprocess.run(
            [sys.executable, __file__, "status"], capture_output=True, text=True
        )
        out = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "{}"
        try:
            s = json.loads(out)
        except Exception:
            s = {}
        if s.get("loggedIn"):
            print(json.dumps(s, ensure_ascii=False))
            return 0
        time.sleep(5)
    print(json.dumps({"loggedIn": False, "timeout": True}, ensure_ascii=False))
    return 1


def cmd_shot(path):
    pw, b, ctx = _cdp()
    try:
        pg = _page(ctx)
        pg.screenshot(path=path, full_page=True, timeout=60000)
        print(path)
        return 0
    finally:
        b.close()
        pw.stop()


def cmd_export():
    pw, b, ctx = _cdp()
    try:
        cookies = ctx.cookies()
        keep = [c for c in cookies if "weixin.qq.com" in c.get("domain", "") or "qq.com" in c.get("domain", "")]
        s = "; ".join(f"{c['name']}={c['value']}" for c in keep)
        env_path = ".env"
        lines = open(env_path, encoding="utf-8").read().splitlines()
        out, done = [], False
        for ln in lines:
            if ln.startswith("WECHAT_COOKIE="):
                out.append(f"WECHAT_COOKIE={s}")
                done = True
            else:
                out.append(ln)
        if not done:
            out.append(f"WECHAT_COOKIE={s}")
        open(env_path, "w", encoding="utf-8").write("\n".join(out) + "\n")
        os.chmod(env_path, 0o600)
        print(json.dumps({"exported": len(keep), "path": env_path}, ensure_ascii=False))
        return 0
    finally:
        b.close()
        pw.stop()


def cmd_stop():
    subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
    print("stopped")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    fn = {
        "start": cmd_start,
        "qr": cmd_wait_qr,
        "status": cmd_status,
        "wait": lambda: cmd_wait(int(sys.argv[2]) if len(sys.argv) > 2 else 300),
        "shot": lambda: cmd_shot(sys.argv[2]),
        "export": cmd_export,
        "stop": cmd_stop,
    }.get(cmd, cmd_status)
    sys.exit(fn() or 0)