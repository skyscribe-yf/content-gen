#!/usr/bin/env python3
"""排期台账 CLI —— schedule/*.json 的唯一读写入口。

为什么（2026-11-14）：原 draft-status.yaml 单文件 370KB（66% 是 notes 历史），agent 每次
查排期/回填 URL 都要整读整写。现按「已发布 / 待发布」拆成分离 JSON + JSON Schema，notes 外置
到 notes.json 按 slug 单点读；draft-status.yaml 降级为 rebuild 生成的兼容视图，勿手改。

数据布局（主源，schema 见 schedule/schema.json）：
  schedule/published.json   已发布台账（status=published，含 wechat_url）
  schedule/pending.json     待发布台账（planned/drafting/ready/scheduled/draft_saved）
  schedule/notes.json       slug → 历史笔记 + plan_notes 全局规划史
  schedule/meta.json        计数总览 + next_publish_date（agent 一眼看完只需读这个）
  draft-status.yaml         ↑ 的生成视图（兼容旧引用）

用法：
  python3 scripts/schedule.py                          # summary 看板（默认）
  python3 scripts/schedule.py list [--all] [--status S] [--series X]
  python3 scripts/schedule.py get <slug>               # 单条记录（纯 JSON，可管道 jq）
  python3 scripts/schedule.py find --wechat-url U | --title T | --slug S
  python3 scripts/schedule.py notes <slug> [--append TEXT]
  python3 scripts/schedule.py add <slug> --title T [--series S] [--status planned]
  python3 scripts/schedule.py remove <slug>                # 删除误登记条目
  python3 scripts/schedule.py set <slug> [--status S] [--published-date D] [--wechat-url U]
         [--zhihu-url U] [--title T] [--series S] [--type T] [--media-id ID]
         [--cover-media-id ID] [--draft-media-id ID] [--old-media-id ID]
         [--scheduled-publish 'YYYY-MM-DD HH:MM'] [--file cover=true]
  python3 scripts/schedule.py next [YYYY-MM-DD]        # 查看/设置下一个发布日
  python3 scripts/schedule.py validate                 # schema + 跨文件不变量校验
  python3 scripts/schedule.py rebuild                  # 从 JSON 重建 draft-status.yaml 视图
  python3 scripts/schedule.py migrate [--force]        # 一次性：旧 draft-status.yaml → schedule/*.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE_DIR = ROOT / "schedule"
SCHEMA_FILE = SCHEDULE_DIR / "schema.json"
PUBLISHED_FILE = SCHEDULE_DIR / "published.json"
PENDING_FILE = SCHEDULE_DIR / "pending.json"
NOTES_FILE = SCHEDULE_DIR / "notes.json"
META_FILE = SCHEDULE_DIR / "meta.json"
YAML_VIEW = ROOT / "draft-status.yaml"

PUBLISHED = "published"
PENDING_STATUSES = ("planned", "drafting", "ready", "scheduled", "draft_saved")
ALL_STATUSES = PENDING_STATUSES + (PUBLISHED,)

# set/add 可写的文章字段（slug 不可改；files 子字段走 --file）
ARTICLE_FIELDS = ("title", "series", "status", "published_date", "scheduled_publish",
                  "wechat_url", "zhihu_url", "type", "media_id", "cover_media_id",
                  "draft_media_id", "old_media_id")
FILE_FLAGS = ("weixin", "draft", "outline", "cover", "quality_check")

_LEDGER_SCHEMA = "schedule/schema.json#/$defs/ledger"
_NOTES_SCHEMA = "schedule/schema.json#/$defs/notes_file"
_META_SCHEMA = "schedule/schema.json#/$defs/meta"


# ── 基础 IO ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _empty_ledger() -> dict:
    return {"schema": _LEDGER_SCHEMA, "schema_version": 1, "updated": None, "articles": []}


def _load_ledger(path: Path) -> dict:
    return _read_json(path) if path.exists() else _empty_ledger()


def _save_ledger(path: Path, articles: list) -> None:
    _write_json(path, {
        "schema": _LEDGER_SCHEMA,
        "schema_version": 1,
        "updated": _now(),
        "articles": sorted(articles, key=lambda a: a["slug"]),
    })


def load_articles() -> tuple[list, list]:
    """返回 (published, pending) 两个列表（引用，可直接改后 save_articles）。"""
    return (_load_ledger(PUBLISHED_FILE).get("articles", []),
            _load_ledger(PENDING_FILE).get("articles", []))


def save_articles(pub: list, pen: list) -> None:
    _save_ledger(PUBLISHED_FILE, pub)
    _save_ledger(PENDING_FILE, pen)


def _load_notes() -> dict:
    if NOTES_FILE.exists():
        return _read_json(NOTES_FILE)
    return {"schema": _NOTES_SCHEMA, "schema_version": 1, "updated": None,
            "notes": {}, "plan_notes": []}


def _locate(pub: list, pen: list, slug: str):
    for lst in (pen, pub):
        for a in lst:
            if a["slug"] == slug:
                return lst, a
    return None, None


def refresh_meta() -> dict:
    """按两个台账重算 meta.json（幂等，可随时调用）。"""
    pub, pen = load_articles()
    by: dict[str, int] = {}
    for a in pub + pen:
        by[a["status"]] = by.get(a["status"], 0) + 1
    meta = _read_json(META_FILE) if META_FILE.exists() else {}
    meta.update({
        "schema": _META_SCHEMA,
        "schema_version": 1,
        "updated": _now(),
        "total": len(pub) + len(pen),
        "by_status": by,
        "next_publish_date": meta.get("next_publish_date"),
        "source": {"published": "schedule/published.json", "pending": "schedule/pending.json",
                   "notes": "schedule/notes.json", "schema": "schedule/schema.json"},
    })
    _write_json(META_FILE, meta)
    return meta


# ── draft-status.yaml 兼容视图 ────────────────────────────────────────────────

_YAML_HEADER = (
    "# ⚠️ 本文件是生成物，勿手改——主源在 schedule/*.json（schema: schedule/schema.json）\n"
    "# 查询/修改请用: python3 scripts/schedule.py (list|get|set|add|notes|validate)\n"
    "# 重新生成:   python3 scripts/schedule.py rebuild\n"
)


def rebuild_yaml() -> int:
    """从 schedule/*.json 重建 draft-status.yaml 兼容视图。"""
    try:
        import yaml
    except ImportError:
        print("⚠️ 未装 pyyaml，跳过 draft-status.yaml 视图重建（JSON 主源不受影响）",
              file=sys.stderr)
        return 1

    pub, pen = load_articles()
    notes = _load_notes()
    notes_map = notes.get("notes", {})
    meta = _read_json(META_FILE) if META_FILE.exists() else {}

    articles = []
    for a in sorted(pub + pen, key=lambda x: x["slug"]):
        rec = {}
        for k in ("slug", "title", "series", "status", "published_date", "scheduled_publish",
                  "wechat_url", "zhihu_url", "type", "media_id", "cover_media_id",
                  "draft_media_id", "old_media_id", "files"):
            if k not in a:
                continue
            v = a[k]
            if v == "":
                continue
            rec[k] = v
        n = notes_map.get(a["slug"])
        if n:
            rec["notes"] = n
        articles.append(rec)

    by: dict[str, int] = {}
    for a in articles:
        by[a["status"]] = by.get(a["status"], 0) + 1
    data = {
        "articles": articles,
        "summary": {
            "total": len(articles),
            "by_status": by,
            "drafting_queue": [a["slug"] for a in articles if a["status"] == "drafting"],
            "ready_queue": [a["slug"] for a in articles if a["status"] == "ready"],
            "scheduled_queue": [a["slug"] for a in articles if a["status"] == "scheduled"],
            "planned_queue": [a["slug"] for a in articles if a["status"] == "planned"],
            "next_publish_date": meta.get("next_publish_date"),
        },
        "plan_notes": notes.get("plan_notes", []),
    }
    body = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=4096,
                          default_flow_style=False)
    YAML_VIEW.write_text(_YAML_HEADER + body, encoding="utf-8")
    return 0


# ── 子命令 ───────────────────────────────────────────────────────────────────

def cmd_summary(_args) -> int:
    meta = _read_json(META_FILE) if META_FILE.exists() else refresh_meta()
    pub, pen = load_articles()
    by = meta.get("by_status", {})
    parts = [f"{k}={v}" for k, v in by.items()]
    print("📊 排期台账（主源 schedule/*.json，schema: schedule/schema.json）")
    print(f"   total={meta.get('total')}  " + "  ".join(parts))
    print(f"   下一个发布日: {meta.get('next_publish_date') or '（未定）'}")
    if pen:
        print(f"\n   待发布 {len(pen)} 篇:")
        for a in pen:
            print(f"     [{a['status']:<11}] {a['slug']}  {a.get('title', '')}")
    else:
        print("\n   待发布队列为空。")
    print("\n   常用: list / get <slug> / set <slug> --status published --wechat-url ... / validate")
    return 0


def cmd_list(args) -> int:
    pub, pen = load_articles()
    rows = (pub + pen) if args.all else pen
    if args.status:
        rows = [a for a in rows if a["status"] == args.status]
    if args.series:
        rows = [a for a in rows if args.series in (a.get("series") or "")]
    if not rows:
        print("（无匹配条目）")
        return 0
    print(f"{'SLUG':<40} {'STATUS':<12} {'DATE':<11} TITLE")
    print("─" * 100)
    for a in rows:
        date = a.get("published_date") or a.get("scheduled_publish") or "—"
        print(f"{a['slug']:<40} {a['status']:<12} {str(date):<11} {a.get('title', '')}")
    print(f"\n共 {len(rows)} 条。详情: python3 scripts/schedule.py get <slug>")
    return 0


def cmd_get(args) -> int:
    pub, pen = load_articles()
    _, rec = _locate(pub, pen, args.slug)
    if rec is None:
        print(f"❌ 台账无此条目: {args.slug}", file=sys.stderr)
        return 1
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    n = _load_notes().get("notes", {}).get(args.slug)
    if n:
        print(f"# （另有 {len(n)} 字历史笔记: python3 scripts/schedule.py notes {args.slug}）",
              file=sys.stderr)
    return 0


def cmd_find(args) -> int:
    pub, pen = load_articles()
    rows = []
    for a in pub + pen:
        if args.slug and args.slug != a["slug"]:
            continue
        if args.wechat_url and args.wechat_url not in (a.get("wechat_url") or ""):
            continue
        if args.zhihu_url and args.zhihu_url not in (a.get("zhihu_url") or ""):
            continue
        if args.title and args.title not in (a.get("title") or ""):
            continue
        rows.append(a)
    if not rows:
        print("（无匹配）")
        return 1
    for a in rows:
        print(json.dumps(a, ensure_ascii=False))
    return 0


def cmd_notes(args) -> int:
    data = _load_notes()
    notes_map = data["notes"]
    if args.append:
        cur = notes_map.get(args.slug, "")
        notes_map[args.slug] = f"{cur}\n{args.append}".strip() if cur else args.append
        data["updated"] = _now()
        _write_json(NOTES_FILE, data)
        rebuild_yaml()
        print(f"✅ notes 已追加: {args.slug}（现 {len(notes_map[args.slug])} 字）")
        return 0
    if args.slug not in notes_map:
        print(f"（{args.slug} 无 notes）")
        return 0
    print(notes_map[args.slug])
    return 0


def cmd_add(args) -> int:
    pub, pen = load_articles()
    if _locate(pub, pen, args.slug)[1] is not None:
        print(f"❌ 条目已存在: {args.slug}", file=sys.stderr)
        return 1
    rec = {"slug": args.slug, "title": args.title, "series": args.series,
           "status": args.status, "published_date": None, "wechat_url": None}
    pen.append(rec)
    save_articles(pub, pen)
    refresh_meta()
    rebuild_yaml()
    print(f"✅ 已登记待发布: {args.slug} [{args.status}] {args.title}")
    return 0


def cmd_set(args) -> int:
    pub, pen = load_articles()
    lst, rec = _locate(pub, pen, args.slug)
    if rec is None:
        print(f"❌ 台账无此条目: {args.slug}（新条目用 add）", file=sys.stderr)
        return 1

    for f in ARTICLE_FIELDS:
        v = getattr(args, f, None)
        if v is not None:
            rec[f] = v
    for spec in args.file or []:
        if "=" not in spec:
            print(f"❌ --file 需要 KEY=BOOL 形式: {spec}", file=sys.stderr)
            return 1
        k, v = spec.split("=", 1)
        if k not in FILE_FLAGS:
            print(f"❌ 未知 files 字段: {k}（可选 {FILE_FLAGS}）", file=sys.stderr)
            return 1
        rec.setdefault("files", {})[k] = v.strip().lower() in ("1", "true", "yes")

    moved = None
    if rec["status"] == PUBLISHED and lst is pen:
        pen.remove(rec)
        pub.append(rec)
        moved = "pending→published"
    elif rec["status"] != PUBLISHED and lst is pub:
        pub.remove(rec)
        pen.append(rec)
        moved = "published→pending"

    save_articles(pub, pen)
    refresh_meta()
    rebuild_yaml()
    msg = f"✅ {args.slug} 已更新"
    if moved:
        msg += f"（{moved}）"
    print(msg)
    if rec["status"] == PUBLISHED and not (rec.get("wechat_url") and rec.get("published_date")):
        print("⚠️ published 条目缺 wechat_url / published_date，validate 会报错", file=sys.stderr)
    return 0


def cmd_remove(args) -> int:
    pub, pen = load_articles()
    lst, rec = _locate(pub, pen, args.slug)
    if rec is None:
        print(f"❌ 台账无此条目: {args.slug}", file=sys.stderr)
        return 1
    lst.remove(rec)
    save_articles(pub, pen)
    ndata = _load_notes()
    if ndata["notes"].pop(args.slug, None) is not None:
        ndata["updated"] = _now()
        _write_json(NOTES_FILE, ndata)
    refresh_meta()
    rebuild_yaml()
    print(f"✅ 已删除: {args.slug}（含其 notes）")
    return 0


def cmd_next(args) -> int:
    meta = _read_json(META_FILE) if META_FILE.exists() else refresh_meta()
    if args.date:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
            print("❌ 日期格式应为 YYYY-MM-DD", file=sys.stderr)
            return 1
        meta["next_publish_date"] = args.date
        meta["updated"] = _now()
        _write_json(META_FILE, meta)
        rebuild_yaml()
        print(f"✅ next_publish_date = {args.date}")
        return 0
    print(meta.get("next_publish_date") or "（未定）")
    return 0


def cmd_rebuild(_args) -> int:
    rc = rebuild_yaml()
    pub, pen = load_articles()
    print(f"✅ draft-status.yaml 视图已重建（published={len(pub)} pending={len(pen)}）")
    return rc


# ── validate：内置轻量 JSON Schema 校验器（无第三方依赖） ─────────────────────

def _validate_node(node, schema: dict, path: str, errors: list, root: dict) -> None:
    if "$ref" in schema:
        name = schema["$ref"].removeprefix("#/$defs/")
        if name not in root.get("$defs", {}):
            errors.append(f"{path}: 未知 $ref {schema['$ref']}")
            return
        _validate_node(node, root["$defs"][name], path, errors, root)
        return

    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        pytypes = {"object": dict, "array": list, "string": str,
                   "integer": int, "boolean": bool, "null": type(None)}
        ok = False
        for t in types:
            if t == "integer" and isinstance(node, bool):
                continue
            if t == "boolean" and not isinstance(node, bool):
                continue
            if t not in pytypes or isinstance(node, pytypes[t]):
                ok = True
                break
        if not ok:
            errors.append(f"{path}: 期望类型 {schema['type']}，实际 {type(node).__name__}")
            return

    if "const" in schema and node != schema["const"]:
        errors.append(f"{path}: 期望 {schema['const']!r}，实际 {node!r}")
    if "enum" in schema and node not in schema["enum"]:
        errors.append(f"{path}: {node!r} 不在枚举 {schema['enum']} 内")
    if isinstance(node, str):
        if "pattern" in schema and not re.search(schema["pattern"], node):
            errors.append(f"{path}: {node!r} 不匹配 {schema['pattern']}")
        if "minLength" in schema and len(node) < schema["minLength"]:
            errors.append(f"{path}: 长度 {len(node)} < minLength {schema['minLength']}")
    if isinstance(node, dict):
        for r in schema.get("required", []):
            if r not in node:
                errors.append(f"{path}: 缺少必填字段 '{r}'")
        props = schema.get("properties", {})
        addl = schema.get("additionalProperties", True)
        for k, v in node.items():
            if k in props:
                _validate_node(v, props[k], f"{path}.{k}", errors, root)
            elif addl is False:
                errors.append(f"{path}: 未定义字段 '{k}'（additionalProperties: false）")
            elif isinstance(addl, dict):
                _validate_node(v, addl, f"{path}.{k}", errors, root)
    if isinstance(node, list) and "items" in schema:
        for i, v in enumerate(node):
            _validate_node(v, schema["items"], f"{path}[{i}]", errors, root)


def cmd_validate(_args) -> int:
    if not SCHEMA_FILE.exists():
        print(f"❌ 缺 schema: {SCHEMA_FILE}", file=sys.stderr)
        return 1
    schema = _read_json(SCHEMA_FILE)
    errors: list[str] = []

    files = [("published.json", PUBLISHED_FILE, "ledger"),
             ("pending.json", PENDING_FILE, "ledger"),
             ("notes.json", NOTES_FILE, "notes_file"),
             ("meta.json", META_FILE, "meta")]
    for name, path, defname in files:
        if not path.exists():
            errors.append(f"缺文件: schedule/{name}")
            continue
        _validate_node(_read_json(path), schema["$defs"][defname], name, errors, schema)

    pub, pen = load_articles()
    slugs = [a["slug"] for a in pub] + [a["slug"] for a in pen]
    if len(slugs) != len(set(slugs)):
        dup = sorted({s for s in slugs if slugs.count(s) > 1})
        errors.append(f"slug 跨文件重复: {dup}")
    for a in pub:
        if a["status"] != PUBLISHED:
            errors.append(f"published.json 中 {a['slug']} status={a['status']}（应为 published）")
        if not a.get("published_date"):
            errors.append(f"published.json 中 {a['slug']} 缺 published_date")
        if not a.get("wechat_url"):
            errors.append(f"published.json 中 {a['slug']} 缺 wechat_url")
    for a in pen:
        if a["status"] == PUBLISHED:
            errors.append(f"pending.json 中 {a['slug']} status=published（应移到 published.json）")
        if a.get("published_date") or a.get("wechat_url"):
            errors.append(f"pending.json 中 {a['slug']} 不应有 published_date/wechat_url")
    notes_keys = set(_load_notes().get("notes", {}))
    unknown = notes_keys - set(slugs)
    if unknown:
        errors.append(f"notes.json 有台账中不存在的 slug: {sorted(unknown)}")
    if META_FILE.exists():
        meta = _read_json(META_FILE)
        if meta.get("total") != len(slugs):
            errors.append(f"meta.total={meta.get('total')} 与实际 {len(slugs)} 不一致")
        by: dict[str, int] = {}
        for a in pub + pen:
            by[a["status"]] = by.get(a["status"], 0) + 1
        if meta.get("by_status") != by:
            errors.append(f"meta.by_status={meta.get('by_status')} 与实际 {by} 不一致")

    if errors:
        print(f"❌ validate 失败（{len(errors)} 项）:")
        for e in errors:
            print("   -", e)
        return 1
    print(f"✅ validate 通过（published={len(pub)} pending={len(pen)} notes={len(notes_keys)}）")
    return 0


def cmd_migrate(args) -> int:
    # schema.json 是静态配置不算数据；只在数据文件已存在时拒绝（防误覆盖）
    existing = [p.name for p in (PUBLISHED_FILE, PENDING_FILE, NOTES_FILE, META_FILE) if p.exists()]
    if existing and not args.force:
        print(f"❌ 数据文件已存在 {existing}；确认重跑请加 --force", file=sys.stderr)
        return 1
    if not YAML_VIEW.exists():
        print(f"❌ 找不到 {YAML_VIEW}", file=sys.stderr)
        return 1
    try:
        import yaml
    except ImportError:
        print("❌ migrate 需要 pyyaml（pip install pyyaml）", file=sys.stderr)
        return 1

    d = yaml.safe_load(YAML_VIEW.read_text(encoding="utf-8"))
    pub, pen, notes_map = [], [], {}
    for a in d.get("articles", []):
        rec = {k: v for k, v in a.items() if k != "notes"}
        # yaml 可能把日期解析成 date 对象，统一成字符串
        rec = json.loads(json.dumps(rec, ensure_ascii=False, default=str))
        n = a.get("notes")
        if n:
            notes_map[rec["slug"]] = "\n".join(n) if isinstance(n, list) else str(n)
        (pub if rec.get("status") == PUBLISHED else pen).append(rec)

    _save_ledger(PUBLISHED_FILE, pub)
    _save_ledger(PENDING_FILE, pen)
    _write_json(NOTES_FILE, {
        "schema": _NOTES_SCHEMA, "schema_version": 1, "updated": _now(),
        "notes": notes_map, "plan_notes": d.get("plan_notes") or [],
    })
    _write_json(META_FILE, {
        "schema": _META_SCHEMA, "schema_version": 1, "updated": _now(),
        "next_publish_date": (d.get("summary") or {}).get("next_publish_date"),
    })
    refresh_meta()
    rebuild_yaml()
    print(f"✅ migrated: published={len(pub)} pending={len(pen)} "
          f"notes={len(notes_map)} plan_notes={len(d.get('plan_notes') or [])}")
    return 0


# ── 入口 ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(
        description="排期台账 CLI（主源 schedule/*.json；draft-status.yaml 是生成视图）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("用法：")[-1])
    sub = p.add_subparsers(dest="command")

    sub.add_parser("summary", help="状态看板（默认）")

    sp = sub.add_parser("list", help="列出条目（默认只看待发布）")
    sp.add_argument("--all", action="store_true", help="含已发布")
    sp.add_argument("--status", choices=ALL_STATUSES)
    sp.add_argument("--series", help="按系列子串过滤")

    sp = sub.add_parser("get", help="单条记录（纯 JSON 输出）")
    sp.add_argument("slug")

    sp = sub.add_parser("find", help="按字段反查")
    sp.add_argument("--slug")
    sp.add_argument("--wechat-url")
    sp.add_argument("--zhihu-url")
    sp.add_argument("--title")

    sp = sub.add_parser("notes", help="查看/追加某篇历史笔记")
    sp.add_argument("slug")
    sp.add_argument("--append", help="追加一条笔记文本")

    sp = sub.add_parser("add", help="登记新条目（进待发布）")
    sp.add_argument("slug", help="内容目录名，如 2026-11-20-my-topic")
    sp.add_argument("--title", required=True)
    sp.add_argument("--series")
    sp.add_argument("--status", choices=PENDING_STATUSES, default="planned")

    sp = sub.add_parser("set", help="更新字段（status 变更自动在两个台账间迁移）")
    sp.add_argument("slug")
    for f in ARTICLE_FIELDS:
        sp.add_argument(f"--{f.replace('_', '-')}",
                        choices=ALL_STATUSES if f == "status" else None)
    sp.add_argument("--file", action="append", metavar="KEY=BOOL",
                    help=f"files 子字段，可重复，如 --file cover=true（可选 {FILE_FLAGS}）")

    sp = sub.add_parser("remove", help="删除误登记的条目")
    sp.add_argument("slug")
    sp = sub.add_parser("next", help="查看/设置下一个发布日")
    sp.add_argument("date", nargs="?", help="YYYY-MM-DD，不给则查看")

    sub.add_parser("validate", help="schema + 跨文件不变量校验")
    sub.add_parser("rebuild", help="重建 draft-status.yaml 兼容视图")
    sp = sub.add_parser("migrate", help="一次性迁移：旧 draft-status.yaml → schedule/*.json")
    sp.add_argument("--force", action="store_true")

    args = p.parse_args()
    cmds = {
        None: cmd_summary, "summary": cmd_summary, "list": cmd_list, "get": cmd_get,
        "find": cmd_find, "notes": cmd_notes, "add": cmd_add, "set": cmd_set,
        "remove": cmd_remove,
        "next": cmd_next, "validate": cmd_validate, "rebuild": cmd_rebuild,
        "migrate": cmd_migrate,
    }
    return cmds[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
