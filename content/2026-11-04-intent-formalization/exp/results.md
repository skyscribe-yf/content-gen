# 实验结果（2026-11-01）

模型：DeepSeek-V4-Pro（主）+ DeepSeek-V4.1-Flash（复核），均经 `pi -p --no-tools` 单轮调用。
被测函数：`parse_duration(text)`，时长解析，≤30 行 Python。
变异体：15 个，手写，每个一行改动（见 `harness.py` 的 `MUTANTS`）。

## 场景 A：给的是**正确**实现

| 臂 | prompt 关键句 | 用例数 | 对着正确实现 | 变异体 |
|---|---|---|---|---|
| A1 | 覆盖率尽量高 | 73 | 67 过 / **6 挂** | 基线不绿，不计分 |
| A2 | 目标是抓住「被改错一行」 | 11 | 全绿 | **杀死 14/15** |

A2 唯一存活：M10（`return total` → `return float(total)`）——值相等，`assert ==` 看不出来。

A1 的 6 条失败明细：
- 4 条：自己发明了错误分类（`pytest.raises(ValueError, match="no valid tokens")`，实现给的是别的消息）
- 1 条：断言 `"1 h 30 m" == 5400`（实现要求数字与单位相邻）
- 1 条：多余字符的边界

## 场景 B：给的是**带一个隐蔽 bug** 的实现

B1 注入 bug：负号被静默吃掉（`"-1h30m"` 返回 5400，应当报错）。

| 跑法 | 用例数 | 在 buggy 上 | 在正确实现上 |
|---|---|---|---|
| B1.pro（V4 Pro） | 45 | **全绿** | 3 挂 |
| B1.flash（V4.1 Flash） | 75 | 1 挂 | 7 挂 |

两者都写出了同一个东西：

```python
def test_leading_minus_ignored():
    assert parse_duration("-1h") == 3600
    assert parse_duration("-1d2h") == 86400 + 7200
```

Flash 版是 `test_leading_minus_is_ignored`，4 个参数用例，连 `-0s == 0` 都断言了。

B2 注入 bug：重复单位不再报错（`"1h1h"` 返回 7200）。

| 跑法 | 用例数 | 在 buggy 上 | 重复单位有没有测 |
|---|---|---|---|
| B2.pro | 35 | 1 挂（`"1 h"` 那条） | **没有**。叫 `test_repeated_same_unit` 的用例测的是 `"1m30s" == 90` |

## 三种失败模式（正文用这个分类）

1. **漏测**：重复单位一次没测，bug 原地躺着。
2. **测错**：`"1 h 30 m"` 这类断言从一开始就不成立。
3. **把 bug 写成预期**：负号被吞，它给这个行为起了名字，写成标准答案。

## 局限（正文必须说）

- 每个格子 n=1，单一函数、单一模型家族，只能当演示，不能当统计结论。
- 白盒补测试意味着实现是唯一的规格来源；这正是它把 bug 写成预期的前提。
- A1 基线不绿，所以它的变异体数字刻意不报。

## 复现

```bash
cd exp
python3 run.py A1,A2,B1,B2 pro     # 四臂
python3 run.py B1 flash            # 复核
python3 harness.py --src src_reference --test runs/A2.pro/test_parse_duration.py
python3 crosscheck.py --test runs/B1.pro/test_parse_duration.py --against src_reference
```
