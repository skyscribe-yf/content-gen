import fs from "node:fs";
import { wechatHttp, type WechatClient } from "./.agents/skills/baoyu-post-to-wechat/scripts/wechat-http.ts";
import { withSshTunnel } from "./.agents/skills/baoyu-post-to-wechat/scripts/wechat-remote-publish.ts";

const MEDIA_ID = "kOcXH4SytIYVIpYksTGfHnBfiGeB3lOS_1cblkvQ3aMiem9uzJa4l96vQiJYRMKJ";

async function fetchAccessToken(appId: string, appSecret: string, client: WechatClient): Promise<string> {
  const url = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${appId}&secret=${appSecret}`;
  const res = await client(url);
  const data = await res.json() as any;
  if (data.errcode) throw new Error(`token err ${data.errcode}: ${data.errmsg}`);
  return data.access_token;
}

async function main() {
  const envPath = ".baoyu-skills/.env";
  let appId="", appSecret="";
  for (const line of fs.readFileSync(envPath,"utf8").split("\n")) {
    const m = line.match(/^\s*WECHAT_APP_ID\s*=\s*(.+)\s*$/);
    if (m) appId = m[1].trim();
    const m2 = line.match(/^\s*WECHAT_APP_SECRET\s*=\s*(.+)\s*$/);
    if (m2) appSecret = m2[1].trim();
  }
  console.log(`appId=${appId.slice(0,6)}...`);
  const remote = { host: "vps", user: "root", port: 22 };
  await withSshTunnel(remote as any, async (client) => {
    const token = await fetchAccessToken(appId, appSecret, client);
    console.log(`token ${token.slice(0,12)}...`);
    const getUrl = `https://api.weixin.qq.com/cgi-bin/draft/get?access_token=${token}`;
    let res = await client(getUrl, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({media_id: MEDIA_ID}) });
    let text = await res.text();
    console.log(`get status ${res.status} len ${text.length}`);
    console.log(text.slice(0, 4000));
    fs.writeFileSync("/tmp/draft_get.json", text);
    const batchUrl = `https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=${token}`;
    res = await client(batchUrl, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({offset:0, count:20, no_content:0}) });
    text = await res.text();
    console.log(`batch len ${text.length}`);
    fs.writeFileSync("/tmp/draft_batch.json", text);
    const j = JSON.parse(text);
    for (const it of j.item || []) {
      const news = it.content?.news_item?.[0] || {};
      console.log(`- ${it.media_id} | ${news.title} | update ${new Date((it.update_time||0)*1000).toISOString()}`);
      if (it.media_id === MEDIA_ID) {
        fs.writeFileSync("/tmp/matched.html", news.content);
        console.log(`matched len ${news.content.length}`);
      }
    }
    const target="协方差矩阵怎么看？一维方差拉开就懂了";
    const found = (j.item||[]).find((it:any)=> it.content?.news_item?.[0]?.title===target);
    if (found) {
      console.log(`found by title media_id=${found.media_id}`);
      fs.writeFileSync("/tmp/found.html", found.content.news_item[0].content);
      console.log(`found content len ${found.content.news_item[0].content.length}`);
      if (found.media_id !== MEDIA_ID) {
        console.log(`NOTE: newer media_id differs, web edit created new draft!`);
      }
    }
  });
}
main().catch(e=>{console.error(e);process.exit(1)});
