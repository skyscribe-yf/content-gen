// fetch-draft.ts — 拉取草稿箱指定文章内容（临时工具）
import { loadCredentials } from "./.agents/skills/baoyu-post-to-wechat/scripts/wechat-extend-config.ts";

const TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token";
const DRAFT_LIST_URL = "https://api.weixin.qq.com/cgi-bin/draft/batchget";
const DRAFT_GET_URL = "https://api.weixin.qq.com/cgi-bin/draft/get";

const creds = loadCredentials();
const tokenRes = await fetch(`${TOKEN_URL}?grant_type=client_credential&appid=${creds.appId}&secret=${creds.appSecret}`);
const tokenData = await tokenRes.json();
if (!tokenData.access_token) throw new Error(`token error: ${JSON.stringify(tokenData)}`);
const token = tokenData.access_token;

// 1. 列出草稿箱（前 20 条）
const listRes = await fetch(`${DRAFT_LIST_URL}?access_token=${token}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ offset: 0, count: 20, no_content: 1 }),
});
const listData = await listRes.json();
if (listData.errcode) throw new Error(`list error: ${JSON.stringify(listData)}`);

console.log("=== 草稿箱条目 ===");
for (const item of listData.item || []) {
  for (const a of item.content.news_item || []) {
    console.log(`${a.media_id} | ${a.title} | ${a.update_time}`);
  }
}
