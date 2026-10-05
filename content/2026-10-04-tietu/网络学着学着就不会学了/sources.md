# 事实源

> 2026-10-04 贴图。Sutton 推文为他本人 10 月 3 日连发的三篇博士论文介绍。数字来自 Dohare 2026 博士论文正文，不采用转述。

## 推文（2026-10-03，@RichardSSutton）

查看时间 2026-10-04 上午，互动还会变，正文不写死赞数。

| 学生 | 论文 | 推文 |
|---|---|---|
| 第 15 个博士生 Shibhansh Dohare | Learning Forever using Artificial Neural Networks | https://x.com/RichardSSutton/status/2106471496126505132 |
| 第 16 个博士生 Fernando Hernandez Garcia | Selective Reinitialization Algorithms for Preventing Plasticity Loss in Artificial Neural Networks | https://x.com/RichardSSutton/status/2106500715254587572 |
| Gautham Vasan（Sutton 刚参加过答辩委员会） | Robots That Learn on the Fly Through Real-World Interaction | https://x.com/RichardSSutton/status/2106510502088360268 |

当时点赞最高的是 Dohare 那条。Fernando 那条阅读更高。旁边还有人讨论「一辈子 16 个博士」，那不是论文结论，正文不写。

## Dohare 论文

- PDF：http://incompleteideas.net/papers/Dohare_Shibhansh_PhD.pdf （阿尔伯塔大学，© 2026，CC Public Domain Mark 1.0）
- 大学存档：https://ualberta.scholaris.ca/items/fbc0a0a4-0a49-4bee-ba81-1aacc2c84c7e （Dohare_Shibhansh_202601_PhD.pdf，2026-03）
- Preface：第 3、4、6、7 章基于 Dohare 等，Nature 632, 768–774（2024），https://doi.org/10.1038/s41586-024-07711-7
- 现在在 Keen Technologies 做研究科学家（Sutton 推文）

## 可写数字与判断（论文原文）

| 项 | 写法 | 出处 |
|---|---|---|
| 现象 | 可塑性下降和隐藏单元变休眠、彼此变像同时发生 | 摘要 |
| 算法 | 持续反向传播 = 普通反向传播 + 每步重置一小部分单元。新单元入边随机、出边置 0，避免立刻改掉已学函数；成熟阈值内不被再次重置 | 第 6 章 |
| 重置率 | ρ 通常很小，每步重置个数不到 1，攒够 1 再重置一个 | 第 6 章 |
| ImageNet 早期 | 这些网络在早期任务测试集上最多学到 88% | 第 4 章，Continual ImageNet |
| ImageNet 后期 | 前 10 个任务有时先升后降；放到 2000 个任务，可塑性损失很严重 | Figure 4.11 说明 |
| 持续反传的 ImageNet 设置 | 成熟阈值 100，重置率 3×10⁻⁴ | 第 6 章 |
| 第 5000 个任务 | 测试集准确率比第一个任务还高；完全保住了可塑性 | 第 6 章 |
| 速度 | 第 5000 个任务上，到达最佳准确率比整网重初始化快 10 倍：10 个 epoch 对大约 125 个 epoch | 第 6 章讨论 |
| CIFAR-100 增量 | 100 类都到齐时，增量训练比从头重训低 5 个百分点，幅度相当于拿掉批归一化这种主要改进 | 第 4 章 |
| CIFAR-100 持续反传 | 在线训练准确率大约高 2 个点，学得比从头训更快 | 第 6 章 |
| RL | 常见算法不随数据变好，表现会掉；掉了之后可塑性没了，回不来。持续反传能让表现随经验继续升。只清休眠单元不够 | 第 7 章 |

## 另外两篇，只作旁证，不写它们论文里没有的数

- Fernando：把持续反传推广成「选择性重置」。单元级重置对输出扰动小，但「单元」的定义随架构变。权重级重置任何网络都能用，但会晃输出，要用 L2 稳住。两种都保住了可塑性。（推文摘要）
- Gautham：机器人边跑边学。AVG 每来一条转移就更新一次，不存回放。物理机器人在边缘设备上几小时内学到能用的策略。四台物理机器人用最小时间奖励、原始像素，几小时内从零学会够到目标，不用外部仪器。（推文摘要，Sutton 贴出的摘要原文）

## 不可写

- 不写「大模型已经失去可塑性」。论文测的是前馈网、残差网、ImageNet/CIFAR 持续任务和 on-policy 深度 RL，不是 2026 年的国产大模型。
- 不把 88% 写成「后来掉到某个具体百分数」，论文这一句只给了早期上限，后期用「损失很严重」描述，没有在我核对的段落里给一个单一终值。
- 不生成 Sutton 或学生的人脸。
