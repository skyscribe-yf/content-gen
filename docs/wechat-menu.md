# 公众号菜单维护

## 菜单结构

```
🔥 热门文章（子菜单≤5）   📚 全部合集（子菜单不限）   📋 关于
├─ 篇1（最优）            ├─ 合集A → 合集页URL        ├─ 联系作者
├─ 篇2                    ├─ 合集B → 合集页URL
├─ ...                    └─ （新系列就加一个子菜单）
└─ 篇5（最弱）
```

## 热门文章（≤5篇，手动管理）

- 从所有已发表**文章**中选阅读量最高的 5 篇（**贴图不计入**，贴图阅读量再高也不进热门列表）
- 每次跑 wechat-data-audit 后必须更新此列表：从 `docs/wechat-data-audit-log.json` 聚合各文章历史最高阅读量 → 过滤贴图 → 重排前 6 → 同步 `content/navigation/menu-config.md` 的热门文章表
- 新文章发布后若数据表现好，替换第 5 篇
- 被替换的文章通过合集页和文末交叉链接仍可访问
- 账号菜单子菜单数受限时（当前仅支持 2 个），实际配置取列表前 N 篇，文档仍维护完整前 6

**2026-08-22 更新（数据截至 08-21，23,427 读；贴图已过滤）**

| 排序 | 文章 | 链接 | 阅读量 |
|-----|------|------|--------|
| 1 | KV缓存存进SSD | `https://mp.weixin.qq.com/s/40BQ06eDTv4-2r8FmQ_rMA` | 2,604 |
| 2 | 高维空间全是壳 | `https://mp.weixin.qq.com/s/Nrfr-90Fpu3mFDML9s0d1Q` | 1,356 |
| 3 | Adam优化器 | `https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA` | 1,109 |
| 4 | DeepSeek-V4为何不用MLA | `https://mp.weixin.qq.com/s/MQEgbY16mLs-N7g2xKW1HQ` | 1,040 |
| 5 | Softmax不直接取最大值 | `https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw` | 566 |

> 同步自 `content/navigation/menu-config.md`，过滤 `item_show_type=8` 贴图后按历史最高阅读重排；实际菜单配前 2 篇。

## 全部合集（合集页，一次配好永远不动）

- 每个系列建立一个微信合集（后台 → 内容管理 → 合集）
- 子菜单「跳转网页」可直接输入合集页 URL（`mp.weixin.qq.com/mp/appmsgalbum?...`），个人订阅号也支持
- 合集自动收纳该系列所有文章，菜单地址**永久不变**
- 发新文章时勾选对应合集即可，菜单无需任何修改
- 新系列出现时，才需要在「全部合集」下新增一个子菜单

## 发布后执行

1. 第一时间把 `wechatUrl` 记入该文章 frontmatter
2. 发文章时勾选对应合集（若忘记勾选，去合集管理添加）
3. 若文章数据突出（阅读量进前 6），更新「热门文章」菜单
