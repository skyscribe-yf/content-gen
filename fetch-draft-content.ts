// fetch-draft-content.ts — 拉取草稿箱指定文章完整内容（临时工具）
import { loadCredentials } from "./.agents/skills/baoyu-post-to-wechat/scripts/wechat-extend-config.ts";

const TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token";
const DRAFT_LIST_URL = "https://api.weixin.qq.com/cgi-bin/draft/batchget";

const creds = loadCredentials();
const tokenRes = await fetch(`${TOKEN_URL}?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`);
const tokenData = await tokenRes.json();
if (!tokenData.access_token) throw new Error(`token error: ${JSON.stringify(tokenData)}`);
const token = tokenData.access_token;

const listRes = await fetch(`${DRAFT_LIST_URL}?access_token=${token}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ offset: 0, count: 20, no_content: 0 }),
});
const listData = await listRes.json();
if (listData.errcode) throw new Error(`list error: ${JSON.stringify(listData)}`);

for (const item of listData.item || []) {
  for (const a of item.content.news_item || []) {
    if (a.title.includes("30 秒视频")) {
      console.log("=== FOUND ===");
      console.log("media_id:", item.media_id);
      console.log("title:", a.title);
      console.log("digest:", a.digest);
      console.log("content:", a.content);
      console.log("thumb_media_id:", a.thumb_media_id);
      console.log("need_open_comment:", a.need_open_comment);
      console.log("only_fans_can_comment:", a.only_fans_can_comment);
    }
  }
}
