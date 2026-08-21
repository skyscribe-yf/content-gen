import fs from "node:fs";
import { loadWechatExtendConfig, loadCredentials } from "./.agents/skills/baoyu-post-to-wechat/scripts/wechat-extend-config.ts";
import { wechatHttp, type WechatClient } from "./.agents/skills/baoyu-post-to-wechat/scripts/wechat-http.ts";
import { withSshTunnel, normalizeRemoteConfig } from "./.agents/skills/baoyu-post-to-wechat/scripts/wechat-remote-publish.ts";

const MEDIA_ID = "kOcXH4SytIYVIpYksTGfHnBfiGeB3lOS_1cblkvQ3aMiem9uzJa4l96vQiJYRMKJ";

async function fetchAccessToken(appId: string, appSecret: string, client: WechatClient): Promise<string> {
  const url = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${appId}&secret=${appSecret}`;
  const res = await client(url);
  const data = await res.json() as any;
  if (data.errcode) throw new Error(`token err ${data.errcode}: ${data.errmsg}`);
  return data.access_token;
}

async function main() {
  const extend = await loadWechatExtendConfig(process.cwd());
  const account = await loadCredentials(process.cwd(), extend);
  const useRemote = extend.defaultPublishMethod === "remote-api" || !!extend.remotePublishHost;
  console.log(`[fetch] useRemote=${useRemote} host=${extend.remotePublishHost}`);

  const run = async (c: WechatClient) => {
    const token = await fetchAccessToken(account.appId, account.appSecret, c);
    console.log(`[fetch] token ok ${token.slice(0,12)}...`);
    const getUrl = `https://api.weixin.qq.com/cgi-bin/draft/get?access_token=${token}`;
    console.log(`[fetch] draft/get`);
    let res = await c(getUrl, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({media_id: MEDIA_ID}) });
    let text = await res.text();
    console.log(`draft/get status ${res.status} len ${text.length}`);
    console.log(text.slice(0, 5000));
    fs.writeFileSync("/tmp/draft_get_single.json", text);
    const batchUrl = `https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=${token}`;
    res = await c(batchUrl, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({offset:0, count:20, no_content:0}) });
    text = await res.text();
    console.log(`\nbatchget len ${text.length}`);
    fs.writeFileSync("/tmp/draft_batch.json", text);
    try {
      const j = JSON.parse(text) as any;
      if (j.item) {
        for (const it of j.item) {
          const news = it.content?.news_item?.[0] || {};
          console.log(`- media_id=${it.media_id} title=${news.title}`);
          if (it.media_id === MEDIA_ID) {
            fs.writeFileSync("/tmp/matched_draft.json", JSON.stringify(it, null, 2));
            if (news.content) {
              fs.writeFileSync("/tmp/draft_content.html", news.content);
              console.log("saved html", news.content.length);
            }
          }
        }
        // also find latest with same title
        const targetTitle = "协方差矩阵怎么看？一维方差拉开就懂了";
        const latest = j.item.find((it:any)=> it.content?.news_item?.[0]?.title === targetTitle);
        if (latest && latest.media_id !== MEDIA_ID) {
          console.log(`found newer draft with same title but different media_id=${latest.media_id}`);
          fs.writeFileSync("/tmp/latest_draft.json", JSON.stringify(latest, null, 2));
          fs.writeFileSync("/tmp/latest_content.html", latest.content.news_item[0].content);
        }
      }
    } catch(e){ console.error(e) }
  };

  if (useRemote && extend.remotePublishHost) {
    const remoteConfig = normalizeRemoteConfig({
      host: extend.remotePublishHost!,
      user: extend.remotePublishUser,
      port: extend.remotePublishPort,
      identityFile: extend.remotePublishIdentityFile,
      knownHostsFile: extend.remotePublishKnownHostsFile,
      strictHostKeyChecking: extend.remotePublishStrictHostKeyChecking,
      connectTimeout: extend.remotePublishConnectTimeout,
      proxyJump: extend.remotePublishProxyJump,
    });
    await withSshTunnel(remoteConfig, async (client)=> { await run(client); });
  } else {
    await run(wechatHttp);
  }
}
main().catch(e=>{ console.error(e); process.exit(1) });
