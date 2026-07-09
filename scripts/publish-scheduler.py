"""
发布调度器 — 读取 publish-schedule.yaml，管理内容状态和发布队列

用法:
  python3 publish-scheduler.py queue              # 查看当前发布队列
  python3 publish-scheduler.py next               # 下一个该发什么
  python3 publish-scheduler.py schedule <topic>   # 将内容排入发布队列
  python3 publish-scheduler.py publish <topic> <platform>  # 标记已发布
  python3 publish-scheduler.py state <topic> [new_state]   # 查看/修改内容状态
  python3 publish-scheduler.py check <topic> <platform>     # 发布前检查清单
  python3 publish-scheduler.py status             # 全局状态看板
  python3 publish-scheduler.py ratio              # 本月内容比例检查
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    # ponytail: yaml没装就用json版，功能一样
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE_CONFIG = ROOT / "publish-schedule.yaml"
QUEUE_FILE = ROOT / "content" / "publish-queue.json"
CONTENT_DIR = ROOT / "content"

WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WEEKDAY_CN = {"mon": "一", "tue": "二", "wed": "三", "thu": "四",
              "fri": "五", "sat": "六", "sun": "日"}


def _load_config() -> dict:
    """加载调度配置"""
    if yaml:
        return yaml.safe_load(SCHEDULE_CONFIG.read_text())
    # ponytail: 没有yaml就手写最小parser，够用
    # 实际上还是装一下比较好：pip install pyyaml
    import subprocess
    result = subprocess.run(
        [sys.executable, "-c", f"import yaml; print(yaml.safe_load(open('{SCHEDULE_CONFIG}')).__repr__())"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return eval(result.stdout.strip())
    print("❌ 需要 pyyaml: pip install pyyaml")
    sys.exit(1)


def _load_queue() -> dict:
    """加载发布队列"""
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return {"items": [], "updated": None}


def _save_queue(queue: dict):
    """保存发布队列"""
    queue["updated"] = datetime.now().isoformat()
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2))


def _find_topic_dir(topic: str) -> Path | None:
    """找到选题对应的内容目录"""
    for d in CONTENT_DIR.iterdir():
        if d.is_dir() and topic in d.name:
            return d
    return None


def _get_state_file(topic: str) -> Path:
    """获取选题的状态文件路径"""
    topic_dir = _find_topic_dir(topic)
    if topic_dir:
        return topic_dir / ".publish-state.json"
    return CONTENT_DIR / f".state-{topic}.json"


def _load_state(topic: str) -> dict:
    """加载单个选题的发布状态"""
    sf = _get_state_file(topic)
    if sf.exists():
        return json.loads(sf.read_text())
    return {
        "topic": topic,
        "state": "draft",
        "platforms": {},
        "scheduled_times": {},
        "published_times": {},
    }


def _save_state(topic: str, state: dict):
    """保存选题发布状态"""
    sf = _get_state_file(topic)
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def _next_window(config: dict, platform: str, after: datetime | None = None) -> datetime:
    """计算某个平台的下一个发布窗口"""
    after = after or datetime.now()
    windows = config["windows"].get(platform, [])
    if not windows or windows[0].get("day") == "any":
        # zhihu等任意时间平台，返回after+1h
        return after + timedelta(hours=1)

    # 找最近的一个窗口
    best = None
    for _ in range(8):  # 往后找一周
        check_date = (after + timedelta(days=_)).date()
        weekday = WEEKDAYS[check_date.weekday()]
        for w in windows:
            if w["day"] == weekday:
                candidate = datetime.combine(check_date, datetime.min.time().replace(hour=w["hour"]))
                if candidate >= after:
                    if best is None or candidate < best:
                        best = candidate
    return best or after + timedelta(days=7)


def _compute_schedule(config: dict, base_time: datetime, content_type: str = "principle") -> dict:
    """根据错位策略计算各平台发布时间"""
    if content_type == "eval":
        stagger = config.get("eval_hot", {})
    else:
        stagger = config.get("stagger", {})

    schedule = {}
    for platform, offset_str in stagger.items():
        if offset_str == "immediate":
            schedule[platform] = base_time
            continue
        # 解析 +12h, +48h, +1h 等
        hours = int(offset_str.replace("+", "").replace("h", ""))
        target = base_time + timedelta(hours=hours)
        # 对齐到该平台的发布窗口
        schedule[platform] = _next_window(config, platform, target)

    return schedule


def queue_cmd():
    """显示当前发布队列"""
    q = _load_queue()
    config = _load_config()
    items = q.get("items", [])

    if not items:
        print("📭 发布队列为空")
        print("💡 添加内容: python3 publish-scheduler.py schedule <topic>")
        return

    print(f"\n📋 发布队列 ({len(items)} 期内容)\n")
    print(f"{'选题':<30s} {'状态':<10s} {'类型':<8s} {'公众号':<18s} {'小红书':<18s} {'B站':<18s}")
    print("─" * 100)

    now = datetime.now()

    for item in items:
        topic = item["topic"]
        state_data = _load_state(topic)
        state = state_data.get("state", "draft")
        content_type = item.get("type", "principle")
        scheduled = state_data.get("scheduled_times", {})

        weixin_t = scheduled.get("weixin", "—")
        xhs_t = scheduled.get("xiaohongshu", "—")
        bili_t = scheduled.get("bilibili", "—")
        published = state_data.get("published_times", {})

        # 格式化时间
        def fmt(t, platform=None):
            if t == "—" or not t:
                return "—"
            try:
                dt = datetime.fromisoformat(t)
                is_published = platform and platform in published
                marker = "✅" if is_published else ("⏳" if dt > now else "🔴")
                return f"{marker} {dt.strftime('%m/%d %H:%M')}"
            except Exception:
                return str(t)[:16]

        print(f"{topic:<30s} {state:<10s} {content_type:<8s} "
              f"{fmt(weixin_t, 'weixin'):<18s} {fmt(xhs_t, 'xiaohongshu'):<18s} {fmt(bili_t, 'bilibili'):<18s}")


def next_cmd():
    """显示下一个该发布的内容"""
    q = _load_queue()
    config = _load_config()
    items = q.get("items", [])
    now = datetime.now()

    upcoming = []
    for item in items:
        state_data = _load_state(item["topic"])
        for platform, time_str in state_data.get("scheduled_times", {}).items():
            if platform in state_data.get("published_times", {}):
                continue
            try:
                dt = datetime.fromisoformat(time_str)
                if dt >= now:
                    upcoming.append((dt, item["topic"], platform))
            except Exception:
                pass

    if not upcoming:
        print("✅ 没有待发布内容")
        return

    upcoming.sort()
    dt, topic, platform = upcoming[0]
    platform_cn = {"weixin": "公众号", "xiaohongshu": "小红书",
                   "bilibili": "B站", "zhihu": "知乎"}.get(platform, platform)

    delta = dt - now
    hours_left = delta.total_seconds() / 3600

    print(f"\n⏰ 下一个发布:")
    print(f"   选题: {topic}")
    print(f"   平台: {platform_cn}")
    if hours_left < 24:
        time_str = f"{hours_left:.1f}小时后"
    else:
        time_str = f"{hours_left/24:.1f}天后"
    print(f"   时间: {dt.strftime('%Y-%m-%d %H:%M')} ({time_str})")

    # 提醒发布前检查
    config = _load_config()
    checklist = config.get("checklist", {}).get(platform, [])
    if checklist:
        print(f"\n📝 发布前检查:")
        for i, item in enumerate(checklist, 1):
            print(f"   [ ] {item}")


def schedule_cmd(topic: str, content_type: str = "principle", base_time: str | None = None):
    """将内容排入发布队列"""
    config = _load_config()
    q = _load_queue()

    # 检查是否已在队列
    for item in q["items"]:
        if item["topic"] == topic:
            print(f"⚠️ {topic} 已在队列中")
            return

    # 确定基准时间（公众号发布时间）
    if base_time:
        base_dt = datetime.fromisoformat(base_time)
    else:
        # 找公众号的下一个发布窗口
        base_dt = _next_window(config, "weixin")

    # 计算各平台发布时间
    schedule = _compute_schedule(config, base_dt, content_type)

    # 更新选题状态
    state = _load_state(topic)
    state["state"] = "scheduled"
    state["scheduled_times"] = {p: t.isoformat() for p, t in schedule.items()}
    state["type"] = content_type
    _save_state(topic, state)

    # 加入队列
    q["items"].append({
        "topic": topic,
        "type": content_type,
        "base_time": base_dt.isoformat(),
    })
    _save_queue(q)

    # 输出排期
    platform_cn = {"weixin": "公众号", "xiaohongshu": "小红书",
                   "bilibili": "B站", "zhihu": "知乎"}

    print(f"\n📅 已排期: {topic} ({content_type})")
    print(f"   基准时间: {base_dt.strftime('%Y-%m-%d %H:%M')} ({WEEKDAY_CN.get(WEEKDAYS[base_dt.weekday()], '')})\n")

    for platform, dt in schedule.items():
        cn = platform_cn.get(platform, platform)
        print(f"   {cn:<6s}  {dt.strftime('%m/%d %H:%M')} ({WEEKDAY_CN.get(WEEKDAYS[dt.weekday()], '')})")


def publish_cmd(topic: str, platform: str):
    """标记某平台已发布"""
    state = _load_state(topic)

    if "published_times" not in state:
        state["published_times"] = {}

    state["published_times"][platform] = datetime.now().isoformat()

    # 检查是否所有平台都发了
    all_platforms = {"weixin", "xiaohongshu", "bilibili", "zhihu"}
    published = set(state["published_times"].keys())
    if all_platforms.issubset(published):
        state["state"] = "published"
    else:
        # 如果主要平台都发了就算published
        main = {"weixin", "xiaohongshu", "bilibili"}
        if main.issubset(published):
            state["state"] = "published"

    _save_state(topic, state)

    platform_cn = {"weixin": "公众号", "xiaohongshu": "小红书",
                   "bilibili": "B站", "zhihu": "知乎"}.get(platform, platform)
    print(f"✅ {topic} → {platform_cn} 已发布")

    # 如果还有未发布平台，提醒
    remaining = all_platforms - published - {platform}
    if remaining:
        cn_map = {"weixin": "公众号", "xiaohongshu": "小红书",
                  "bilibili": "B站", "zhihu": "知乎"}
        names = [cn_map.get(p, p) for p in remaining]
        print(f"📋 剩余平台: {', '.join(names)}")


def state_cmd(topic: str, new_state: str | None = None):
    """查看或修改选题状态"""
    state = _load_state(topic)

    if new_state:
        config = _load_config()
        valid = list(config.get("states", {}).keys())
        if new_state not in valid:
            print(f"❌ 无效状态: {new_state}")
            print(f"有效状态: {', '.join(valid)}")
            return

        old = state.get("state", "draft")
        state["state"] = new_state
        _save_state(topic, state)
        print(f"✅ {topic}: {old} → {new_state}")

        # 提示下一步
        state_config = config["states"].get(new_state, {})
        if "next" in state_config:
            condition = state_config.get("condition", "")
            print(f"💡 下一状态: {state_config['next']}")
            if condition:
                print(f"   条件: {condition}")
    else:
        print(f"\n📊 {topic} 状态:")
        print(f"   状态: {state.get('state', 'draft')}")
        if state.get("scheduled_times"):
            print(f"   排期:")
            cn_map = {"weixin": "公众号", "xiaohongshu": "小红书",
                      "bilibili": "B站", "zhihu": "知乎"}
            for p, t in state["scheduled_times"].items():
                cn = cn_map.get(p, p)
                published = "✅" if p in state.get("published_times", {}) else "⏳"
                print(f"     {published} {cn}: {t[:16]}")
        if state.get("published_times"):
            print(f"   已发布:")
            for p, t in state["published_times"].items():
                cn = cn_map.get(p, p)
                print(f"     ✅ {cn}: {t[:16]}")


def check_cmd(topic: str, platform: str):
    """显示发布前检查清单"""
    config = _load_config()
    checklist = config.get("checklist", {}).get(platform, [])

    platform_cn = {"weixin": "公众号", "xiaohongshu": "小红书",
                   "bilibili": "B站", "zhihu": "知乎"}.get(platform, platform)

    print(f"\n📝 {topic} → {platform_cn} 发布前检查:\n")
    for i, item in enumerate(checklist, 1):
        print(f"  [ ] {item}")

    print(f"\n💡 全部勾选后再执行: python3 publish-scheduler.py publish {topic} {platform}")


def status_cmd():
    """全局状态看板"""
    config = _load_config()
    q = _load_queue()
    items = q.get("items", [])
    now = datetime.now()

    # 统计各状态数量
    state_counts = {}
    for item in items:
        state_data = _load_state(item["topic"])
        s = state_data.get("state", "draft")
        state_counts[s] = state_counts.get(s, 0) + 1

    # 统计本月发布数
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    month_published = 0
    month_by_type = {}
    for item in items:
        state_data = _load_state(item["topic"])
        published = state_data.get("published_times", {})
        for p, t in published.items():
            try:
                dt = datetime.fromisoformat(t)
                if dt >= month_start and p == "weixin":  # 按公众号发布时间计
                    month_published += 1
                    ct = item.get("type", "principle")
                    month_by_type[ct] = month_by_type.get(ct, 0) + 1
            except Exception:
                pass

    print(f"\n📊 内容状态看板\n")
    print(f"  队列中: {len(items)} 期")
    for s, c in state_counts.items():
        print(f"  {s}: {c}")
    print(f"\n  本月已发布: {month_published} 期")
    for t, c in month_by_type.items():
        print(f"    {t}: {c}")

    # 比例检查
    if month_by_type:
        total = sum(month_by_type.values())
        print(f"\n  📐 比例检查:")
        for t, target in [("principle", "50%"), ("fusion", "30%"), ("eval", "20%")]:
            actual = month_by_type.get(t, 0)
            pct = f"{actual/total*100:.0f}%" if total else "0%"
            marker = "✅" if pct == target else "⚠️"
            print(f"    {marker} {t}: {pct} (目标 {target})")


def ratio_cmd():
    """本月内容比例检查"""
    status_cmd()  # ponytail: ratio就是status里的比例部分


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="发布调度器")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("queue", help="查看发布队列")
    sub.add_parser("next", help="下一个该发什么")
    sub.add_parser("status", help="全局状态看板")

    sched_p = sub.add_parser("schedule", help="排入发布队列")
    sched_p.add_argument("topic", help="选题名称")
    sched_p.add_argument("--type", default="principle", choices=["principle", "fusion", "eval"])
    sched_p.add_argument("--base-time", help="基准发布时间 (ISO格式)")

    pub_p = sub.add_parser("publish", help="标记已发布")
    pub_p.add_argument("topic", help="选题名称")
    pub_p.add_argument("platform", choices=["weixin", "xiaohongshu", "bilibili", "zhihu"])

    state_p = sub.add_parser("state", help="查看/修改状态")
    state_p.add_argument("topic", help="选题名称")
    state_p.add_argument("new_state", nargs="?", help="新状态")

    check_p = sub.add_parser("check", help="发布前检查清单")
    check_p.add_argument("topic", help="选题名称")
    check_p.add_argument("platform", choices=["weixin", "xiaohongshu", "bilibili", "zhihu"])

    sub.add_parser("ratio", help="内容比例检查")

    args = parser.parse_args()

    cmds = {
        "queue": lambda: queue_cmd(),
        "next": lambda: next_cmd(),
        "schedule": lambda: schedule_cmd(args.topic, args.type, args.base_time),
        "publish": lambda: publish_cmd(args.topic, args.platform),
        "state": lambda: state_cmd(args.topic, getattr(args, 'new_state', None)),
        "check": lambda: check_cmd(args.topic, args.platform),
        "status": lambda: status_cmd(),
        "ratio": lambda: ratio_cmd(),
    }

    if args.command in cmds:
        cmds[args.command]()
    else:
        parser.print_help()
