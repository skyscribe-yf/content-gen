import re

_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_TOKEN = re.compile(r"(\d+)([dhms])", re.IGNORECASE)


def parse_duration(text: str) -> int:
    if not isinstance(text, str):
        raise TypeError("text must be str")
    s = text.strip()
    if not s:
        raise ValueError("empty duration")
    if s.startswith("-"):
        s = s[1:]
    if s.startswith("+"):
        raise ValueError("sign not allowed")
    parts = _TOKEN.findall(s)
    if not parts:
        raise ValueError("no valid tokens")
    consumed = "".join(f"{n}{u}" for n, u in parts)
    if len(consumed) != len(s.replace(" ", "")):
        raise ValueError("malformed duration")
    total = 0
    seen = set()
    for num, unit in parts:
        u = unit.lower()
        if u in seen:
            raise ValueError("repeated unit")
        seen.add(u)
        total += int(num) * _UNITS[u]
    return total
