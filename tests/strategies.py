"""Hypothesis strategies that generate valid ``s_layer`` blocks as plain data."""

from __future__ import annotations

from typing import Any

from hypothesis import strategies as st

from s_layer_semantic_formats import KIND_MEMBER_TYPES, KINDS, NUMERIC_KINDS, TEMPORAL_KINDS, Kind

Data = dict[str, Any]

text = st.text(min_size=1, max_size=8)
json_scalars = (
    st.none()
    | st.booleans()
    | st.integers(min_value=-(2**53), max_value=2**53)
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(max_size=6)
)
json_values = st.recursive(
    json_scalars,
    lambda children: (
        st.lists(children, max_size=3) | st.dictionaries(st.text(max_size=4), children, max_size=3)
    ),
    max_leaves=6,
)
extensions = st.dictionaries(
    st.from_regex(r"x-[a-z][a-z0-9-]{0,6}", fullmatch=True), json_values, max_size=2
)
unique_texts = st.lists(text, min_size=1, max_size=4, unique=True)


def _with_extensions(fields: st.SearchStrategy[Data]) -> st.SearchStrategy[Data]:
    return st.tuples(fields, extensions).map(lambda pair: {**pair[0], **pair[1]})


def _score_range() -> st.SearchStrategy[list[float]]:
    number = st.integers(-100, 100) | st.floats(-1e6, 1e6, allow_nan=False)
    return st.tuples(number, number).filter(lambda pair: pair[0] != pair[1]).map(sorted)


_REQUIRED: dict[str, dict[str, st.SearchStrategy[Any]]] = {
    "currency": {"currency": st.from_regex(r"[A-Z]{3}", fullmatch=True)},
    "duration": {"unit": st.sampled_from(["ms", "s", "min", "h", "d"])},
    "quantity": {"unit": st.sampled_from(["km", "kg", "m/s", "[degF]", "L"]) | text},
    "score": {"range": _score_range()},
    "geo": {
        "level": st.sampled_from(
            ["country", "region", "state", "city", "postal_code", "latitude", "longitude"]
        )
    },
}
_OPTIONAL: dict[str, dict[str, st.SearchStrategy[Any]]] = {
    "number": {"unit": text},
    "percentage": {"scale": st.sampled_from(["fraction", "percent"])},
    "bytes": {"unit": st.sampled_from(["B", "KB", "MB", "GiB", "TiB"])},
    "category": {"order": unique_texts},
    "geo": {"code": st.sampled_from(["iso3166-1-alpha-2", "iso3166-1-alpha-3"]) | text},
    "boolean": {"labels": st.fixed_dictionaries({"true": text, "false": text})},
}


def value_for(kind: Kind) -> st.SearchStrategy[Data]:
    return _with_extensions(
        st.fixed_dictionaries(
            {"kind": st.just(kind), **_REQUIRED.get(kind, {})},
            optional=_OPTIONAL.get(kind, {}),
        )
    )


def decimals() -> st.SearchStrategy[Any]:
    pair = st.tuples(st.integers(0, 20), st.integers(0, 20)).map(sorted)
    return (
        pair.map(list)
        | pair.map(lambda p: {"min": p[0], "max": p[1]})
        | pair.map(lambda p: {"max": p[1]})
    )


def display_for(kind: Kind) -> st.SearchStrategy[Data]:
    keys: dict[str, st.SearchStrategy[Any]] = {}
    if kind in NUMERIC_KINDS:
        keys |= {
            "decimals": decimals(),
            "compact": st.sampled_from(["none", "auto", "thousands", "millions", "billions"]),
            "negative": st.sampled_from(["minus", "parentheses"]),
            "grouping": st.booleans(),
        }
    if kind == "identifier":
        keys["grouping"] = st.just(False)
    if kind in TEMPORAL_KINDS:
        keys["date_style"] = st.sampled_from(["short", "medium", "long", "iso"])
    return _with_extensions(st.fixed_dictionaries({}, optional=keys))


def time_for(kind: Kind) -> st.SearchStrategy[Data]:
    grains = ["day", "week", "month", "quarter", "year"]
    if kind == "datetime":
        grains = ["second", "minute", "hour", *grains]
    return _with_extensions(
        st.fixed_dictionaries(
            {},
            optional={
                "grain": st.sampled_from(grains),
                "fiscal_year_start": st.integers(1, 12),
            },
        )
    )


def aggregation_for(kind: Kind) -> st.SearchStrategy[Data]:
    if kind in {"percentage", "score"}:
        plain = st.just({"additivity": "non_additive"})
    else:
        plain = st.sampled_from([{"additivity": "additive"}, {"additivity": "non_additive"}])
    semi = unique_texts.map(lambda by: {"additivity": "semi_additive", "by": by})
    if kind in {"percentage", "score"}:
        return _with_extensions(plain)
    return _with_extensions(plain | semi)


def block_for(kind: Kind) -> st.SearchStrategy[Data]:
    optional: dict[str, st.SearchStrategy[Any]] = {
        "display": display_for(kind),
        "label": st.text(min_size=1, max_size=40),
        "synonyms": unique_texts,
    }
    if kind in TEMPORAL_KINDS:
        optional["time"] = time_for(kind)
    if "metric" in KIND_MEMBER_TYPES[kind]:
        optional["aggregation"] = aggregation_for(kind)
    return _with_extensions(st.fixed_dictionaries({"value": value_for(kind)}, optional=optional))


blocks: st.SearchStrategy[Data] = st.sampled_from(KINDS).flatmap(block_for)
"""Any valid block, as the plain data a YAML or JSON loader would produce."""
