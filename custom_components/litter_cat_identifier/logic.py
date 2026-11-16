"""Pure helpers, no Home Assistant imports (unit-testable)."""

from __future__ import annotations

_UNIT_TO_KG = {
    "kg": 1.0,
    "g": 0.001,
    "lb": 0.45359237,
    "lbs": 0.45359237,
    "oz": 0.028349523125,
}


def parse_float(value: object) -> float | None:
    """Return a float or None for unknown/unavailable/garbage states."""
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return result


def to_kg(value: float, unit: str | None) -> float:
    """Convert a reading to kilograms. Unknown units are assumed to be kg."""
    if not unit:
        return value
    return value * _UNIT_TO_KG.get(unit.strip().lower(), 1.0)


def identify(weight: float, learned: dict[str, float], tolerance: float) -> str | None:
    """Return the cat whose learned weight is closest, if within tolerance.

    Ties go to the first cat in insertion order.
    """
    best: str | None = None
    best_diff = float("inf")
    for name, ref in learned.items():
        diff = abs(weight - ref)
        if diff < best_diff:
            best, best_diff = name, diff
    if best is None or best_diff > tolerance:
        return None
    return best


def learn(current: float, reading: float, smoothing: float) -> float:
    """Exponential moving average so the reference follows slow weight changes."""
    smoothing = min(max(smoothing, 0.0), 1.0)
    return current * (1.0 - smoothing) + reading * smoothing


def median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        raise ValueError("no values")
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def classify_unidentified(
    weight: float | None,
    seconds_since_previous: float | None,
    previous_cat: str | None,
    window: float,
) -> tuple[str, str | None]:
    """Best guess for an unidentified reading: (reason, likely_cat)."""
    if previous_cat is not None and seconds_since_previous is not None and 0 <= seconds_since_previous <= window:
        return "partial_after_visit", previous_cat
    if weight is None:
        return "no_weight", None
    return "refill_or_partial", None
