#!/usr/bin/env python3
"""Store and compare local WeChat audit snapshots."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "docs" / "wechat-data-audit-log.json"


def _required(mapping: Any, keys: tuple[str, ...], path: str, errors: list[str]) -> bool:
    if not isinstance(mapping, dict):
        errors.append(f"{path} must be an object")
        return False
    missing = [key for key in keys if key not in mapping]
    if missing:
        errors.append(f"{path} missing: {', '.join(missing)}")
    return not missing


def _date(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{path} must be YYYY-MM-DD")
        return
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be YYYY-MM-DD")


def _datetime(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{path} must be ISO 8601 with timezone")
        return
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path} must be ISO 8601 with timezone")
        return
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{path} must include a timezone")


def _non_negative_int(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"{path} must be a non-negative integer")


def _int(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(f"{path} must be an integer")


def _money(value: Any, path: str, errors: list[str], nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        errors.append(f"{path} must be a non-negative number")


def _percentage(value: Any, path: str, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 100:
        errors.append(f"{path} must be a percentage from 0 to 100 or null")


def _period(value: Any, path: str, errors: list[str]) -> None:
    if _required(value, ("from", "to"), path, errors):
        _date(value["from"], f"{path}.from", errors)
        _date(value["to"], f"{path}.to", errors)


def _daily_content(value: Any, path: str, errors: list[str]) -> None:
    if _required(value, ("date", "reads", "shares", "comments"), path, errors):
        _date(value["date"], f"{path}.date", errors)
        for key in ("reads", "shares", "comments"):
            _non_negative_int(value[key], f"{path}.{key}", errors)


def _article(value: Any, path: str, errors: list[str]) -> None:
    if _required(value, ("date", "title", "reads", "share"), path, errors):
        _date(value["date"], f"{path}.date", errors)
        if not isinstance(value["title"], str) or not value["title"]:
            errors.append(f"{path}.title must be a non-empty string")
        _non_negative_int(value["reads"], f"{path}.reads", errors)
        _percentage(value["share"], f"{path}.share", errors)


def _content(value: Any, path: str, errors: list[str]) -> None:
    if not _required(value, ("readers30d", "daily", "sources", "articles"), path, errors):
        return
    _non_negative_int(value["readers30d"], f"{path}.readers30d", errors)
    _daily_content(value["daily"], f"{path}.daily", errors)
    if not isinstance(value["sources"], dict):
        errors.append(f"{path}.sources must be an object")
    else:
        for key, percentage in value["sources"].items():
            _percentage(percentage, f"{path}.sources.{key}", errors)
    if not isinstance(value["articles"], list):
        errors.append(f"{path}.articles must be an array")
    else:
        for index, article in enumerate(value["articles"]):
            _article(article, f"{path}.articles[{index}]", errors)


def _daily_users(value: Any, path: str, errors: list[str]) -> None:
    if _required(value, ("date", "new", "cancelled", "net", "total"), path, errors):
        _date(value["date"], f"{path}.date", errors)
        for key in ("new", "cancelled", "total"):
            _non_negative_int(value[key], f"{path}.{key}", errors)
        _int(value["net"], f"{path}.net", errors)


def _users(value: Any, path: str, errors: list[str]) -> None:
    if not _required(value, ("daily", "channelTotal", "channels", "trend"), path, errors):
        return
    _daily_users(value["daily"], f"{path}.daily", errors)
    _non_negative_int(value["channelTotal"], f"{path}.channelTotal", errors)
    if not isinstance(value["channels"], dict):
        errors.append(f"{path}.channels must be an object")
    else:
        for key, channel in value["channels"].items():
            channel_path = f"{path}.channels.{key}"
            if _required(channel, ("count", "share"), channel_path, errors):
                _non_negative_int(channel["count"], f"{channel_path}.count", errors)
                _percentage(channel["share"], f"{channel_path}.share", errors)
    if not isinstance(value["trend"], list):
        errors.append(f"{path}.trend must be an array")
    else:
        for index, row in enumerate(value["trend"]):
            _daily_users(row, f"{path}.trend[{index}]", errors)


def _income_summary(value: Any, path: str, errors: list[str]) -> None:
    keys = ("pulls", "impressions", "exposureRate", "clicks", "ctr", "ecpm", "revenue")
    if not _required(value, keys, path, errors):
        return
    for key in ("pulls", "impressions", "clicks"):
        _non_negative_int(value[key], f"{path}.{key}", errors)
    _percentage(value["exposureRate"], f"{path}.exposureRate", errors)
    _percentage(value["ctr"], f"{path}.ctr", errors)
    _money(value["ecpm"], f"{path}.ecpm", errors, nullable=True)
    _money(value["revenue"], f"{path}.revenue", errors)


def _income_slot(value: Any, path: str, errors: list[str]) -> None:
    if not _required(value, ("summary", "dailyRevenueTotal", "daily"), path, errors):
        return
    _income_summary(value["summary"], f"{path}.summary", errors)
    _money(value["dailyRevenueTotal"], f"{path}.dailyRevenueTotal", errors)
    if not isinstance(value["daily"], list):
        errors.append(f"{path}.daily must be an array")
        return
    for index, row in enumerate(value["daily"]):
        row_path = f"{path}.daily[{index}]"
        if _required(row, ("date", "pulls", "impressions", "exposureRate", "clicks", "ctr", "ecpm", "revenue"), row_path, errors):
            _date(row["date"], f"{row_path}.date", errors)
            _income_summary(row, row_path, errors)


def _article_income(value: Any, path: str, errors: list[str]) -> None:
    if not _required(value, ("scope", "articles"), path, errors):
        return
    if not isinstance(value["scope"], str) or not value["scope"]:
        errors.append(f"{path}.scope must be a non-empty string")
    if not isinstance(value["articles"], list):
        errors.append(f"{path}.articles must be an array")
        return
    for index, article in enumerate(value["articles"]):
        article_path = f"{path}.articles[{index}]"
        required = ("date", "title", "original", "revenue", "slots")
        if not _required(article, required, article_path, errors):
            continue
        _date(article["date"], f"{article_path}.date", errors)
        if not isinstance(article["title"], str) or not article["title"]:
            errors.append(f"{article_path}.title must be a non-empty string")
        if not isinstance(article["original"], bool):
            errors.append(f"{article_path}.original must be boolean")
        _money(article["revenue"], f"{article_path}.revenue", errors)
        if not isinstance(article["slots"], dict):
            errors.append(f"{article_path}.slots must be an object")
            continue
        for slot, values in article["slots"].items():
            slot_path = f"{article_path}.slots.{slot}"
            if _required(values, ("revenue", "share"), slot_path, errors):
                _money(values["revenue"], f"{slot_path}.revenue", errors)
                _percentage(values["share"], f"{slot_path}.share", errors)


def _income(value: Any, path: str, errors: list[str]) -> None:
    if not _required(value, ("overview", "articleIncomeAvailable", "slots"), path, errors):
        return
    overview = value["overview"]
    overview_keys = ("cumulativeRevenue", "programmaticRevenue", "yesterdayIncrement", "mutualSelectionRevenue", "commerceRevenue")
    if _required(overview, overview_keys, f"{path}.overview", errors):
        for key in overview_keys:
            _money(overview[key], f"{path}.overview.{key}", errors)
    if not isinstance(value["articleIncomeAvailable"], bool):
        errors.append(f"{path}.articleIncomeAvailable must be boolean")
    if "articleIncome" in value:
        _article_income(value["articleIncome"], f"{path}.articleIncome", errors)
    if not isinstance(value["slots"], dict):
        errors.append(f"{path}.slots must be an object")
    else:
        for key, slot in value["slots"].items():
            _income_slot(slot, f"{path}.slots.{key}", errors)


def validate_snapshot(snapshot: dict) -> list[str]:
    errors: list[str] = []
    required = ("collectedAt", "dataThrough", "periods", "content", "users", "income", "notes")
    if not _required(snapshot, required, "audit", errors):
        return errors
    _datetime(snapshot["collectedAt"], "audit.collectedAt", errors)
    _date(snapshot["dataThrough"], "audit.dataThrough", errors)
    periods = snapshot["periods"]
    if _required(periods, ("content", "users", "income"), "audit.periods", errors):
        for key in ("content", "users", "income"):
            _period(periods[key], f"audit.periods.{key}", errors)
    _content(snapshot["content"], "audit.content", errors)
    _users(snapshot["users"], "audit.users", errors)
    _income(snapshot["income"], "audit.income", errors)
    if not isinstance(snapshot["notes"], list) or not all(isinstance(note, str) for note in snapshot["notes"]):
        errors.append("audit.notes must be an array of strings")
    return errors


def validate_log(log: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(log, dict):
        return ["log must be an object"]
    if log.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if not isinstance(log.get("account"), str) or not log["account"]:
        errors.append("account must be a non-empty string")
    audits = log.get("audits")
    if not isinstance(audits, list):
        return errors + ["audits must be an array"]
    seen: set[str] = set()
    for index, snapshot in enumerate(audits):
        errors.extend(f"audits[{index}].{error.removeprefix('audit.')}" for error in validate_snapshot(snapshot))
        if isinstance(snapshot, dict):
            collected_at = snapshot.get("collectedAt")
            if collected_at in seen:
                errors.append(f"audits[{index}].collectedAt is duplicated: {collected_at}")
            seen.add(collected_at)
    return errors


def load_log(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _timestamp(snapshot: dict) -> dt.datetime:
    return dt.datetime.fromisoformat(snapshot["collectedAt"].replace("Z", "+00:00"))


def latest_snapshot(log: dict) -> dict | None:
    audits = log.get("audits", [])
    return max(audits, key=_timestamp) if audits else None


def snapshot_for_date(log: dict, date: str) -> dict | None:
    matches = [snapshot for snapshot in log.get("audits", []) if snapshot.get("collectedAt", "")[:10] == date]
    return max(matches, key=_timestamp) if matches else None


def compare_snapshots(old: dict, new: dict) -> dict:
    old_income = old["income"]["overview"]["programmaticRevenue"]
    new_income = new["income"]["overview"]["programmaticRevenue"]
    metrics = {
        "readers30d": {
            "from": old["content"]["readers30d"],
            "to": new["content"]["readers30d"],
            "delta": new["content"]["readers30d"] - old["content"]["readers30d"],
        },
        "dailyNewFollowers": {
            "from": old["users"]["daily"]["new"],
            "to": new["users"]["daily"]["new"],
            "delta": new["users"]["daily"]["new"] - old["users"]["daily"]["new"],
        },
        "programmaticRevenue": {
            "from": old_income,
            "to": new_income,
            "delta": round(new_income - old_income, 2),
        },
    }
    return {"from": old["collectedAt"], "to": new["collectedAt"], "metrics": metrics}


def _atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        Path(temp_name).replace(path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def append_snapshot(path: Path, snapshot: dict) -> None:
    errors = validate_snapshot(snapshot)
    if errors:
        raise ValueError("invalid snapshot:\n" + "\n".join(errors))
    log = load_log(path)
    log_errors = validate_log(log)
    if log_errors:
        raise ValueError("invalid log:\n" + "\n".join(log_errors))
    if any(item.get("collectedAt") == snapshot["collectedAt"] for item in log["audits"]):
        raise ValueError(f"duplicate collectedAt: {snapshot['collectedAt']}")
    log["audits"].append(snapshot)
    _atomic_write(path, log)


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    append = commands.add_parser("append")
    append.add_argument("--input", type=Path, required=True)
    commands.add_parser("latest")
    show = commands.add_parser("show")
    show.add_argument("--date", required=True)
    compare = commands.add_parser("compare")
    compare.add_argument("--from", dest="from_date", required=True)
    compare.add_argument("--to", dest="to_date", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "append":
            snapshot = json.loads(args.input.read_text(encoding="utf-8"))
            append_snapshot(args.log, snapshot)
            print(f"appended {snapshot['collectedAt']}")
            return 0
        log = load_log(args.log)
        errors = validate_log(log)
        if errors:
            raise ValueError("invalid log:\n" + "\n".join(errors))
        if args.command == "validate":
            print("valid")
        elif args.command == "latest":
            snapshot = latest_snapshot(log)
            if snapshot is None:
                raise ValueError("log has no audits")
            _print_json(snapshot)
        elif args.command == "show":
            snapshot = snapshot_for_date(log, args.date)
            if snapshot is None:
                raise ValueError(f"no audit on {args.date}")
            _print_json(snapshot)
        elif args.command == "compare":
            old = snapshot_for_date(log, args.from_date)
            new = snapshot_for_date(log, args.to_date)
            if old is None or new is None:
                raise ValueError("both comparison dates must exist in the log")
            _print_json(compare_snapshots(old, new))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
