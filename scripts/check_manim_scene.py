#!/usr/bin/env python3
"""Command-line entry point for the static Manim scene preflight checker.

The implementation lives in :mod:`manim_timeline`; this thin wrapper keeps a
memorable command name for CI and re-exports :func:`analyze_scene` for scripts
that historically import the checker module.
"""

from __future__ import annotations

import sys
from typing import Sequence

from manim_timeline import analyze_scene, main as _timeline_main


def main(argv: Sequence[str] | None = None) -> int:
    """Run the timeline checker CLI without importing Manim."""

    return _timeline_main(argv)


if __name__ == "__main__":  # pragma: no cover - exercised through CLI smoke checks
    sys.exit(main())


__all__ = ["analyze_scene", "main"]

