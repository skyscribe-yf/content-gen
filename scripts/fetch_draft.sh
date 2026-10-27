#!/usr/bin/bash
# 拉取草稿箱中指定 media_id 的正文（作者后台改稿回拉同步用）
# 用法: scripts/fetch_draft.sh <media_id> [输出目录]
# 产物: <输出目录，默认 /tmp>/draft-found.json（原始 API 响应）
#       <输出目录>/draft-content.html（正文 HTML，含 mdnice 样式与 SVG 公式）
# 依赖: vps-us SSH SOCKS5 隧道（本机出口 IP 常不在微信白名单，2026-10-24 复验；
#       取 token 失败 40164 时检查 ~/.ssh/config 的 vps-us 是否可达）
set -u
MID="${1:?用法: $0 <media_id> [输出目录]}"
OUTDIR="${2:-/tmp}"
mkdir -p "$OUTDIR"
cd "$(dirname "$0")/.." || exit 1

ENV=.baoyu-skills/.env
APPID=$(grep -m1 '^WECHAT_APP_ID=' "$ENV" | cut -d= -f2- | tr -d '"'"'"' \r')
SECRET=$(grep -m1 '^WECHAT_APP_SECRET=' "$ENV" | cut -d= -f2- | tr -d '"'"'"' \r')
C="env -u http_proxy -u https_proxy curl -s -m 30 --socks5-hostname 127.0.0.1:1080"

ssh -N -D 1080 vps-us >/dev/null 2>&1 &
TP=$!
trap 'kill $TP 2>/dev/null' EXIT
sleep 3

TOK=$($C "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=$APPID&secret=$SECRET")
TOKEN=$(printf '%s' "$TOK" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
if [ -z "$TOKEN" ]; then echo "[fetch] NO TOKEN: $(echo "$TOK" | head -c 200)"; exit 1; fi
echo "[fetch] token ok"

FOUND=""
for OFF in 0 20 40 60; do
  RESP=$($C -X POST "https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=$TOKEN" \
    -H 'Content-Type: application/json' -d "{\"offset\":$OFF,\"count\":20,\"no_content\":0}")
  if printf '%s' "$RESP" | grep -q "$MID"; then
    printf '%s' "$RESP" > "$OUTDIR/draft-found.json"
    echo "[fetch] FOUND at offset $OFF -> $OUTDIR/draft-found.json"
    FOUND=1
    break
  fi
  N=$(printf '%s' "$RESP" | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('item',[]) or []))" 2>/dev/null || echo 0)
  echo "[fetch] offset=$OFF items=$N"
  [ "$N" = "0" ] && break
done

if [ -z "$FOUND" ]; then
  echo "[fetch] 草稿箱未命中，试 freepublish（定时群发）"
  RESP=$($C -X POST "https://api.weixin.qq.com/cgi-bin/freepublish/batchget?access_token=$TOKEN" \
    -H 'Content-Type: application/json' -d '{"offset":0,"count":5}')
  printf '%s' "$RESP" > "$OUTDIR/freepublish.json"
  printf '%s' "$RESP" | grep -q "$MID" && echo "[fetch] FOUND in freepublish -> $OUTDIR/freepublish.json" || echo "[fetch] NOT FOUND"
  exit 1
fi

python3 - "$OUTDIR/draft-found.json" "$MID" "$OUTDIR/draft-content.html" <<'PYEOF'
import sys, json
src, mid, dst = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(src))
for it in d.get('item') or []:
    if it.get('media_id') == mid:
        for a in (it.get('content') or {}).get('news_item') or []:
            open(dst, 'w').write(a.get('content', ''))
            print('[fetch] content saved ->', dst, '| title:', a.get('title', '')[:40])
            break
        break
PYEOF
