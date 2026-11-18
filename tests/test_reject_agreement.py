"""
The committed JSON Schema and the models agree on what they reject.

The schema checks shape only (see its description); the models add a fixed set of rules
between fields and sections that a JSON Schema cannot state. So for any input, mutated from a
valid block:

- whatever the schema rejects, the models reject too, and
- whatever the models reject while the schema accepts, they reject only for one of those
  model-only rules.

That makes the schema a differential oracle for the models' shape rules, and the models one
for the schema.
"""

from __future__ import annotations

import copy
from typing import Any, cast

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from s_layer_semantic_formats import KINDS, SemanticFormat, load_schema
from tests.strategies import block_for, blocks, json_values

VALIDATOR = Draft202012Validator(load_schema())

MODEL_ONLY_RULES = frozenset(
    {
        "score_range",  # range min < max
        "decimals_bounds",  # decimals min <= max
        "by_required",  # semi_additive needs `by`
        "by_not_allowed",  # `by` only with semi_additive
        "not_applicable",  # time, display keys and grains that do not fit the kind
        "contradicts_kind",  # additivity or grouping the kind rules out
    }
)
"""The models' rules between fields, which the schema's description says it does not check."""

Path = tuple[str | int, ...]


def _children(node: Any) -> list[tuple[str | int, Any]]:
    if isinstance(node, dict):
        return list(cast("dict[str, Any]", node).items())
    if isinstance(node, list):
        return list(enumerate(cast("list[Any]", node)))
    return []


def _paths(node: Any, prefix: Path = ()) -> list[Path]:
    """Every key or index path in a JSON value, parents before children."""
    found: list[Path] = []
    for step, child in _children(node):
        found.append((*prefix, step))
        found.extend(_paths(child, (*prefix, step)))
    return found


def _dicts(node: Any, prefix: Path = ()) -> list[Path]:
    """Every path that holds a JSON object, the root included."""
    found: list[Path] = [prefix] if isinstance(node, dict) else []
    for step, child in _children(node):
        found.extend(_dicts(child, (*prefix, step)))
    return found


def _get(node: Any, path: Path) -> Any:
    for step in path:
        node = node[step]
    return node


@st.composite
def mutated_blocks(draw: st.DrawFn) -> dict[str, Any]:
    """A valid block with one or two mutations applied."""
    data: dict[str, Any] = copy.deepcopy(draw(blocks))
    for _ in range(draw(st.integers(1, 2))):
        mutation = draw(
            st.sampled_from(
                [
                    *("unknown_key", "replace", "drop", "null", "kind", "bad_kind"),
                    # Shape-valid but wrong across fields: these reach the model-only rules.
                    *("graft", "graft", "graft", "swap_bounds", "toggle_by"),
                ]
            )
        )
        if mutation == "graft":
            # Sections generated for another kind: each is valid shape, but may not fit.
            donor = draw(st.sampled_from(KINDS).flatmap(block_for))
            for section in ("display", "time", "aggregation"):
                if section in donor and draw(st.booleans()):
                    data[section] = donor[section]
        elif mutation == "swap_bounds":
            value: Any = data.get("value")
            display: Any = data.get("display")
            if isinstance(value, dict) and isinstance(
                cast("dict[str, Any]", value).get("range"), list
            ):
                value["range"] = value["range"][::-1]
            elif isinstance(display, dict):
                low, high = sorted(draw(st.lists(st.integers(0, 20), min_size=2, max_size=2)))
                display["decimals"] = {"min": high, "max": low}
        elif mutation == "toggle_by":
            aggregation: Any = data.setdefault("aggregation", {"additivity": "additive"})
            if isinstance(aggregation, dict):
                if "by" in aggregation:
                    del aggregation["by"]
                else:
                    aggregation["by"] = ["d"]
        elif mutation == "unknown_key":
            parent = _get(data, draw(st.sampled_from(_dicts(data))))
            key = draw(st.text(min_size=1, max_size=6).filter(lambda k: not k.startswith("x-")))
            parent[key] = draw(json_values)
        elif mutation in {"replace", "drop", "null"} and _paths(data):
            path = draw(st.sampled_from(_paths(data)))
            parent = _get(data, path[:-1])
            if mutation == "drop":
                del parent[path[-1]]
            else:
                parent[path[-1]] = None if mutation == "null" else draw(json_values)
        elif isinstance(value := data.get("value"), dict):
            cast("dict[str, Any]", value)["kind"] = draw(
                st.sampled_from(KINDS)
                if mutation == "kind"
                else st.text(max_size=8).filter(lambda k: k not in KINDS)
            )
    return data


def _model_errors(data: dict[str, Any]) -> set[str] | None:
    """The pydantic error types the models raise, or ``None`` when they accept the data."""
    try:
        SemanticFormat.model_validate(data)
    except ValidationError as error:
        return {detail["type"] for detail in error.errors()}
    return None


@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
@given(mutated_blocks())
def test_schema_and_models_agree_on_rejection(data: dict[str, Any]) -> None:
    schema_accepts = VALIDATOR.is_valid(data)  # pyright: ignore[reportUnknownMemberType]
    errors = _model_errors(data)
    if not schema_accepts:
        assert errors is not None, "the schema rejects a block the models accept"
    if schema_accepts and errors is not None:
        shape_errors = errors - MODEL_ONLY_RULES
        assert not shape_errors, f"the models reject on shape ({shape_errors}), the schema accepts"


@settings(max_examples=200)
@given(blocks, st.data())
def test_both_reject_an_unknown_key_anywhere(data: dict[str, Any], draw: st.DataObject) -> None:
    data = copy.deepcopy(data)
    dicts = [path for path in _dicts(data) if not any(str(s).startswith("x-") for s in path)]
    parent = _get(data, draw.draw(st.sampled_from(dicts)))
    key = draw.draw(st.text(min_size=1, max_size=6).filter(lambda k: not k.startswith("x-")))
    assume(key not in parent)
    parent[key] = 1
    assert not VALIDATOR.is_valid(data)  # pyright: ignore[reportUnknownMemberType]
    errors = _model_errors(data)
    assert errors is not None
    assert "unknown_key" in errors or "extra_forbidden" in errors


@pytest.mark.parametrize("kind", ["", "Currency", "ratio", "count "])
def test_both_reject_an_unknown_kind(kind: str) -> None:
    data = {"value": {"kind": kind}}
    assert not VALIDATOR.is_valid(data)  # pyright: ignore[reportUnknownMemberType]
    assert _model_errors(data) is not None


@pytest.mark.parametrize(
    ("data", "rule"),
    [
        ({"value": {"kind": "score", "range": [5, 1]}}, "score_range"),
        (
            {"value": {"kind": "count"}, "display": {"decimals": {"min": 3, "max": 1}}},
            "decimals_bounds",
        ),
        (
            {"value": {"kind": "count"}, "aggregation": {"additivity": "semi_additive"}},
            "by_required",
        ),
        (
            {"value": {"kind": "count"}, "aggregation": {"additivity": "additive", "by": ["d"]}},
            "by_not_allowed",
        ),
        ({"value": {"kind": "count"}, "time": {"grain": "day"}}, "not_applicable"),
        (
            {"value": {"kind": "percentage"}, "aggregation": {"additivity": "additive"}},
            "contradicts_kind",
        ),
    ],
)
def test_each_model_only_rule_is_real_and_outside_the_schema(
    data: dict[str, Any], rule: str
) -> None:
    """Each allowance in MODEL_ONLY_RULES is a rule the models enforce and the schema does not."""
    assert VALIDATOR.is_valid(data)  # pyright: ignore[reportUnknownMemberType]
    assert _model_errors(data) == {rule}
