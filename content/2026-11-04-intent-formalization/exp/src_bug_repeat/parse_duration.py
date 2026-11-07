import re

_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_TOKEN = re.compile(r"(\d+)([dhms])", re.IGNORECASE)


def parse_duration(text: str) -> int:
    if not isinstance(text, str):
        raise TypeError("text must be str")
    s = text.strip()
    if not s:
        raise ValueError("empty duration")
    if s.startswith("-") or s.startswith("+"):
        raise ValueError("sign not allowed")
    parts = _TOKEN.findall(s)
    if not parts:
        raise ValueError("no valid tokens")
    consumed = "".join(f"{n}{u}" for n, u in parts)
    if len(consumed) != len(s.replace(" ", "")):
        raise ValueError("malformed duration")
    total = 0
    for num, unit in parts:
        total += int(num) * _UNITS[unit.lower()]
    return total
