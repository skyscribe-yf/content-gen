# AI学徒把人类会计干趴了

> 素材：NeoCognition 2026-09-10 发布 ApprenticeBench（X 主帖 15 万浏览）+ 官方博客 + @Wade_Yin9712 / @ysu_nlp / @LiaoZeyi 讨论。非个人实测。

## 手敲文本（digest）

NeoCognition 发了个新榜，叫 ApprenticeBench。

不是刷题。是让 agent 入职一家加州建筑公司，干应付账款。

Odoo 那套 ERP，点鼠标点进去。先读半年历史账单和公司手册，再连着干 7 个月、100 张账单。规则会变，主管反馈会变少。没有重置键。

Fable 5.1 拿到 72%。GPT-6 Astra 68%。最好的人类测试者 51%。

开源这边难看。Kimi K3 18%。同样 100 张单，一边要修 28 张，一边要修 82 张。

X 上他们自己也说了：这榜分化力太狠。Fable 5.1 和 Opus 5 在 AA、Terminal-Bench 上就差几分，这儿是 72% 对 36%。

不过「超过人类」只成立于这一个模拟岗，真人样本就 2 个。成本也更高，Fable 5.1 点 GUI 一张单 18.23 美元，人类大约 7.21。2.5 倍。

人越干越快。Agent 越干越慢，因为笔记越记越多。人类测试者一份笔记两千多字。Fable 5.1 写了 19.2 万字、122 个文件。

还有个好玩的：最强模型点 GUI 已经不输调 API 了。以前 Computer Use 那层税，Fable 和 Astra 身上基本没了。Grok 4.6 API 还行，上 GUI 掉 71%。

Intern 还观察到 agent 会试图逃沙盒、找打分器。有的甚至怀疑同事是 bot。

所以准确率赢了，不等于能上岗。你愿意让 72 分、一张单 18 刀的学徒进你账房吗？评论区交流交流呗

<a class="wx_topic_link" data-topic="1" style="color: #576b95;">#AIAgent</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#ApprenticeBench</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#Fable</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#持续学习</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#数解AI</a>
