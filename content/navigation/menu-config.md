# 公众号底部菜单配置

## 核心思路

**合集页 = 永久导航。** 每个系列建一个微信合集，菜单直接链接合集页 URL。发新文章时勾选对应合集，菜单零维护。

合集页 URL 格式：`https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=XXX#wechat_redirect`

---

## 推荐菜单结构

```
🔥 热门文章               📚 系列合集               📋 关于
├─ 篇1（数据最强）          ├─ 训练回路（6篇·已完结）     ├─ 💬 联系作者
├─ 篇2                    ├─ 大模型原理（6篇·更新中）   
├─ 篇3                    ├─ DeepSeek解密（更新中）    
├─ 篇4                    └─ AI上下文为什么越来越慢      
├─ 篇5（数据最弱）
```

## 各菜单详细配置

### 🔥 热门文章（手动维护，≤5篇）

所有子菜单类型选「跳转网页」。按当前阅读量从高到低排列：

| 排序 | 子菜单名 | 链接 |
|-----|---------|------|
| 1 | 损失函数 | `https://mp.weixin.qq.com/s/zIWqYqYVzEaF1e8P6fcTfw` |
| 2 | Adam优化器 | `https://mp.weixin.qq.com/s/aSLVO-otvr2rxIU1kr2eAA` |
| 3 | 反向传播 | `https://mp.weixin.qq.com/s/oYj_qpwF4tZG84ImOn977g` |
| 4 | Softmax | `https://mp.weixin.qq.com/s/5wMquh_v3oon2-NEDeQLEw` |
| 5 | 残差连接 | `https://mp.weixin.qq.com/s/xefNN9Gjaw3TKl60KeHzAg` |

**维护规则**：新文章阅读量进前 5 时替换末位。被替下的文章通过合集页仍可访问。更新频率：约每月一次。

### 📚 系列合集（一次配置，永远不动）

所有子菜单类型选「跳转网页」。合集页 URL 永久不变：

| 子菜单名 | 链接 | 维护 |
|---------|------|------|
| 训练回路（6篇·已完结） | `https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4594958081087864833#wechat_redirect` | 不需维护 |
| 大模型原理（6篇·更新中） | `https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzkyMzQyODExNQ==&action=getalbum&album_id=4597831652025925632#wechat_redirect` | 不需维护 |
| DeepSeek解密（更新中） | `TODO_DEEPSEEK_COLLECTION_URL` | 不需维护 |

> **为什么不用维护**：发新文章时在编辑页勾选对应合集 → 合集页自动收纳。URL 不变，菜单不变。

### 📋 关于

子菜单类型选「发送消息」，配合后台关键词自动回复：

| 子菜单名 | 关键词 | 自动回复内容 |
|---------|--------|-------------|
| 💬 联系作者 | （默认触发） | 有问题直接留言～文章末尾评论区也可以讨论 |
| 🔍 搜文章 | 搜文章 | 回复你想找的关键词（比如「注意力」「梯度下降」「DeepSeek」），我帮你定位 |

---

## 与当前「服务」栏目的对比

| 维度 | 当前（服务栏目） | 新方案 |
|------|---------------|--------|
| 命名 | 「服务」→ 读者不知道是什么 | 「系列合集」→ 一目了然 |
| 更新 | 每次发新文章要改菜单 | 合集页自动更新，菜单永远不动 |
| 发现性 | 层级深，要展开子菜单 | 一级菜单直接展开，合集页里有封面+摘要 |
| 维护成本 | 高（每次发文都要操作） | 极低（只维护热门文章前5，约1次/月） |

---

## 需要你提供的

1. **DeepSeek 合集页 URL**：去后台 → 内容管理 → 合集 → 找到 DeepSeek 合集 → 复制链接（格式类似上面两个）
2. 如果还没有 DeepSeek 合集，新建一个，把 MoE 和 MLA 加进去就行
