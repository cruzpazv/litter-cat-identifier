import importlib.util
from pathlib import Path

import pytest

_path = Path(__file__).parents[1] / "custom_components/litter_cat_identifier/logic.py"
_spec = importlib.util.spec_from_file_location("logic", _path)
logic = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(logic)

CATS = {"Luna": 3.8, "Simba": 5.5}


@pytest.mark.parametrize(
    ("weight", "expected"),
    [(3.9, "Luna"), (3.2, "Luna"), (5.1, "Simba"), (6.4, "Simba"), (8.0, None), (2.0, None)],
)
def test_identify(weight, expected):
    assert logic.identify(weight, CATS, tolerance=1.0) == expected


def test_identify_empty():
    assert logic.identify(4.0, {}, 1.0) is None


def test_learn_tracks_drift():
    w = 3.8
    for _ in range(30):
        w = logic.learn(w, 4.3, 0.2)
    assert w == pytest.approx(4.3, abs=0.01)


def test_learn_clamps():
    assert logic.learn(4.0, 5.0, 2) == 5.0
    assert logic.learn(4.0, 5.0, -1) == 4.0


@pytest.mark.parametrize(
    ("value", "unit", "kg"),
    [(4.2, "kg", 4.2), (4200, "g", 4.2), (10, "lb", 4.5359237), (4.2, None, 4.2), (4.2, "???", 4.2)],
)
def test_to_kg(value, unit, kg):
    assert logic.to_kg(value, unit) == pytest.approx(kg)


@pytest.mark.parametrize(("raw", "out"), [("4.2", 4.2), ("unknown", None), (None, None), ("nan", None)])
def test_parse_float(raw, out):
    assert logic.parse_float(raw) == out


def test_median():
    assert logic.median([4.3, 4.5, 4.4]) == 4.4
    assert logic.median([4.0, 5.0]) == 4.5


@pytest.mark.parametrize(
    ("weight", "since", "prev", "expected"),
    [
        (1.6, 30, "Luna", ("partial_after_visit", "Luna")),
        (1.6, 60, "Luna", ("partial_after_visit", "Luna")),
        (1.6, 61, "Luna", ("refill_or_partial", None)),
        (1.6, 30, None, ("refill_or_partial", None)),
        (None, 600, "Luna", ("no_weight", None)),
        (None, 10, "Luna", ("partial_after_visit", "Luna")),
    ],
)
def test_classify(weight, since, prev, expected):
    assert logic.classify_unidentified(weight, since, prev, 60) == expected
