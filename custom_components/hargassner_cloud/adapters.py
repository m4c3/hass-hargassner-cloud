from __future__ import annotations

import math
import re
from typing import Any

# Zentrale Typ-Adapter (Punkt 14)

_NUM_PATTERN = re.compile(r"^[-+]?\d*(?:[.,]\d+)?$")


def _normalize_num_str(s: str) -> str:
    # "  -1.234,56  " -> "-1234.56"
    s = s.strip().replace(" ", "")
    # Entferne Tausenderpunkte, erlaube nur die letzte Trennstelle als Dezimalpunkt
    s = s.replace(".", "").replace(",", ".")
    return s


def as_float(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return None
        return float(x)
    if isinstance(x, str):
        s = x.strip().lower()
        if s in {"", "nan", "null", "none"}:
            return None
        if not _NUM_PATTERN.match(x.replace(" ", "")):
            # Versuche trotzdem nach Normalisierung
            s2 = _normalize_num_str(x)
            try:
                v = float(s2)
                return None if (math.isnan(v) or math.isinf(v)) else v
            except ValueError:
                return None
        s = _normalize_num_str(x)
        try:
            v = float(s)
            return None if (math.isnan(v) or math.isinf(v)) else v
        except ValueError:
            return None
    return None


def as_int(x: Any) -> int | None:
    f = as_float(x)
    if f is None:
        return None
    return round(f)


def as_bool(x: Any) -> bool | None:
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return bool(x)
    if isinstance(x, str):
        s = x.strip().lower()
        if s in {"true", "on", "1", "yes", "y"}:
            return True
        if s in {"false", "off", "0", "no", "n"}:
            return False
    return None


def as_str(x: Any) -> str | None:
    if x is None:
        return None
    return str(x)
