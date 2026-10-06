# 事实源

> 2026-10-06 贴图。主事实核对自 Nieman Lab 原文（2026-10-05）和文中配图。不把配图说明写成记者没写的实验。

## 主报道

- 标题：ChatGPT is adding real cartoonists’ signatures to fake New Yorker cartoons
- 作者：Andrew Deck，Nieman Lab，2026-10-05 16:01
- URL：https://www.niemanlab.org/2026/10/chatgpt-is-adding-real-cartoonists-signatures-to-fake-new-yorker-cartoons/
- HN（2026-10-06 凌晨抓取时）：首页第 1，约 141 分、44 条评论，发帖约 1 小时

## 可写事实

| 项 | 事实 | 出处 |
|---|---|---|
| 传开的那张 | 天堂门口，Dolly Parton 与 Tim Curry（文中写 Frank-N-Furter 装）。对白 “I knew I chose the right plus one” | 正文 + 配图 `src/loper-forgery.jpg` |
| 时间与热度 | 文中写 8 月底两人去世后的几天里传开。X 帖 2026-08-26 22:18，账号 @woofknight。配图读数：赞 25K、浏览 422.2K、转发 2.4K、回复 82。正文写其中一个帖子 25,000 likes | 正文 + 配图底栏 |
| 签名 | 右下角签 Bloper。正文写笔名 “BLOPER”，Brendan Loper 的笔名。不是他画的，也不是他签的 | 正文 + 配图 |
| 怎么来的 | 一名 Dolly Parton 粉丝发在 Facebook，评论里写自己只让 ChatGPT 画 “a New Yorker-style cartoon” | 正文 |
| 画家本人 | 亲弟弟先发消息，问是不是他画的。之后是陌生人邮件和私信。五月有人在 Instagram 提醒过。夏天 Reddit r/ChatGPT 又有一批 | 正文，Loper 原话转述 |
| 规模 | 记者自己测，记下超过 15 位《纽约客》画家的签名被用上。点名包括 Harry Bliss、Emily Flake、Joe Dator、Pat Byrnes、Peter Vey、Jason Adam Katzenstein、George Booth、Liza Donnelly、Ellis Rosen、Saul Steinberg；也有 1960 年代的 Warren Miller | 正文 |
| Flake | 笔名 “e. flake”。假图对白 “She was on her way to buy coffee.” 她说整体更像好几个画家揉在一起，签名却是她的：“就像有人把一句我没说过的话安到我头上。” | 正文 + `src/flake-ai.jpg` / `flake-real.jpg` |
| Byrnes | 1998 年起以 “P.Byrnes” 在《纽约客》发画。从十几岁起签名末尾固定一个句号。记者找到的十几张带他名字的 ChatGPT 图，每一张句号都在 | 正文 + `src/byrnes-ai.jpg` / `byrnes-real.jpg` |
| 笑点 | 记者写：有些对白根本不成笑话。不是每张都有签名，也有笔名是乱码 | 正文 |
| OpenAI | 发言人：未来的创造力本质上属于人；感谢社区指出 bug 和非预期行为。记者通知后，再要纽约客风格会返回 “This prompt may violate our guardrails concerning similarity to third-party content.” 发稿时，一些没指定风格的普通漫画仍会签上真人名字。OpenAI 没有回答签名是怎么学进去的 | 正文 |
| 授权 | Condé Nast 2024 年与 OpenAI 有多年内容授权（Wired）。《纽约客》发言人：从未允许任何大模型开发方用漫画训练；刊头标志也不在任何大模型授权里。记者看过的画家合同模板不是职务作品，版权在画家，模板里没有 AI 训练许可 | 正文 |

## 配图来源（嵌入用，不改像素内容）

- `src/loper-forgery.jpg`：Nieman 配的那条 8 月 26 日 X 帖截图，含 Bloper 签名和 25K / 422.2K
- `src/flake-ai.jpg`、`src/flake-real.jpg`：假图对白是买咖啡；真图对白 “At least A. I. ain’t comin’ for our jobs.” 两张都签 e. flake
- `src/byrnes-ai.jpg`、`src/byrnes-real.jpg`：两张都签 P.BYRNES.，句号在

## 口径边界（正文必须带）

- 「超过 15 位」是记者记录到的人数，不是 OpenAI 官方统计。
- 25K / 42.2 万是这篇配图里那一条帖的读数，不是全网总和。正文写的是 25,000 likes。
- 护栏挡住的是「纽约客风格」这类提示。发稿时普通漫画仍会签真人名。不要写成「已经修好了」。
- 不写「我测过」。作者没有复现。
- 不把 Baltimore Sun 换 AI 漫画、Anthropic 15 亿美元和解写进这篇。那是同一篇报道的旁支，不是这条签名新闻。
