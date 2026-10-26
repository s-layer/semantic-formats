"""``validate_block``: member types and readable error paths."""

from __future__ import annotations

from typing import Any

import pytest

from s_layer_semantic_formats import (
    KIND_MEMBER_TYPES,
    KINDS,
    Issue,
    MemberType,
    SLayerError,
    SLayerValidationError,
    parse_block,
    validate_block,
)
from tests.test_models import EXAMPLES

MEMBER_TYPES: tuple[MemberType, ...] = ("metric", "fact", "dimension")

APPLIES_TO = {
    "number": {"metric", "fact"},
    "count": {"metric"},
    "currency": {"metric", "fact"},
    "percentage": {"metric"},
    "duration": {"metric", "fact"},
    "bytes": {"metric"},
    "quantity": {"metric", "fact"},
    "score": {"metric"},
    "category": {"dimension"},
    "geo": {"dimension"},
    "date": {"dimension"},
    "datetime": {"dimension"},
    "identifier": {"dimension"},
    "boolean": {"dimension"},
}


def test_applicability_table_matches_the_design_doc() -> None:
    assert {kind: set(types) for kind, types in KIND_MEMBER_TYPES.items()} == APPLIES_TO


@pytest.mark.parametrize("member_type", MEMBER_TYPES)
@pytest.mark.parametrize("kind", KINDS)
def test_kind_applies_to_member_type(kind: str, member_type: MemberType) -> None:
    data = {"value": EXAMPLES[kind]}
    if member_type in APPLIES_TO[kind]:
        assert validate_block(data, member_type).kind == kind
    else:
        with pytest.raises(SLayerValidationError) as caught:
            validate_block(data, member_type)
        (issue,) = caught.value.issues
        assert issue.path == "value.kind"
        assert f"not a {member_type}" in issue.message


@pytest.mark.parametrize("member_type", ["fact", "dimension"])
def test_aggregation_only_on_metrics(member_type: MemberType) -> None:
    kind = "number" if member_type == "fact" else "category"
    data = {"value": EXAMPLES[kind], "aggregation": {"additivity": "non_additive"}}
    with pytest.raises(SLayerValidationError) as caught:
        validate_block(data, member_type)
    assert [issue.path for issue in caught.value.issues] == ["aggregation"]
    assert validate_block(
        {"value": EXAMPLES["number"], "aggregation": {"additivity": "non_additive"}}, "metric"
    )


def test_wrong_kind_and_aggregation_are_both_reported() -> None:
    with pytest.raises(SLayerValidationError) as caught:
        validate_block(
            {"value": {"kind": "count"}, "aggregation": {"additivity": "additive"}}, "fact"
        )
    assert [issue.path for issue in caught.value.issues] == ["value.kind", "aggregation"]


def test_error_lists_every_problem_with_its_path() -> None:
    data: dict[str, Any] = {
        "value": {"kind": "currency", "currency": "dollars"},
        "display": {"decimals": {"min": 4, "max": 2}, "compact": "lots"},
        "synonyms": ["rev", "rev"],
        "colour": "green",
    }
    with pytest.raises(SLayerValidationError) as caught:
        validate_block(data, "metric")
    error = caught.value
    assert sorted(issue.path for issue in error.issues) == [
        "colour",
        "display.compact",
        "display.decimals.min",
        "synonyms[1]",
        "value.currency",
    ]
    text = str(error)
    assert text.startswith("invalid s_layer block (5 problems):")
    assert "  value.currency: String should match pattern '^[A-Z]{3}$'" in text
    assert isinstance(error, SLayerError)
    assert isinstance(error, ValueError)


def test_root_level_problems_have_an_empty_path() -> None:
    with pytest.raises(SLayerValidationError) as caught:
        validate_block(["not", "a", "mapping"], "metric")  # pyright: ignore[reportArgumentType]
    (issue,) = caught.value.issues
    assert issue.path == ""
    assert str(issue).startswith("(block): ")


def test_single_problem_message() -> None:
    error = SLayerValidationError([Issue("value.kind", "required")])
    assert str(error) == "invalid s_layer block (1 problem):\n  value.kind: required"


def test_unknown_member_type() -> None:
    with pytest.raises(ValueError, match="member_type"):
        validate_block({"value": {"kind": "count"}}, "measure")  # pyright: ignore[reportArgumentType]


def test_accepts_a_parsed_block() -> None:
    block = parse_block({"value": {"kind": "count"}})
    assert validate_block(block, "metric") is block
    with pytest.raises(SLayerValidationError):
        validate_block(block, "dimension")
