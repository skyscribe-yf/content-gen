# DeepSeek V4.1刷分了？旧榜和新榜对不上

> 素材：X 上 V4.1 Flash 发布后的 benchmaxxing 争论（TB 2.1 vs 4.0 名次倒挂、harness 分差、Teortaxes / Onur Solmaz / Artificial Analysis）+ 作者实测原声。非导流、非评测广告。

## 手敲文本（digest）

DeepSeek V4.1 Flash 一出来，X 上立刻吵开了。

一边是官方表。Terminal-Bench 2.1 打到 90.6，DeepSWE 74.2，CyberGym 88.1。数字看着确实吓人。

另一边立刻有人说：这是 benchmaxxing。旧榜第一，新榜掉队。

最刺眼的是 Terminal-Bench 自己的版本差。2.1 上它能压一头，换到 3.0、4.0，相对排名就往下掉。HuggingFace 的 Onur 画了张图，说污染过的模型，在训练后才出现的新榜上，名次会倒过来。不管是不是故意的，他觉得这模型真正值钱的是架构，不是那张表。

也有人立刻反驳：2.1 到 4.0 根本不是同一套题，任务数从 89 掉到 66，每一行还都是自家 harness。斜率本身分不开泄漏和评测漂移。

DeepSeek 铁粉 Teortaxes 更直接：因为相对排名在 TB 2.1 和 4.0 上不一样，就说刷分，挺好笑的。V4.1 几乎是反着刷的。他们明显不在乎榜，甚至不在乎用户体验。这就是内部那套鲸鱼 AGI 研发套件。

第三方 Artificial Analysis 给的 Intelligence Index 是 40，压过自家 V4 Pro 的 36，但还在 GLM-5.3、Kimi K3 后面。AutomationBench 倒是冲到并列第一。同时它也是他们测过最啰嗦的模型之一，单任务平均吐 8.9 万 token。啰嗦归啰嗦，单任务成本还是被价格按在地板上。

同一套权重，换个壳，分还能再晃一截。这个上次说过了，这次不展开。只补一句：官方 instruct 数字，推理强度全部拉满 100。你平时不会这么开。

实际测试非常好用，价格也很低廉，当然对于很多benchmark不能覆盖的角落，各方的说辞差异还是很大。上一次Gemini 3.8 Flash也出现了类似的问题，甚至artificial analysis还连夜改榜单的计分呢。至今Muse Spark的能力还是众说纷纭的。

话说回来，榜单本来就不是说明书。旧套件饱和了，新套件还没被训熟，两边都会出鬼。你拿它当选模型的唯一尺子，迟早被尺子耍。

你现在看榜，还是看自己仓库里跑完那一下？评论区交流交流呗

<a class="wx_topic_link" data-topic="1" style="color: #576b95;">#DeepSeek</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#V4.1Flash</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#benchmark</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#刷分</a>  <a class="wx_topic_link" data-topic="1" style="color: #576b95;">#数解AI</a>
