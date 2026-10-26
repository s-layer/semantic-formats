"""The block models: kinds, defaults, required keys, strictness and extension keys."""

from __future__ import annotations

from typing import Any

import pytest

from s_layer_semantic_formats import (
    KINDS,
    CurrencyValue,
    Kind,
    SemanticFormat,
    SLayerValidationError,
    implied_additivity,
    parse_block,
)

EXAMPLES: dict[str, dict[str, Any]] = {
    "number": {"kind": "number", "unit": "1"},
    "count": {"kind": "count"},
    "currency": {"kind": "currency", "currency": "USD"},
    "percentage": {"kind": "percentage", "scale": "percent"},
    "duration": {"kind": "duration", "unit": "s"},
    "bytes": {"kind": "bytes", "unit": "KiB"},
    "quantity": {"kind": "quantity", "unit": "km"},
    "score": {"kind": "score", "range": [0, 10]},
    "category": {"kind": "category", "order": ["free", "pro", "enterprise"]},
    "geo": {"kind": "geo", "level": "country", "code": "iso3166-1-alpha-2"},
    "date": {"kind": "date"},
    "datetime": {"kind": "datetime"},
    "identifier": {"kind": "identifier"},
    "boolean": {"kind": "boolean", "labels": {"true": "Returning", "false": "New"}},
}


def issue_paths(data: Any) -> list[str]:
    with pytest.raises(SLayerValidationError) as caught:
        parse_block(data)
    return [issue.path for issue in caught.value.issues]


def test_examples_cover_every_kind() -> None:
    assert set(EXAMPLES) == set(KINDS)
    assert len(KINDS) == 14


@pytest.mark.parametrize("kind", KINDS)
def test_every_kind_parses(kind: str) -> None:
    block = parse_block({"value": EXAMPLES[kind]})
    assert block.kind == kind


def test_value_is_discriminated_on_kind() -> None:
    block = parse_block({"value": {"kind": "currency", "currency": "EUR"}})
    assert isinstance(block.value, CurrencyValue)
    assert block.value.currency == "EUR"


# --- required keys and defaults ---------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "path"),
    [
        ({"kind": "currency"}, "value.currency"),
        ({"kind": "currency", "currency": "usd"}, "value.currency"),
        ({"kind": "currency", "currency": "USDX"}, "value.currency"),
        ({"kind": "quantity"}, "value.unit"),
        ({"kind": "quantity", "unit": ""}, "value.unit"),
        ({"kind": "duration"}, "value.unit"),
        ({"kind": "duration", "unit": "weeks"}, "value.unit"),
        ({"kind": "bytes", "unit": "kb"}, "value.unit"),
        ({"kind": "score"}, "value.range"),
        ({"kind": "score", "range": [10, 0]}, "value.range"),
        ({"kind": "score", "range": [1, 1]}, "value.range"),
        ({"kind": "geo"}, "value.level"),
        ({"kind": "geo", "level": "planet"}, "value.level"),
        ({"kind": "category", "order": []}, "value.order"),
        ({"kind": "category", "order": ["a", "b", "a"]}, "value.order[2]"),
        ({"kind": "boolean", "labels": {"true": "Yes"}}, "value.labels.false"),
        ({"kind": "percentage", "scale": "basis_points"}, "value.scale"),
    ],
)
def test_invalid_value_keys(value: dict[str, Any], path: str) -> None:
    assert path in issue_paths({"value": value})


def test_unknown_kind_is_rejected() -> None:
    with pytest.raises(SLayerValidationError) as caught:
        parse_block({"value": {"kind": "ratio"}})
    (issue,) = caught.value.issues
    assert issue.path == "value.kind"
    assert "unknown kind 'ratio'" in issue.message


def test_missing_kind_and_missing_value() -> None:
    assert issue_paths({"value": {}}) == ["value.kind"]
    assert issue_paths({}) == ["value"]
    assert issue_paths({"value": "currency"}) == ["value"]


def test_kind_specific_defaults() -> None:
    percentage = parse_block({"value": {"kind": "percentage"}})
    assert percentage.value.model_dump()["scale"] == "fraction"
    size = parse_block({"value": {"kind": "bytes"}})
    assert size.value.model_dump()["unit"] == "B"


def test_score_range_accepts_ints_and_floats() -> None:
    block = parse_block({"value": {"kind": "score", "range": [-100, 100.5]}})
    assert block.value.model_dump()["range"] == (-100.0, 100.5)


@pytest.mark.parametrize("bad", [[True, 2], ["0", "10"], [0, float("inf")], [0], [0, 1, 2]])
def test_score_range_rejects_non_numbers(bad: list[Any]) -> None:
    assert issue_paths({"value": {"kind": "score", "range": bad}})


# --- display ----------------------------------------------------------------------------


def test_display_defaults_on_numeric_kinds() -> None:
    block = parse_block({"value": {"kind": "count"}})
    assert block.display is not None
    assert block.display.negative == "minus"
    assert block.display.grouping is True
    assert block.display.decimals is None
    assert block.display.compact is None


def test_identifier_implies_no_grouping() -> None:
    block = parse_block({"value": {"kind": "identifier"}})
    assert block.display is not None
    assert block.display.grouping is False
    assert issue_paths({"value": {"kind": "identifier"}, "display": {"grouping": True}}) == [
        "display.grouping"
    ]


def test_display_absent_on_non_numeric_kinds() -> None:
    assert parse_block({"value": {"kind": "category"}}).display is None


@pytest.mark.parametrize("spelling", [{"max": 2}, {"min": 0, "max": 2}, [0, 2]])
def test_decimals_spellings(spelling: Any) -> None:
    block = parse_block({"value": {"kind": "number"}, "display": {"decimals": spelling}})
    assert block.display is not None
    assert block.display.decimals is not None
    assert block.display.decimals.as_pair() == (0, 2)


@pytest.mark.parametrize(
    ("decimals", "path"),
    [
        ({"min": 3, "max": 1}, "display.decimals.min"),
        ({"min": 1}, "display.decimals.max"),
        ({"max": 21}, "display.decimals.max"),
        ({"max": -1}, "display.decimals.max"),
        ({"max": 2.0}, "display.decimals.max"),
        ({"max": True}, "display.decimals.max"),
        ({"max": 2, "exact": True}, "display.decimals.exact"),
    ],
)
def test_invalid_decimals(decimals: Any, path: str) -> None:
    assert path in issue_paths({"value": {"kind": "number"}, "display": {"decimals": decimals}})


@pytest.mark.parametrize(
    ("kind", "display", "path"),
    [
        ("currency", {"date_style": "iso"}, "display.date_style"),
        ("date", {"decimals": {"max": 0}}, "display.decimals"),
        ("date", {"grouping": False}, "display.grouping"),
        ("category", {"compact": "auto"}, "display.compact"),
        ("geo", {"negative": "parentheses"}, "display.negative"),
        ("identifier", {"decimals": {"max": 0}}, "display.decimals"),
    ],
)
def test_display_keys_must_fit_the_kind(kind: str, display: dict[str, Any], path: str) -> None:
    value = dict(EXAMPLES[kind])
    assert issue_paths({"value": value, "display": display}) == [path]


def test_display_values_are_strict() -> None:
    paths = issue_paths(
        {
            "value": {"kind": "number"},
            "display": {"grouping": "yes", "compact": "huge", "negative": "red"},
        }
    )
    assert sorted(paths) == ["display.compact", "display.grouping", "display.negative"]


# --- time and aggregation ---------------------------------------------------------------


def test_time_on_temporal_kinds() -> None:
    block = parse_block(
        {"value": {"kind": "date"}, "time": {"grain": "month", "fiscal_year_start": 4}}
    )
    assert block.time is not None
    assert block.time.grain == "month"
    assert block.time.fiscal_year_start == 4


@pytest.mark.parametrize(
    ("data", "path"),
    [
        ({"value": {"kind": "currency", "currency": "USD"}, "time": {"grain": "month"}}, "time"),
        ({"value": {"kind": "date"}, "time": {"grain": "hour"}}, "time.grain"),
        ({"value": {"kind": "date"}, "time": {"grain": "fortnight"}}, "time.grain"),
        ({"value": {"kind": "date"}, "time": {"fiscal_year_start": 13}}, "time.fiscal_year_start"),
        ({"value": {"kind": "date"}, "time": {"fiscal_year_start": 0}}, "time.fiscal_year_start"),
        ({"value": {"kind": "date"}, "time": {"fiscal_year_start": "4"}}, "time.fiscal_year_start"),
    ],
)
def test_invalid_time(data: dict[str, Any], path: str) -> None:
    assert issue_paths(data) == [path]


def test_datetime_allows_sub_day_grain() -> None:
    block = parse_block({"value": {"kind": "datetime"}, "time": {"grain": "minute"}})
    assert block.time is not None
    assert block.time.grain == "minute"


def test_semi_additive_needs_by() -> None:
    block = parse_block(
        {
            "value": {"kind": "currency", "currency": "GBP"},
            "aggregation": {"additivity": "semi_additive", "by": ["balance_date"]},
        }
    )
    assert block.aggregation is not None
    assert block.aggregation.by == ["balance_date"]
    count = {"kind": "count"}
    assert issue_paths({"value": count, "aggregation": {"additivity": "semi_additive"}}) == [
        "aggregation.by"
    ]
    assert issue_paths(
        {"value": count, "aggregation": {"additivity": "additive", "by": ["d"]}}
    ) == ["aggregation.by"]
    assert issue_paths(
        {"value": count, "aggregation": {"additivity": "semi_additive", "by": ["d", "d"]}}
    ) == ["aggregation.by[1]"]
    assert issue_paths({"value": count, "aggregation": {}}) == ["aggregation.additivity"]


@pytest.mark.parametrize("kind", ["percentage", "score"])
def test_implied_non_additive_kinds(kind: Kind) -> None:
    assert implied_additivity(kind) == "non_additive"
    block = parse_block({"value": EXAMPLES[kind]})
    assert block.aggregation is None
    assert block.additivity == "non_additive"
    stated = parse_block({"value": EXAMPLES[kind], "aggregation": {"additivity": "non_additive"}})
    assert stated.additivity == "non_additive"
    for additivity in ["additive", "semi_additive"]:
        aggregation: dict[str, Any] = {"additivity": additivity}
        if additivity == "semi_additive":
            aggregation["by"] = ["d"]
        paths = issue_paths({"value": EXAMPLES[kind], "aggregation": aggregation})
        assert paths == ["aggregation.additivity"]


@pytest.mark.parametrize("kind", [k for k in KINDS if k not in {"percentage", "score"}])
def test_other_kinds_imply_nothing(kind: Kind) -> None:
    assert implied_additivity(kind) is None
    assert parse_block({"value": EXAMPLES[kind]}).additivity is None


def test_stated_additivity_wins() -> None:
    block = parse_block({"value": {"kind": "count"}, "aggregation": {"additivity": "additive"}})
    assert block.additivity == "additive"


# --- naming -----------------------------------------------------------------------------


def test_label_and_synonyms() -> None:
    block = parse_block(
        {"value": {"kind": "count"}, "label": "Orders", "synonyms": ["order count", "orders"]}
    )
    assert block.label == "Orders"
    assert block.synonyms == ["order count", "orders"]


@pytest.mark.parametrize(
    ("data", "path"),
    [
        ({"label": ""}, "label"),
        ({"label": "x" * 256}, "label"),
        ({"synonyms": []}, "synonyms"),
        ({"synonyms": ["a", ""]}, "synonyms[1]"),
        ({"synonyms": ["a", "a"]}, "synonyms[1]"),
        ({"synonyms": "a"}, "synonyms"),
    ],
)
def test_invalid_naming(data: dict[str, Any], path: str) -> None:
    assert issue_paths({"value": {"kind": "count"}, **data}) == [path]


# --- unknown and extension keys ---------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "path"),
    [
        ({"value": {"kind": "count"}, "format": "usd"}, "format"),
        ({"value": {"kind": "count", "currency": "USD"}}, "value.currency"),
        ({"value": {"kind": "count"}, "display": {"locale": "en-GB"}}, "display.locale"),
        ({"value": {"kind": "date"}, "time": {"tz": "UTC"}}, "time.tz"),
        (
            {"value": {"kind": "count"}, "aggregation": {"additivity": "additive", "how": 1}},
            "aggregation.how",
        ),
        ({"value": {"kind": "count"}, "x-": 1}, "x-"),
        ({"value": {"kind": "count"}, "X-acme": 1}, "X-acme"),
        (
            {"value": {"kind": "boolean", "labels": {"true": "y", "false": "n", "x-a": 1}}},
            "value.labels.x-a",
        ),
        (
            {"value": {"kind": "number"}, "display": {"decimals": {"max": 1, "x-a": 1}}},
            "display.decimals.x-a",
        ),
    ],
)
def test_unknown_keys_are_rejected(data: dict[str, Any], path: str) -> None:
    assert issue_paths(data) == [path]


def test_unknown_keys_are_reported_with_other_problems() -> None:
    paths = issue_paths(
        {"value": {"kind": "currency", "currency": "usd", "symbol": "$"}, "colour": "red"}
    )
    assert sorted(paths) == ["colour", "value.currency", "value.symbol"]


def test_extension_keys_are_kept_verbatim_at_every_level() -> None:
    payload = {"nested": [1, 2.5, None, {"b": True}], "s": "text"}
    block = parse_block(
        {
            "value": {"kind": "number", "x-acme-unit-label": "widgets"},
            "display": {"x-flint": payload},
            "time": None,
            "aggregation": {"additivity": "additive", "x-acme": 7},
            "x-lightdash": {"hidden": True},
        }
    )
    assert block.extensions == {"x-lightdash": {"hidden": True}}
    assert block.value.extensions == {"x-acme-unit-label": "widgets"}
    assert block.display is not None
    assert block.display.extensions == {"x-flint": payload}
    assert block.aggregation is not None
    assert block.aggregation.extensions == {"x-acme": 7}
    normal = block.normal_form()
    assert normal["x-lightdash"] == {"hidden": True}
    display = normal["display"]
    assert isinstance(display, dict)
    assert display["x-flint"] == payload


def test_extension_values_must_be_json() -> None:
    assert issue_paths({"value": {"kind": "count"}, "x-a": object()})


def test_models_are_frozen() -> None:
    block = parse_block({"value": {"kind": "count"}})
    with pytest.raises(Exception):  # noqa: B017 - pydantic raises its own ValidationError
        block.label = "Orders"


def test_direct_model_validation_raises_pydantic_errors() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SemanticFormat.model_validate({"value": {"kind": "nope"}})


@pytest.mark.parametrize(
    ("with_null", "without"),
    [
        (
            {"value": {"kind": "percentage", "scale": None}},
            {"value": {"kind": "percentage"}},
        ),
        ({"value": {"kind": "bytes", "unit": None}}, {"value": {"kind": "bytes"}}),
        (
            {"value": {"kind": "count"}, "display": {"decimals": {"min": None, "max": 2}}},
            {"value": {"kind": "count"}, "display": {"decimals": {"max": 2}}},
        ),
    ],
)
def test_null_on_a_key_with_a_default_means_absent(
    with_null: dict[str, Any], without: dict[str, Any]
) -> None:
    assert parse_block(with_null) == parse_block(without)


def test_empty_time_is_absent_on_any_kind() -> None:
    block = parse_block({"value": {"kind": "count"}, "time": {}})
    assert block == parse_block({"value": {"kind": "count"}})


def test_semi_additive_without_by_says_why() -> None:
    with pytest.raises(SLayerValidationError) as caught:
        parse_block({"value": {"kind": "count"}, "aggregation": {"additivity": "semi_additive"}})
    [issue] = caught.value.issues
    assert issue.path == "aggregation.by"
    assert issue.message == "required when additivity is semi_additive"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), [1, float("-inf")]])
def test_extension_values_must_be_finite(bad: Any) -> None:
    assert issue_paths({"value": {"kind": "count"}, "x-a": bad}) == ["x-a"]


def test_boolean_labels_accept_yaml_bool_keys() -> None:
    # A YAML 1.1 loader (dbt's) reads unquoted `true:` / `false:` keys as booleans.
    loaded = parse_block({"value": {"kind": "boolean", "labels": {True: "Yes", False: "No"}}})
    quoted = parse_block({"value": {"kind": "boolean", "labels": {"true": "Yes", "false": "No"}}})
    assert loaded == quoted


def test_slayerblock_is_a_deprecated_alias_of_semantic_format() -> None:
    import s_layer_semantic_formats

    with pytest.warns(DeprecationWarning, match="use SemanticFormat instead"):
        alias = s_layer_semantic_formats.SLayerBlock
    assert alias is SemanticFormat


def test_importing_slayerblock_by_name_warns() -> None:
    with pytest.warns(DeprecationWarning, match="SLayerBlock is deprecated"):
        from s_layer_semantic_formats import SLayerBlock
    assert SLayerBlock is SemanticFormat


def test_slayerblock_is_not_exported_by_star_import() -> None:
    import s_layer_semantic_formats

    assert "SLayerBlock" not in s_layer_semantic_formats.__all__
    assert "SemanticFormat" in s_layer_semantic_formats.__all__


def test_unknown_attributes_still_raise() -> None:
    import s_layer_semantic_formats

    with pytest.raises(AttributeError, match="no attribute 'NoSuchName'"):
        getattr(s_layer_semantic_formats, "NoSuchName")  # noqa: B009
