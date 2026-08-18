#!/usr/bin/env python3
"""Static timeline contract checks for Manim ``shipinhao`` scenes.

This module deliberately does not import Manim.  It reads the voice timeline
next to a ``scenes.py`` file and inspects the source with :mod:`ast`, so it is
safe to run before the rendering environment (or its native dependencies) is
installed.

The public entry point is :func:`analyze_scene`.  A result is a plain dict so
callers can serialize it without depending on project-specific classes.  The
command line interface prints the same result as either deterministic text or
JSON.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import operator
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


EPSILON = 0.03
"""Small timing slack for hand-rounded ``self.at`` values (seconds)."""

BOUNDARY_TOLERANCE = 0.12
"""Tolerance when matching a source ``self.at`` to an audio boundary."""


@dataclass
class _Timeline:
    source: str | None = None
    kind: str | None = None
    segments: dict[str, dict[str, Any]] = field(default_factory=dict)
    global_boundaries: list[float] = field(default_factory=list)
    global_duration: float | None = None
    info: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class TimelineContract:
    """Runtime view of the same metadata consumed by the static checker.

    Scenes use this small adapter through ``_Base.at_clip``.  Keeping the
    loader here prevents the render path and the preflight path from silently
    acquiring different timestamp rules.
    """

    def __init__(self, timeline: _Timeline):
        if timeline.error:
            raise ValueError(timeline.error)
        self._timeline = timeline

    @classmethod
    def for_scene(cls, scene_file: str | Path) -> "TimelineContract":
        path = Path(scene_file)
        if path.is_dir():
            path = path / "scenes.py"
        timeline = _load_timeline(path.parent / "tts")
        return cls(timeline)

    def start_of(self, clip_id: str) -> float:
        wanted = str(clip_id).strip().upper()
        for segment in self._timeline.segments.values():
            starts = segment.get("clip_starts", {})
            for key, value in starts.items():
                if str(key).strip().upper() == wanted:
                    return float(value)
        # Full subtitles sometimes carry IDs but no scene grouping.  Their
        # normalized global records are kept in the global boundary list; a
        # numeric suffix remains a useful deterministic fallback.
        if wanted.startswith("C") and wanted[1:].isdigit():
            index = int(wanted[1:]) - 1
            if 0 <= index < len(self._timeline.global_boundaries):
                return self._timeline.global_boundaries[index]
        raise KeyError(f"时间轴中不存在 clip {clip_id!r}")


@dataclass
class _Event:
    kind: str
    line: int
    col: int
    value: float | None = None
    duration: float | None = None
    call: ast.Call | None = None
    label: str = ""
    animation_count: int = 0
    animation_names: tuple[str, ...] = ()


def _normalise_scene_name(value: object) -> str:
    """Return the conventional upper-case scene key used by the manifests."""

    return str(value).strip().upper()


def _number(node: ast.AST | None) -> float | None:
    """Safely evaluate a small numeric AST expression.

    Timeline code commonly uses literals (``2.80``), but accepting arithmetic
    constants such as ``32 / 2`` makes the checker useful without evaluating
    arbitrary scene code.  Anything dynamic returns ``None``.
    """

    if node is None:
        return None
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        value = None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = float(value)
        return result if math.isfinite(result) else None

    operations: dict[type[ast.operator], Any] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }

    def evaluate(expr: ast.AST) -> float | None:
        if isinstance(expr, ast.Constant) and isinstance(expr.value, (int, float)):
            if isinstance(expr.value, bool) or not math.isfinite(float(expr.value)):
                return None
            return float(expr.value)
        if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, (ast.UAdd, ast.USub)):
            inner = evaluate(expr.operand)
            return None if inner is None else (inner if isinstance(expr.op, ast.UAdd) else -inner)
        if isinstance(expr, ast.BinOp) and type(expr.op) in operations:
            left, right = evaluate(expr.left), evaluate(expr.right)
            if left is None or right is None:
                return None
            try:
                result = float(operations[type(expr.op)](left, right))
            except (ArithmeticError, OverflowError, ValueError):
                return None
            return result if math.isfinite(result) else None
        return None

    return evaluate(node)


def _json_number(value: object) -> float | None:
    """Convert a JSON number to a finite float, otherwise return ``None``."""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if math.isfinite(number):
            return number
    return None


def _as_seconds(value: object) -> float | None:
    """Normalize subtitle timestamps, which are usually milliseconds."""

    number = _json_number(value)
    if number is None:
        return None
    # ``full.subtitle.json`` stores milliseconds.  Small hand-authored test
    # fixtures often use seconds, so retain values below one thousand.
    return number / 1000.0 if abs(number) > 1000.0 else number


def _unique_sorted(values: Iterable[float]) -> list[float]:
    """Sort finite timestamps and remove near-duplicates deterministically."""

    result: list[float] = []
    for value in sorted(float(v) for v in values if math.isfinite(float(v))):
        if not result or abs(value - result[-1]) > 1e-7:
            result.append(round(value, 6))
    return result


def _clip_start_end(clip: Mapping[str, Any]) -> tuple[float | None, float | None]:
    """Read a clip's start/end fields across known manifest spellings."""

    start_value = clip.get("start", clip.get("time_begin", clip.get("begin")))
    end_value = clip.get("end", clip.get("time_end", clip.get("finish")))
    start = _as_seconds(start_value)
    end = _as_seconds(end_value)
    return start, end


def _segment_from_clips(clips: object, duration: object = None) -> dict[str, Any]:
    """Build one normalized segment from sentence clips or pause points."""

    boundaries: list[float] = []
    ends: list[float] = []
    clip_starts: dict[str, float] = {}
    if isinstance(clips, Sequence) and not isinstance(clips, (str, bytes)):
        for item in clips:
            if isinstance(item, Mapping):
                start, end = _clip_start_end(item)
                if start is not None:
                    boundaries.append(start)
                    clip_id = item.get("id", item.get("clip_id", item.get("name")))
                    if clip_id is not None:
                        clip_starts[str(clip_id)] = start
                if end is not None:
                    ends.append(end)
            else:
                point = _as_seconds(item)
                if point is not None:
                    boundaries.append(point)
    boundaries = _unique_sorted(boundaries)
    if not boundaries or boundaries[0] > EPSILON:
        boundaries.insert(0, 0.0)
    parsed_duration = _as_seconds(duration)
    if parsed_duration is None and ends:
        parsed_duration = max(ends)
    if parsed_duration is None and boundaries:
        parsed_duration = max(boundaries)
    return {"boundaries": boundaries, "duration": parsed_duration, "clip_starts": clip_starts}


def _load_timeline(tts_dir: Path) -> _Timeline:
    """Load the highest-priority available timeline manifest.

    Sentence-level boundaries are preferred because they contain both starts
    and ends.  ``pauses.json`` and ``full.subtitle.json`` are fallbacks used by
    older projects and by the recording/TTS branches respectively.
    """

    candidates = (
        ("sentence-boundaries.json", "sentence-boundaries"),
        ("pauses.json", "pauses"),
        ("full.subtitle.json", "full-subtitle"),
    )
    for filename, kind in candidates:
        path = tts_dir / filename
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return _Timeline(source=str(path), kind=kind, error=f"无法读取 {filename}: {exc}")
        timeline = _Timeline(source=str(path), kind=kind)
        try:
            if kind == "sentence-boundaries":
                _parse_sentence_boundaries(payload, timeline)
            elif kind == "pauses":
                _parse_pauses(payload, timeline)
            else:
                _parse_full_subtitle(payload, timeline)
        except (TypeError, ValueError, KeyError) as exc:
            timeline.error = f"无法解析 {filename}: {exc}"
        return timeline
    return _Timeline(error=f"未找到 {tts_dir}/sentence-boundaries.json、pauses.json 或 full.subtitle.json")


def _parse_sentence_boundaries(payload: object, timeline: _Timeline) -> None:
    """Normalize the current ``source + segments + clips`` manifest shape."""

    raw_segments: object
    if isinstance(payload, Mapping):
        raw_segments = payload.get("segments", payload)
    else:
        raw_segments = payload
    if isinstance(raw_segments, Mapping):
        iterable = [{"id": key, **value} for key, value in raw_segments.items() if isinstance(value, Mapping)]
    elif isinstance(raw_segments, Sequence) and not isinstance(raw_segments, (str, bytes)):
        iterable = list(raw_segments)
    else:
        raise ValueError("segments 不是列表或对象")
    for item in iterable:
        if not isinstance(item, Mapping):
            continue
        key = _normalise_scene_name(item.get("id", item.get("scene", item.get("name", ""))))
        if not key:
            continue
        clips = item.get("clips", item.get("boundaries", []))
        timeline.segments[key] = _segment_from_clips(clips, item.get("duration"))


def _parse_pauses(payload: object, timeline: _Timeline) -> None:
    """Normalize ``{"S1": [pause, ...]}`` recording manifests."""

    data = payload.get("segments", payload) if isinstance(payload, Mapping) else payload
    if not isinstance(data, Mapping):
        raise ValueError("pauses 不是对象")
    for key, values in data.items():
        scene = _normalise_scene_name(key)
        if not scene:
            continue
        if isinstance(values, Mapping):
            raw_points = values.get("pauses", values.get("boundaries", values.get("clips", [])))
            duration = values.get("duration")
        else:
            raw_points, duration = values, None
        timeline.segments[scene] = _segment_from_clips(raw_points, duration)


def _parse_full_subtitle(payload: object, timeline: _Timeline) -> None:
    """Normalize subtitle records and keep global timestamps for later mapping."""

    if isinstance(payload, Mapping):
        records = payload.get("segments", payload.get("subtitles", payload.get("items", [])))
    else:
        records = payload
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise ValueError("full.subtitle 不是列表")
    global_points: list[float] = []
    global_ends: list[float] = []
    grouped: dict[str, list[float]] = {}
    grouped_ends: dict[str, list[float]] = {}
    for item in records:
        if not isinstance(item, Mapping):
            continue
        start, end = _clip_start_end(item)
        if start is None:
            continue
        global_points.append(start)
        if end is not None:
            global_ends.append(end)
        raw_key = item.get("id", item.get("scene", item.get("segment")))
        if raw_key is not None:
            key = _normalise_scene_name(raw_key)
            grouped.setdefault(key, []).append(start)
            if end is not None:
                grouped_ends.setdefault(key, []).append(end)
    timeline.global_boundaries = _unique_sorted(global_points)
    timeline.global_duration = max(global_ends or global_points, default=None)
    timeline.info = {
        "scope": "global",
        "mapping": "pending",
        "note": "full.subtitle.json 没有场景字段；只有取得每段音频时长后才换算为场景相对时间",
    }
    for key, points in grouped.items():
        timeline.segments[key] = {
            "boundaries": _unique_sorted(points),
            "duration": max(grouped_ends.get(key, points), default=None),
        }


def _iter_calls(node: ast.AST) -> Iterator[ast.Call]:
    """Yield calls in source order, excluding nested function definitions."""

    calls: list[ast.Call] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, current: ast.FunctionDef) -> None:  # noqa: N802
            if current is not node:
                return
            self.generic_visit(current)

        def visit_AsyncFunctionDef(self, current: ast.AsyncFunctionDef) -> None:  # noqa: N802
            if current is not node:
                return
            self.generic_visit(current)

        def visit_Lambda(self, current: ast.Lambda) -> None:  # noqa: N802
            return

        def visit_Call(self, current: ast.Call) -> None:  # noqa: N802
            calls.append(current)
            self.generic_visit(current)

    Visitor().visit(node)
    calls.sort(key=lambda call: (getattr(call, "lineno", 0), getattr(call, "col_offset", 0)))
    return iter(calls)


def _method_name(call: ast.Call) -> str:
    """Return the final attribute/name component of a call."""

    function = call.func
    if isinstance(function, ast.Attribute):
        return function.attr
    if isinstance(function, ast.Name):
        return function.id
    return ""


def _is_self_method(call: ast.Call, name: str | None = None) -> bool:
    """Whether a call is ``self.<name>(...)``."""

    if not isinstance(call.func, ast.Attribute) or not isinstance(call.func.value, ast.Name):
        return False
    if call.func.value.id != "self":
        return False
    return name is None or call.func.attr == name


def _keyword_number(call: ast.Call, name: str) -> float | None:
    """Read a numeric keyword from a call."""

    for keyword in call.keywords:
        if keyword.arg == name:
            return _number(keyword.value)
    return None


def _nested_run_times(node: ast.AST) -> list[float]:
    """Collect literal ``run_time=`` values nested in animation arguments."""

    result: list[float] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            value = _keyword_number(child, "run_time")
            if value is not None and value >= 0:
                result.append(value)
    return result


def _animation_names(call: ast.Call) -> tuple[str, ...]:
    """Name top-level animation expressions in a ``self.play`` call."""

    names: list[str] = []
    for argument in call.args:
        if isinstance(argument, ast.Starred):
            names.append("*")
        elif isinstance(argument, ast.Call):
            names.append(_method_name(argument) or "call")
        elif isinstance(argument, ast.Name):
            names.append(argument.id)
        else:
            names.append(type(argument).__name__)
    return tuple(names)


def _action_duration(call: ast.Call) -> float | None:
    """Estimate a static action duration without executing user code."""

    method = _method_name(call)
    if method == "wait":
        value = _number(call.args[0]) if call.args else _keyword_number(call, "duration")
        return 1.0 if value is None else max(0.0, value)
    explicit = _keyword_number(call, "run_time")
    nested = _nested_run_times(call)
    if explicit is not None:
        duration = explicit
    elif nested:
        duration = max(nested)
    else:
        duration = 1.0
    if method == "breathe":
        loops = _number(next((kw.value for kw in call.keywords if kw.arg == "loops"), None))
        if loops is not None:
            duration *= max(0.0, loops)
    return max(0.0, duration) if math.isfinite(duration) else None


ANIMATION_METHODS = {
    "play",
    "wait",
    "play_scroll_unroll",
    "play_scroll_unroll_many",
    "play_red_cross",
    "play_mark",
    "transition_out",
    "camera_zoom_to",
    "morph_to",
    "trace_dot",
    "breathe",
    "emphasize",
    "counter_value",
    "grow_bar",
    "tilt_balance",
}


def _events(construct: ast.FunctionDef | ast.AsyncFunctionDef) -> list[_Event]:
    """Extract timeline and action events from one construct method."""

    events: list[_Event] = []
    for call in _iter_calls(construct):
        line, col = getattr(call, "lineno", 0), getattr(call, "col_offset", 0)
        if _is_self_method(call, "at"):
            events.append(_Event("at", line, col, value=_number(call.args[0]) if call.args else None, call=call, label="self.at"))
        elif _is_self_method(call, "at_clip"):
            clip_id = ""
            if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
                clip_id = call.args[0].value
            events.append(_Event("clip", line, col, call=call, label=clip_id or "self.at_clip"))
        elif _is_self_method(call) and _method_name(call) in ANIMATION_METHODS:
            method = _method_name(call)
            if method in {"at", "pad_to_voice"}:
                continue
            names = _animation_names(call) if method == "play" else (method,)
            count = len(call.args) if method == "play" else 1
            events.append(_Event("action", line, col, duration=_action_duration(call), call=call, label=f"self.{method}", animation_count=count, animation_names=names))
        elif _is_self_method(call, "pad_to_voice"):
            events.append(_Event("pad", line, col, call=call, label="self.pad_to_voice"))
    # Nested calls (for example ``type_in(..., run_time=...)``) are present in
    # the AST too, but only the self.* events above belong to the contract.
    return events


def _literal_mapping(tree: ast.AST, name: str) -> dict[str, float]:
    """Read a top-level numeric mapping such as ``VOICE_DUR`` if available."""

    for node in getattr(tree, "body", []):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError, SyntaxError):
            return {}
        if not isinstance(value, Mapping):
            return {}
        result: dict[str, float] = {}
        for key, item in value.items():
            number = _json_number(item)
            if number is not None:
                result[_normalise_scene_name(key)] = number
        return result
    return {}


def _wav_duration(path: Path) -> float | None:
    """Read a PCM WAV duration without invoking ffprobe."""
    try:
        with wave.open(str(path), "rb") as handle:
            rate = handle.getframerate()
            frames = handle.getnframes()
        return frames / rate if rate else None
    except (OSError, wave.Error, ZeroDivisionError):
        return None


def _map_global_timeline(
    timeline: _Timeline,
    durations: Mapping[str, float],
    scene_names: Iterable[str],
    tts_dir: Path | None = None,
) -> None:
    """Map a global full-subtitle track to local scene clocks when possible."""

    if not timeline.global_boundaries or timeline.segments:
        return
    names = [_normalise_scene_name(name) for name in scene_names]
    if len(names) == 1:
        name = names[0]
        timeline.segments[name] = {"boundaries": list(timeline.global_boundaries), "duration": timeline.global_duration}
        return
    offset = 0.0
    for index, name in enumerate(names, 1):
        duration = durations.get(name)
        if tts_dir is not None:
            measured = _wav_duration(tts_dir / f"s{index}.wav")
            if measured is not None:
                duration = measured
        if duration is None:
            break
        local = [point - offset for point in timeline.global_boundaries if offset - EPSILON <= point <= offset + duration + EPSILON]
        if local:
            local.insert(0, 0.0) if local[0] > EPSILON else None
        else:
            local = [0.0]
        timeline.segments[name] = {"boundaries": _unique_sorted(local), "duration": duration}
        # The TTS splitter leaves a 100 ms seam between segments.  It belongs
        # to the global subtitle clock, not to either local Scene clock.
        offset += duration + 0.1


def _issue(code: str, severity: str, message: str, *, line: int | None = None, scene: str | None = None, **details: Any) -> dict[str, Any]:
    """Create a stable issue mapping used by both API and CLI output."""

    item: dict[str, Any] = {"code": code, "severity": severity}
    if scene is not None:
        item["scene"] = scene
    if line is not None:
        item["line"] = line
    item["message"] = message
    if details:
        item["details"] = {key: details[key] for key in sorted(details)}
    return item


def _nearest(value: float, boundaries: Sequence[float]) -> tuple[float | None, float | None]:
    """Return nearest boundary and absolute delta."""

    if not boundaries:
        return None, None
    point = min(boundaries, key=lambda item: abs(item - value))
    return point, abs(point - value)


def _constructs(tree: ast.Module) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Find class ``construct`` methods in source order."""

    result: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == "construct":
                result.append((node.name, child))
    return result


def _card_metrics(call: ast.Call) -> tuple[str, float | None, float | None, float | None] | None:
    """Extract helper card dimensions and font size from a call."""

    name = _method_name(call)
    if name not in {"_card", "boxed", "boxrow"}:
        return None
    positional = list(call.args)
    positions = {"_card": (1, 2, 5), "boxed": (1, 2, 4), "boxrow": (1, 2, 4)}[name]
    values: list[float | None] = []
    keywords = {kw.arg: _number(kw.value) for kw in call.keywords if kw.arg}
    for index, keyword_names in zip(positions, (("w", "width"), ("h", "height"), ("fs", "font_size"))):
        value = _number(positional[index]) if len(positional) > index else None
        if value is None:
            for keyword in keyword_names:
                if keyword in keywords:
                    value = keywords[keyword]
                    break
        values.append(value)
    return name, values[0], values[1], values[2]


def _format_time(value: float | None) -> str:
    """Format seconds consistently for human-readable CLI output."""

    return "?" if value is None else f"{value:.3f}s"


def analyze_scene(path: str | Path, strict: bool = False) -> dict[str, Any]:
    """Analyze one ``scenes.py`` file and its neighbouring voice timeline.

    Args:
        path: A path to ``scenes.py`` or to its ``shipinhao`` directory.
        strict: Promote all warnings to errors.  This is useful as a CI gate;
            the default mode keeps visual heuristics advisory.

    Returns:
        A deterministic, JSON-serializable mapping with ``ok``, ``timeline``,
        ``scenes``, ``issues`` and ``summary`` keys.  No scene code is
        imported or executed.
    """

    requested = Path(path)
    scene_path = requested / "scenes.py" if requested.is_dir() else requested
    scene_path = scene_path.resolve()
    top_issues: list[dict[str, Any]] = []
    try:
        source = scene_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        top_issues.append(_issue("scene_unreadable", "error", f"无法读取场景文件: {exc}"))
        return _finalize(scene_path, None, [], top_issues, strict)
    try:
        tree = ast.parse(source, filename=str(scene_path))
    except SyntaxError as exc:
        top_issues.append(_issue("syntax_error", "error", f"场景语法错误: {exc.msg}", line=exc.lineno))
        return _finalize(scene_path, None, [], top_issues, strict)

    tts_dir = scene_path.parent / "tts"
    timeline = _load_timeline(tts_dir)
    if timeline.error:
        top_issues.append(_issue("timeline_error", "error", timeline.error))
    durations = _literal_mapping(tree, "VOICE_DUR")
    constructs = _constructs(tree)
    if not constructs:
        top_issues.append(_issue("no_construct", "error", "未找到任何 Scene.construct()"))
    _map_global_timeline(timeline, durations, (name for name, _ in constructs), tts_dir)

    scenes: list[dict[str, Any]] = []
    for scene_name, construct in constructs:
        key = _normalise_scene_name(scene_name)
        events = _events(construct)
        local_issues: list[dict[str, Any]] = []
        segment = timeline.segments.get(key)
        boundaries = list(segment.get("boundaries", [])) if segment else []
        if timeline.source and not segment and timeline.kind != "full-subtitle":
            local_issues.append(_issue("scene_missing_timeline", "warning", f"时间轴中没有 {key} 的边界", line=construct.lineno, scene=key))

        at_values: list[float] = []
        actions: list[dict[str, Any]] = []
        elapsed = 0.0
        last_at: float | None = None
        action_indices: list[int] = []
        for index, event in enumerate(events):
            if event.kind in {"at", "clip"}:
                if event.kind == "clip":
                    clip_starts = segment.get("clip_starts", {}) if segment else {}
                    value = clip_starts.get(event.label)
                    if value is None:
                        local_issues.append(_issue("clip_unknown", "error", f"self.at_clip({event.label!r}) 不在当前场景时间轴中", line=event.line, scene=key))
                        continue
                else:
                    value = event.value
                if value is None:
                    local_issues.append(_issue("at_dynamic", "warning", "self.at() 参数不是静态数字，无法对齐", line=event.line, scene=key))
                    continue
                at_values.append(value)
                if last_at is not None and value < last_at - EPSILON:
                    local_issues.append(_issue("at_rollback", "error", f"{event.label}({_format_time(value)}) 回退到 {_format_time(last_at)} 之前", line=event.line, scene=key, previous=last_at, value=value))
                last_at = value
                elapsed = max(elapsed, value)
                if boundaries:
                    nearest, delta = _nearest(value, boundaries)
                    if delta is not None and delta > BOUNDARY_TOLERANCE:
                        local_issues.append(_issue("at_not_on_boundary", "warning", f"{event.label}({_format_time(value)}) 未对齐句级边界（最近 {_format_time(nearest)}）", line=event.line, scene=key, at=value, nearest=nearest, delta=round(delta, 3)))
            elif event.kind == "action":
                start = elapsed
                duration = event.duration
                end = None if duration is None else start + duration
                next_at: float | None = None
                for future in events[index + 1:]:
                    if future.kind in {"at", "clip"}:
                        if future.kind == "at":
                            next_at = future.value
                        elif segment:
                            next_at = segment.get("clip_starts", {}).get(future.label)
                        break
                if end is not None:
                    elapsed = end
                    if next_at is not None and next_at >= start - EPSILON and end > next_at + EPSILON:
                        local_issues.append(_issue("action_overrun", "error", f"{event.label} 结束于 {_format_time(end)}，超过下一时间点 {_format_time(next_at)}", line=event.line, scene=key, start=round(start, 3), end=round(end, 3), next_at=round(next_at, 3)))
                action = {"line": event.line, "kind": event.label, "start": round(start, 3), "duration": None if duration is None else round(duration, 3), "end": None if end is None else round(end, 3)}
                if next_at is not None:
                    action["next_at"] = round(next_at, 3)
                actions.append(action)
                action_indices.append(index)

        pad_events = [event for event in events if event.kind == "pad"]
        if not pad_events:
            local_issues.append(_issue("missing_pad_to_voice", "error", "construct 末尾缺少 self.pad_to_voice()", line=construct.lineno, scene=key))
        else:
            last_meaningful = next((event for event in reversed(events) if event.kind != "pad"), None)
            if last_meaningful and pad_events[-1].line < last_meaningful.line:
                local_issues.append(_issue("pad_to_voice_not_last", "warning", "self.pad_to_voice() 不是 construct 末尾动作", line=pad_events[-1].line, scene=key))

        calls = list(_iter_calls(construct))
        layout_lines = [call.lineno for call in calls if _method_name(call) == "layout_page"]
        for call in calls:
            method = _method_name(call)
            if method == "counter_value" and not any(kw.arg == "anchor" for kw in call.keywords):
                local_issues.append(_issue(
                    "dynamic_unanchored", "warning",
                    "counter_value() 没有 anchor=槽位，动态数字可能先在 ORIGIN 出现或挤开同一行静态元素",
                    line=call.lineno, scene=key,
                ))
            if method == "shift" and layout_lines and any(line < call.lineno for line in layout_lines):
                local_issues.append(_issue(
                    "post_layout_shift", "warning",
                    "layout_page() 后又手动 shift，整页几何可能失去统一居中；请回到 page_stack 组装阶段调整",
                    line=call.lineno, scene=key,
                ))
            if method == "arrange" and any(
                    kw.arg == "aligned_edge"
                    and isinstance(kw.value, ast.Name)
                    and kw.value.id == "DOWN"
                    for kw in call.keywords
            ):
                local_issues.append(_issue(
                    "row_vertical_misalignment", "warning",
                    "横向排列使用 aligned_edge=DOWN，静态/动态对象可能不在同一基线",
                    line=call.lineno, scene=key,
                ))
            metrics = _card_metrics(call)
            if metrics is None:
                continue
            helper, width, height, font_size = metrics
            # _card()/boxed()/boxrow() now call fit_text_in_box(), which
            # measures the actual rendered label and applies the shared
            # vertical sizing/line-spacing policy.  Static source ``fs`` is
            # therefore only a hint for these helpers; flag custom boxes that
            # bypass the policy instead.
            if helper not in {"_card", "boxed", "boxrow"} and height is not None and font_size is not None and (
                    (height >= 2.5 and font_size <= 24)
                    or (height >= 3.0 and font_size <= 34)
            ):
                local_issues.append(_issue("high_card_small_text", "warning", f"{helper} 高度 {_format_time(height)} 但字号只有 {font_size:g}，手机画面可能过小", line=call.lineno, scene=key, helper=helper, width=width, height=height, font_size=font_size))

        # Two separate one-animation plays with no time anchor in between are
        # a conservative signal for an accidental serial animation.  The
        # finding is advisory because intentional choreography is valid too.
        previous_action: _Event | None = None
        reveal_helpers = {
            "self.play",
            "self.play_scroll_unroll",
            "self.play_scroll_unroll_many",
            "self.counter_value",
            "self.grow_bar",
            "self.play_mark",
            "self.play_red_cross",
        }
        for event in events:
            if event.kind in {"at", "clip"} or event.kind == "pad":
                previous_action = None
                continue
            if event.kind != "action":
                continue
            if (previous_action is not None
                    and previous_action.label in reveal_helpers
                    and event.label in reveal_helpers
                    and previous_action.animation_count == event.animation_count == 1):
                local_issues.append(_issue(
                    "serial_animation", "warning",
                    "连续两个 reveal 动作没有时间锚点，可能应并行播放或显式标注时序",
                    line=event.line, scene=key,
                    previous_line=previous_action.line,
                    animations=list(previous_action.animation_names + event.animation_names),
                ))
            previous_action = event

        scene_result: dict[str, Any] = {
            "name": key,
            "line": construct.lineno,
            "timeline": key if segment else None,
            "duration": None if not segment else segment.get("duration"),
            "at": [round(value, 3) for value in at_values],
            "actions": actions,
            "has_pad_to_voice": bool(pad_events),
            "issues": sorted(local_issues, key=_issue_sort_key),
        }
        scenes.append(scene_result)
        top_issues.extend(local_issues)

    return _finalize(scene_path, timeline, scenes, top_issues, strict)


def _issue_sort_key(item: Mapping[str, Any]) -> tuple[Any, ...]:
    """Stable issue ordering for text and JSON consumers."""

    return (item.get("line", 0), item.get("scene", ""), item.get("code", ""), item.get("message", ""))


def _finalize(scene_path: Path, timeline: _Timeline | None, scenes: list[dict[str, Any]], issues: list[dict[str, Any]], strict: bool) -> dict[str, Any]:
    """Assemble and normalize the public result mapping."""

    if strict:
        # Keep the nested per-scene view consistent with the top-level issue
        # list.  Otherwise ``--strict`` would fail the command while still
        # printing advisory WARNING entries under each scene.
        for scene in scenes:
            scene["issues"] = [
                {**item, "severity": "error" if item.get("severity") == "warning" else item.get("severity")}
                for item in scene.get("issues", [])
            ]
    normalized: list[dict[str, Any]] = []
    for item in sorted(issues, key=_issue_sort_key):
        copy = dict(item)
        if strict and copy.get("severity") == "warning":
            copy["severity"] = "error"
        normalized.append(copy)
    errors = sum(item.get("severity") == "error" for item in normalized)
    warnings = sum(item.get("severity") == "warning" for item in normalized)
    source = None if timeline is None else timeline.source
    timeline_result: dict[str, Any] = {"source": source, "kind": None if timeline is None else timeline.kind, "segments": {}}
    if timeline is not None:
        for key in sorted(timeline.segments):
            value = timeline.segments[key]
            timeline_result["segments"][key] = {"boundaries": [round(point, 3) for point in value.get("boundaries", [])], "duration": value.get("duration")}
        if timeline.error:
            timeline_result["error"] = timeline.error
    result: dict[str, Any] = {
        "ok": errors == 0,
        "passed": errors == 0,
        "path": str(scene_path),
        "strict": bool(strict),
        "timeline": timeline_result,
        "scenes": sorted(scenes, key=lambda item: (item.get("line", 0), item.get("name", ""))),
        "issues": normalized,
        "summary": {"errors": errors, "warnings": warnings, "scenes": len(scenes)},
    }
    return result


def format_text(result: Mapping[str, Any]) -> str:
    """Render an analysis result as stable, concise human-readable text."""

    timeline = result.get("timeline", {})
    lines = [
        f"status: {'PASS' if result.get('ok') else 'FAIL'}",
        f"path: {result.get('path', '')}",
        f"timeline: {timeline.get('kind') or 'missing'} ({timeline.get('source') or 'none'})",
    ]
    for scene in result.get("scenes", []):
        issues = scene.get("issues", [])
        lines.append(f"scene {scene.get('name')}: at={len(scene.get('at', []))} actions={len(scene.get('actions', []))} pad={'yes' if scene.get('has_pad_to_voice') else 'no'} issues={len(issues)}")
        for item in issues:
            location = f" line {item['line']}" if item.get("line") is not None else ""
            lines.append(f"  {item.get('severity', '').upper()} {item.get('code', '')}{location}: {item.get('message', '')}")
    for item in result.get("issues", []):
        if item.get("scene") is None:
            lines.append(f"  {item.get('severity', '').upper()} {item.get('code', '')}: {item.get('message', '')}")
    summary = result.get("summary", {})
    lines.append(f"summary: scenes={summary.get('scenes', 0)} errors={summary.get('errors', 0)} warnings={summary.get('warnings', 0)}")
    return "\n".join(lines)


def _parser() -> argparse.ArgumentParser:
    """Build the module CLI parser."""

    parser = argparse.ArgumentParser(description="静态检查 Manim shipinhao 时间轴合同（无需安装 manim）")
    parser.add_argument("path", help="scenes.py 文件或 shipinhao 目录")
    parser.add_argument("--strict", action="store_true", help="将所有警告提升为错误")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON（等价于 --format json）")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="输出格式，默认 text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point; return 1 when the contract fails."""

    args = _parser().parse_args(argv)
    result = analyze_scene(args.path, strict=args.strict)
    if args.json:
        output_format = "json"
    else:
        output_format = args.format
    if output_format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_text(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":  # pragma: no cover - exercised through CLI smoke checks
    sys.exit(main())
