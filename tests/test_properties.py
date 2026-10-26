"""Property tests over randomly generated valid blocks."""

from __future__ import annotations

import json
from typing import Any

from hypothesis import given
from jsonschema import Draft202012Validator

from s_layer_semantic_formats import (
    KIND_MEMBER_TYPES,
    from_compact_json,
    load_schema,
    normalize,
    parse_block,
    to_compact_json,
    validate_block,
)
from tests.strategies import blocks

VALIDATOR = Draft202012Validator(load_schema())


@given(blocks)
def test_normalize_is_idempotent(data: dict[str, Any]) -> None:
    once = normalize(data)
    twice = normalize(once)
    assert twice == once
    assert json.dumps(twice, sort_keys=True) == json.dumps(once, sort_keys=True)
    assert parse_block(once) == parse_block(data)


@given(blocks)
def test_compact_json_round_trips(data: dict[str, Any]) -> None:
    block = parse_block(data)
    spec = to_compact_json(block)
    payload = json.loads(spec)
    assert "label" not in payload
    assert "synonyms" not in payload
    assert "kind" not in payload.get("value", {})
    rebuilt = from_compact_json(block.kind, spec, label=block.label, synonyms=block.synonyms)
    assert rebuilt == block
    assert normalize(rebuilt) == normalize(block)
    assert to_compact_json(rebuilt) == spec


@given(blocks)
def test_generated_blocks_validate_for_their_member_types(data: dict[str, Any]) -> None:
    block = parse_block(data)
    for member_type in KIND_MEMBER_TYPES[block.kind]:
        if member_type == "metric" or block.aggregation is None:
            assert validate_block(data, member_type) == block


@given(blocks)
def test_json_schema_accepts_valid_blocks_and_their_normal_form(data: dict[str, Any]) -> None:
    VALIDATOR.validate(data)  # pyright: ignore[reportUnknownMemberType]
    VALIDATOR.validate(normalize(data))  # pyright: ignore[reportUnknownMemberType]
