from __future__ import annotations

import math

import pytest

from custom_components.hargassner_cloud.adapters import (
    as_bool,
    as_float,
    as_int,
    as_str,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("12,5", 12.5),
        ("1.234,5", 1234.5),
        (-2, -2.0),
        (math.nan, None),
        (math.inf, None),
        ("invalid", None),
    ],
)
def test_as_float(value: object, expected: float | None) -> None:
    assert as_float(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1.6, 2), ("2,4", 2), (None, None), ("invalid", None)],
)
def test_as_int(value: object, expected: int | None) -> None:
    assert as_int(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(True, True), (0, False), ("yes", True), ("off", False), ("unknown", None)],
)
def test_as_bool(value: object, expected: bool | None) -> None:
    assert as_bool(value) is expected


def test_as_str() -> None:
    assert as_str(42) == "42"
    assert as_str(None) is None
