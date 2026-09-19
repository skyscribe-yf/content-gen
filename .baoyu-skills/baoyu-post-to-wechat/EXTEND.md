default_theme: grace
default_color: blue
default_publish_method: remote-api
remote_publish_host: vps-us
remote_publish_user: root
default_author: 数解AI
need_open_comment: 1
only_fans_can_comment: 0

# ---------------------------------------------------------------------------
# 紧凑排版（2026-09-18 作者要求：两侧留白收紧）
# ---------------------------------------------------------------------------
# md-to-wechat.ts 里 compactWechatLayout() 会收掉 mdnice scienceBlue 主题
# 自带的左右留白：外层 section `padding: 0 10px` → 0，段落 `margin: 10px 10px`
# → `10px 0`，h2 右边距归零。实测 390px 视口下正文宽度从 334px 恢复到 374px。
# 若要回退旧版式，删除该函数调用即可；改主题后需复核正则是否仍匹配。

# ---------------------------------------------------------------------------
# 发布通道口径（2026-09-18 更新，取代 2026-09-15 版）
# ---------------------------------------------------------------------------
# 1. **默认走 remote-api（vps-us）**——本机出口是动态 IP，白名单经常失效；
#    vps-us（81.31.232.134）出口在白名单，2026-09-18 实测存稿成功。
#    用法：`bun .agents/skills/baoyu-post-to-wechat/scripts/wechat-api.ts <file>
#          --theme grace --color blue`（EXTEND 里 default_publish_method:
#          remote-api + remote_publish_host: vps-us 会自动启用隧道）。
# 2. 本机直连（`--no-remote` / 把 default_publish_method 改回 api）作为备选：
#    前提是当前真实出口 IP 在白名单里。
#    - 查真实出口：`env -u http_proxy -u https_proxy curl -4 -s ifconfig.me`
#    - 2026-09-18 实测出口 = 112.10.197.224（2026-09-15 曾为 112.10.196.237，
#      动态变化；40164 报错里给出的 IP 就是要加白名单的那个，照抄即可）
#    - shell 的 http_proxy/https_proxy=127.0.0.1:2083 对微信域名是直连规则，
#      走代理不改变微信看到的出口 IP，别指望用代理绕过白名单。
# 3. `vps`（46.20.109.156）已失联（2026-09-18 SSH 22 端口超时），不要再指向它；
#    远端主机用 `vps-us`（~/.ssh/config 已配置，root，密钥登录）。
# 4. remote 隧道报错时先 `ssh vps-us 'curl -s -m 8 -o /dev/null -w "%{http_code}" \
#    https://api.weixin.qq.com/cgi-bin/getcallbackip'` 验证 VPS 出网与白名单。
