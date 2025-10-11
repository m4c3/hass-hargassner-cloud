from __future__ import annotations
from typing import Any, Dict, List

# Gemeinsame Helper (Punkt 11: Mapping kapseln & Wiederverwendung)

def widgets(root: Dict[str, Any]) -> List[Dict[str, Any]]:
    return (root or {}).get("data") or []

def find_widget(root: Dict[str, Any], widget: str, number: str | None = None) -> Dict[str, Any] | None:
    for w in widgets(root):
        if w.get("widget") != widget:
            continue
        if number is not None and str(w.get("number")) != str(number):
            continue
        return w
    return None

def value_at(root: Dict[str, Any], widget: str, field: str, number: str | None = None):
    w = find_widget(root, widget, number)
    return (w.get("values") or {}).get(field) if w else None

def first_of(*vals):
    for v in vals:
        if v is not None:
            return v
    return None

def apply_overrides(default: dict, overrides: dict | None) -> dict:
    """Gibt ein neues Dict mit überschriebenen Feldern zurück (widget/field/number)."""
    if not overrides:
        return default
    out = dict(default)
    for k, v in overrides.items():
        if not isinstance(v, dict):
            continue
        out[k] = {**out.get(k, {}), **{kk: vv for kk, vv in v.items() if kk in {"widget", "field", "number"}}}
    return out
