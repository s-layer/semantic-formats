"""Entry points: validation, the normal form and the compact tag payload."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast, get_args

from pydantic import ValidationError

from s_layer_semantic_formats._errors import Issue, SLayerValidationError, SpecTooLongError
from s_layer_semantic_formats._models import (
    KIND_MEMBER_TYPES,
    KINDS,
    MemberType,
    SLayerBlock,
    canonical_json,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from pydantic import JsonValue

__all__ = [
    "MAX_TAG_LENGTH",
    "SPEC_EXCLUDED_KEYS",
    "from_compact_json",
    "member_type_issues",
    "normalize",
    "parse_block",
    "spec_tag_value",
    "to_compact_json",
    "validate_block",
]

MAX_TAG_LENGTH = 256
"""Longest value a Snowflake tag (and so ``S_LAYER_SPEC``) can hold."""

SPEC_EXCLUDED_KEYS: frozenset[str] = frozenset({"label", "synonyms"})
"""Top-level keys that travel outside ``S_LAYER_SPEC`` (``value.kind`` does too)."""

_MEMBER_TYPES: tuple[MemberType, ...] = get_args(MemberType)


def _format_path(loc: Iterable[int | str]) -> str:
    path = ""
    for part in loc:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}" if path else part
    return path


def _issue(detail: Any) -> Issue:
    loc: list[int | str] = list(detail["loc"])
    # A discriminated union puts the chosen tag in the path: value.currency.currency.
    if len(loc) >= 2 and loc[0] == "value" and loc[1] in KINDS:
        del loc[1]
    error_type: str = detail["type"]
    message: str = detail["msg"]
    if error_type == "union_tag_invalid":
        loc.append("kind")
        given: object = detail["input"].get("kind") if isinstance(detail["input"], dict) else None
        message = f"unknown kind {given!r}; expected one of: {', '.join(KINDS)}"
    elif error_type == "union_tag_not_found":
        loc.append("kind")
        message = "required: every block needs value.kind"
    elif error_type == "missing":
        message = "required key is missing"
    return Issue(path=_format_path(loc), message=message)


def _from_pydantic(error: ValidationError) -> SLayerValidationError:
    return SLayerValidationError(_issue(detail) for detail in error.errors(include_url=False))


def parse_block(data: Mapping[str, Any] | SLayerBlock) -> SLayerBlock:
    """
    Parse a block without checking which member type it is attached to.

    Raises:
        SLayerValidationError: The data is not a valid block.
    """
    if isinstance(data, SLayerBlock):
        return data
    try:
        return SLayerBlock.model_validate(data)
    except ValidationError as error:
        raise _from_pydantic(error) from None


def member_type_issues(block: SLayerBlock, member_type: MemberType) -> list[Issue]:
    """List why a valid block cannot be attached to ``member_type`` (empty when it can)."""
    issues: list[Issue] = []
    allowed = KIND_MEMBER_TYPES[block.kind]
    if member_type not in allowed:
        expected = " or ".join(sorted(allowed))
        issues.append(
            Issue(
                "value.kind",
                f"kind {block.kind!r} applies to a {expected}, not a {member_type}",
            )
        )
    if block.aggregation is not None and member_type != "metric":
        issues.append(Issue("aggregation", f"only allowed on a metric, not a {member_type}"))
    return issues


def validate_block(data: Mapping[str, Any] | SLayerBlock, member_type: MemberType) -> SLayerBlock:
    """
    Validate an ``s_layer`` block for a metric, fact or dimension.

    Args:
        data: The block as loaded from YAML or JSON (the value of ``config.meta.s_layer``),
            or an already-parsed block.
        member_type: ``"metric"``, ``"fact"`` or ``"dimension"``.

    Returns:
        The parsed block, with defaults filled in.

    Raises:
        SLayerValidationError: The block is invalid, or its kind does not apply to
            ``member_type``. ``issues`` lists every problem with its path.
        ValueError: ``member_type`` is not one of the three member types.

    Example:
        .. code-block:: python

            block = validate_block({"value": {"kind": "count"}}, "metric")
    """
    if member_type not in _MEMBER_TYPES:
        raise ValueError(f"member_type must be one of {', '.join(_MEMBER_TYPES)}")
    block = parse_block(data)
    issues = member_type_issues(block, member_type)
    if issues:
        raise SLayerValidationError(issues)
    return block


def normalize(block: Mapping[str, Any] | SLayerBlock) -> dict[str, JsonValue]:
    """
    Return the block's normal form as JSON-ready data.

    Defaults are filled in, keys are sorted and decimals are a ``[min, max]`` pair, so
    ``{"max": 2}`` and ``{"min": 0, "max": 2}`` normalise to the same value.

    Raises:
        SLayerValidationError: ``block`` is a mapping that is not a valid block.
    """
    return parse_block(block).normal_form()


def _spec_data(block: SLayerBlock) -> dict[str, JsonValue]:
    data = block.normal_form()
    for key in SPEC_EXCLUDED_KEYS:
        data.pop(key, None)
    value = data["value"]
    assert isinstance(value, dict)
    del value["kind"]
    if not value:
        del data["value"]
    return data


def to_compact_json(block: Mapping[str, Any] | SLayerBlock) -> str:
    """
    Return the ``S_LAYER_SPEC`` payload for Snowflake and DuckDB tags.

    It is the normal form minus ``value.kind``, ``label`` and ``synonyms`` (which travel in
    ``S_LAYER_KIND``, ``S_LAYER_LABEL`` and the native synonyms clause), with sorted keys and
    no whitespace. An empty ``value`` object is left out.

    Example:
        .. code-block:: python

            to_compact_json({"value": {"kind": "currency", "currency": "USD"}})
            # '{"display":{"grouping":true,"negative":"minus"},"value":{"currency":"USD"}}'
    """
    return canonical_json(_spec_data(parse_block(block)))


def spec_tag_value(block: Mapping[str, Any] | SLayerBlock, limit: int = MAX_TAG_LENGTH) -> str:
    """
    Return :func:`to_compact_json`, raising if it does not fit in a tag value.

    Raises:
        SpecTooLongError: The payload is longer than ``limit`` characters. It is never
            truncated.
    """
    spec = to_compact_json(block)
    if len(spec) > limit:
        raise SpecTooLongError(spec, limit)
    return spec


def from_compact_json(
    kind: str,
    spec: str | None,
    *,
    label: str | None = None,
    synonyms: Iterable[str] | None = None,
    member_type: MemberType | None = None,
) -> SLayerBlock:
    """
    Rebuild a block from its tag values: ``S_LAYER_KIND``, ``S_LAYER_SPEC``, ``S_LAYER_LABEL``.

    Args:
        kind: The ``S_LAYER_KIND`` tag value.
        spec: The ``S_LAYER_SPEC`` tag value; ``None`` or ``""`` when the tag is not set.
        label: The ``S_LAYER_LABEL`` tag value, if set.
        synonyms: Synonyms read from the native synonyms clause, if any. An empty list is
            the same as none.
        member_type: When given, also check the kind applies to this member type.

    Raises:
        SLayerValidationError: The payload is not JSON, repeats a key that travels
            elsewhere, or does not make a valid block.
    """
    data: dict[str, Any] = {}
    if spec:
        try:
            loaded: object = json.loads(spec)
        except json.JSONDecodeError as error:
            raise SLayerValidationError([Issue("", f"S_LAYER_SPEC is not JSON: {error}")]) from None
        if not isinstance(loaded, dict):
            raise SLayerValidationError([Issue("", "S_LAYER_SPEC must be a JSON object")])
        data = dict(cast("dict[str, Any]", loaded))
    issues = [
        Issue(key, "must not appear in S_LAYER_SPEC")
        for key in sorted(SPEC_EXCLUDED_KEYS & set(data))
    ]
    value: object = data.get("value", {})
    if not isinstance(value, dict):
        issues.append(Issue("value", "must be a JSON object"))
    elif "kind" in value:
        issues.append(Issue("value.kind", "must not appear in S_LAYER_SPEC; it is S_LAYER_KIND"))
    if issues:
        raise SLayerValidationError(issues)
    assert isinstance(value, dict)
    data["value"] = {"kind": kind, **value}
    if label is not None:
        data["label"] = label
    synonym_list = list(synonyms) if synonyms is not None else []
    if synonym_list:
        data["synonyms"] = synonym_list
    if member_type is None:
        return parse_block(data)
    return validate_block(data, member_type)
