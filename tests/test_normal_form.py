"""The normal form, equality and the compact ``S_LAYER_SPEC`` payload."""

from __future__ import annotations

import json
from typing import Any

import pytest

from s_layer_semantic_formats import (
    MAX_TAG_LENGTH,
    SLayerValidationError,
    SpecTooLongError,
    from_compact_json,
    normalize,
    parse_block,
    spec_tag_value,
    to_compact_json,
)

USD = {"kind": "currency", "currency": "USD"}


def test_decimals_bound_spellings_are_equal() -> None:
    short = parse_block({"value": USD, "display": {"decimals": {"max": 2}}})
    full = parse_block({"value": USD, "display": {"decimals": {"min": 0, "max": 2}}})
    pair = parse_block({"value": USD, "display": {"decimals": [0, 2]}})
    assert short == full == pair
    assert hash(short) == hash(full) == hash(pair)
    assert normalize(short)["display"] == {
        "decimals": [0, 2],
        "grouping": True,
        "negative": "minus",
    }


def test_defaults_make_blocks_equal() -> None:
    implicit = parse_block({"value": {"kind": "percentage"}})
    explicit = parse_block(
        {
            "value": {"kind": "percentage", "scale": "fraction"},
            "display": {"negative": "minus", "grouping": True},
        }
    )
    assert implicit == explicit
    assert parse_block({"value": {"kind": "bytes"}}) == parse_block(
        {"value": {"kind": "bytes", "unit": "B"}}
    )
    assert parse_block({"value": {"kind": "identifier"}}) == parse_block(
        {"value": {"kind": "identifier"}, "display": {"grouping": False}}
    )
    assert parse_block({"value": {"kind": "category"}}) == parse_block(
        {"value": {"kind": "category"}, "display": {}, "time": None}
    )


def test_different_blocks_are_not_equal() -> None:
    assert parse_block({"value": USD}) != parse_block(
        {"value": {"kind": "currency", "currency": "EUR"}}
    )
    assert parse_block({"value": USD}) != parse_block({"value": USD, "label": "Revenue"})
    assert parse_block({"value": {"kind": "count"}, "x-a": 1}) != parse_block(
        {"value": {"kind": "count"}, "x-a": 1.0}
    )
    assert parse_block({"value": USD}) != {"value": USD}


def test_normal_form_shape() -> None:
    data = {
        "x-z": {"b": 1, "a": [3, 1]},
        "synonyms": ["sales", "turnover"],
        "label": "Revenue",
        "value": {"currency": "USD", "kind": "currency"},
        "display": {"compact": "auto", "decimals": {"max": 0}},
    }
    normal = normalize(data)
    assert normal == {
        "display": {"compact": "auto", "decimals": [0, 0], "grouping": True, "negative": "minus"},
        "label": "Revenue",
        "synonyms": ["sales", "turnover"],
        "value": {"currency": "USD", "kind": "currency"},
        "x-z": {"a": [3, 1], "b": 1},
    }
    assert list(normal) == sorted(normal)
    display, extension = normal["display"], normal["x-z"]
    assert isinstance(display, dict)
    assert isinstance(extension, dict)
    assert list(display) == sorted(display)
    assert list(extension) == ["a", "b"]
    assert json.loads(json.dumps(normal)) == normal


def test_normal_form_keeps_list_order() -> None:
    normal = normalize(
        {
            "value": {"kind": "count"},
            "aggregation": {"additivity": "semi_additive", "by": ["z_date", "a_account"]},
        }
    )
    assert normal["aggregation"] == {"additivity": "semi_additive", "by": ["z_date", "a_account"]}
    order = normalize({"value": {"kind": "category", "order": ["low", "mid", "high"]}})
    assert order["value"] == {"kind": "category", "order": ["low", "mid", "high"]}


def test_whole_number_score_bounds_are_integers() -> None:
    normal = normalize({"value": {"kind": "score", "range": [0.0, 10]}})
    assert normal["value"] == {"kind": "score", "range": [0, 10]}
    assert to_compact_json({"value": {"kind": "score", "range": [1, 5.5]}}) == (
        '{"display":{"grouping":true,"negative":"minus"},"value":{"range":[1,5.5]}}'
    )


def test_normalize_rejects_invalid_data() -> None:
    with pytest.raises(SLayerValidationError):
        normalize({"value": {"kind": "currency"}})


# --- compact JSON ----------------------------------------------------------------------


def test_compact_json_matches_the_design_doc_example() -> None:
    block = {"value": USD, "display": {"decimals": {"min": 0, "max": 0}, "compact": "auto"}}
    assert to_compact_json(block) == (
        '{"display":{"compact":"auto","decimals":[0,0],"grouping":true,"negative":"minus"},'
        '"value":{"currency":"USD"}}'
    )


def test_compact_json_drops_kind_label_and_synonyms() -> None:
    block = {"value": {"kind": "date"}, "label": "Order month", "synonyms": ["month"]}
    assert to_compact_json(block) == "{}"
    spec = to_compact_json({**block, "time": {"grain": "month"}})
    assert spec == '{"time":{"grain":"month"}}'
    assert to_compact_json({"value": {"kind": "date", "x-a": 1}}) == '{"value":{"x-a":1}}'


def test_compact_json_keeps_non_ascii_text() -> None:
    spec = to_compact_json({"value": {"kind": "category", "order": ["niño", "日本"]}})
    assert spec == '{"value":{"order":["niño","日本"]}}'


@pytest.mark.parametrize(
    "data",
    [
        {"value": USD, "label": "Revenue", "synonyms": ["sales"]},
        {"value": {"kind": "count"}},
        {"value": {"kind": "date"}, "time": {"grain": "quarter", "fiscal_year_start": 4}},
        {"value": {"kind": "identifier"}},
        {"value": {"kind": "geo", "level": "country", "code": "iso3166-1-alpha-2"}},
        {
            "value": {"kind": "bytes", "unit": "GiB", "x-acme": {"k": [1, None]}},
            "display": {"compact": "auto", "decimals": [1, 2]},
            "aggregation": {"additivity": "semi_additive", "by": ["snapshot_date"]},
            "x-top": True,
        },
    ],
)
def test_compact_json_round_trips(data: dict[str, Any]) -> None:
    block = parse_block(data)
    spec = to_compact_json(block)
    rebuilt = from_compact_json(block.kind, spec, label=block.label, synonyms=block.synonyms)
    assert rebuilt == block
    assert normalize(rebuilt) == normalize(block)


def test_from_compact_json_without_a_spec() -> None:
    assert from_compact_json("count", None) == parse_block({"value": {"kind": "count"}})
    assert from_compact_json("date", "") == parse_block({"value": {"kind": "date"}})
    assert from_compact_json("date", "{}", synonyms=[]) == parse_block({"value": {"kind": "date"}})


def test_from_compact_json_checks_member_type() -> None:
    assert from_compact_json("count", "{}", member_type="metric").kind == "count"
    with pytest.raises(SLayerValidationError):
        from_compact_json("count", "{}", member_type="dimension")


@pytest.mark.parametrize(
    ("kind", "spec", "path"),
    [
        ("count", "not json", ""),
        ("count", "[1, 2]", ""),
        ("count", '{"label": "Orders"}', "label"),
        ("count", '{"synonyms": ["orders"]}', "synonyms"),
        ("count", '{"value": {"kind": "count"}}', "value.kind"),
        ("count", '{"value": 3}', "value"),
        ("ratio", "{}", "value.kind"),
        ("currency", "{}", "value.currency"),
        ("count", '{"display": {"colour": "red"}}', "display.colour"),
    ],
)
def test_from_compact_json_rejects_bad_payloads(kind: str, spec: str, path: str) -> None:
    with pytest.raises(SLayerValidationError) as caught:
        from_compact_json(kind, spec)
    assert path in [issue.path for issue in caught.value.issues]


def test_spec_tag_value_enforces_the_tag_limit() -> None:
    block = {"value": USD, "display": {"compact": "auto"}}
    assert spec_tag_value(block) == to_compact_json(block)
    long_order = [f"tier-{index:03d}" for index in range(40)]
    long_block = {"value": {"kind": "category", "order": long_order}}
    assert len(to_compact_json(long_block)) > MAX_TAG_LENGTH
    with pytest.raises(SpecTooLongError) as caught:
        spec_tag_value(long_block)
    assert caught.value.limit == 256
    assert caught.value.spec == to_compact_json(long_block)
    assert "over the 256-character tag limit" in str(caught.value)


def test_spec_tag_value_limit_is_inclusive() -> None:
    block = {"value": {"kind": "count"}}
    spec = to_compact_json(block)
    assert spec_tag_value(block, limit=len(spec)) == spec
    with pytest.raises(SpecTooLongError):
        spec_tag_value(block, limit=len(spec) - 1)
