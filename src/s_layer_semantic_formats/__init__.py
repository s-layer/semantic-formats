"""
The S-LAYER semantic format vocabulary.

Typed models for the ``s_layer`` block written in dbt ``config.meta`` on metrics, dimensions
and facts, its normal form, the compact ``S_LAYER_SPEC`` tag payload and the JSON Schema.
"""

import warnings
from typing import TYPE_CHECKING

from s_layer_semantic_formats._api import (
    MAX_TAG_LENGTH,
    SPEC_EXCLUDED_KEYS,
    from_compact_json,
    member_type_issues,
    normalize,
    parse_block,
    spec_tag_value,
    to_compact_json,
    validate_block,
)
from s_layer_semantic_formats._errors import (
    Issue,
    SLayerError,
    SLayerValidationError,
    SpecTooLongError,
)
from s_layer_semantic_formats._models import (
    KIND_MEMBER_TYPES,
    KINDS,
    NUMERIC_KINDS,
    TEMPORAL_KINDS,
    Additivity,
    Aggregation,
    BooleanLabels,
    BooleanValue,
    BytesValue,
    CategoryValue,
    CountValue,
    CurrencyValue,
    DatetimeValue,
    DateValue,
    Decimals,
    Display,
    DurationValue,
    GeoValue,
    IdentifierValue,
    Kind,
    MemberType,
    NumberValue,
    PercentageValue,
    QuantityValue,
    ScoreValue,
    SemanticFormat,
    Time,
    Value,
    implied_additivity,
)
from s_layer_semantic_formats._schema import SCHEMA_PATH, json_schema, load_schema, render_schema

if TYPE_CHECKING:
    # Type checkers see the deprecated name as a plain alias; at runtime ``__getattr__`` below
    # resolves it and warns.
    SLayerBlock = SemanticFormat
else:
    # Kept out of type checkers' view so that misspelled imports still fail type checking.
    def __getattr__(name: str) -> object:
        """Resolve ``SLayerBlock``, the deprecated name of `SemanticFormat`, with a warning."""
        if name == "SLayerBlock":
            warnings.warn(
                "SLayerBlock is deprecated and will be removed in a future release; "
                "use SemanticFormat instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return SemanticFormat
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "KINDS",
    "KIND_MEMBER_TYPES",
    "MAX_TAG_LENGTH",
    "NUMERIC_KINDS",
    "SCHEMA_PATH",
    "SPEC_EXCLUDED_KEYS",
    "TEMPORAL_KINDS",
    "Additivity",
    "Aggregation",
    "BooleanLabels",
    "BooleanValue",
    "BytesValue",
    "CategoryValue",
    "CountValue",
    "CurrencyValue",
    "DateValue",
    "DatetimeValue",
    "Decimals",
    "Display",
    "DurationValue",
    "GeoValue",
    "IdentifierValue",
    "Issue",
    "Kind",
    "MemberType",
    "NumberValue",
    "PercentageValue",
    "QuantityValue",
    "SemanticFormat",
    "SLayerError",
    "SLayerValidationError",
    "ScoreValue",
    "SpecTooLongError",
    "Time",
    "Value",
    "from_compact_json",
    "implied_additivity",
    "json_schema",
    "load_schema",
    "member_type_issues",
    "normalize",
    "parse_block",
    "render_schema",
    "spec_tag_value",
    "to_compact_json",
    "validate_block",
]
