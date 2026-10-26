"""Typed pydantic models for the ``s_layer`` block."""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Annotated, Any, Literal, LiteralString, Self, cast, get_args

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    JsonValue,
    ModelWrapValidatorHandler,
    StringConstraints,
    ValidationError,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError

if TYPE_CHECKING:
    from pydantic.config import JsonDict

__all__ = [
    "KINDS",
    "KIND_MEMBER_TYPES",
    "NUMERIC_KINDS",
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
    "Kind",
    "MemberType",
    "NumberValue",
    "PercentageValue",
    "QuantityValue",
    "SLayerBlock",
    "ScoreValue",
    "Time",
    "Value",
    "implied_additivity",
]

# --------------------------------------------------------------------------------------
# Closed lists
# --------------------------------------------------------------------------------------

Kind = Literal[
    "number",
    "count",
    "currency",
    "percentage",
    "duration",
    "bytes",
    "quantity",
    "score",
    "category",
    "geo",
    "date",
    "datetime",
    "identifier",
    "boolean",
]
"""Every ``value.kind``, in the design doc's order."""

KINDS: tuple[Kind, ...] = get_args(Kind)

MemberType = Literal["metric", "fact", "dimension"]
"""The semantic-view member types a block can be attached to."""

KIND_MEMBER_TYPES: Mapping[Kind, frozenset[MemberType]] = {
    "number": frozenset({"metric", "fact"}),
    "count": frozenset({"metric"}),
    "currency": frozenset({"metric", "fact"}),
    "percentage": frozenset({"metric"}),
    "duration": frozenset({"metric", "fact"}),
    "bytes": frozenset({"metric"}),
    "quantity": frozenset({"metric", "fact"}),
    "score": frozenset({"metric"}),
    "category": frozenset({"dimension"}),
    "geo": frozenset({"dimension"}),
    "date": frozenset({"dimension"}),
    "datetime": frozenset({"dimension"}),
    "identifier": frozenset({"dimension"}),
    "boolean": frozenset({"dimension"}),
}
"""Which member types each kind applies to (the "Applies to" column of the design doc)."""

NUMERIC_KINDS: frozenset[Kind] = frozenset(
    {"number", "count", "currency", "percentage", "duration", "bytes", "quantity", "score"}
)
"""Kinds whose values are numbers, so number display hints apply to them."""

TEMPORAL_KINDS: frozenset[Kind] = frozenset({"date", "datetime"})
"""Kinds that are a temporal axis, so ``time`` and ``display.date_style`` apply to them."""

Additivity = Literal["additive", "semi_additive", "non_additive"]
Grain = Literal["second", "minute", "hour", "day", "week", "month", "quarter", "year"]
SUB_DAY_GRAINS: frozenset[str] = frozenset({"second", "minute", "hour"})
Compact = Literal["none", "auto", "thousands", "millions", "billions"]
Negative = Literal["minus", "parentheses"]
DateStyle = Literal["short", "medium", "long", "iso"]
PercentageScale = Literal["fraction", "percent"]
DurationUnit = Literal["ms", "s", "min", "h", "d"]
BytesUnit = Literal[
    "B", "KB", "MB", "GB", "TB", "PB", "EB", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"
]
GeoLevel = Literal["country", "region", "state", "city", "postal_code", "latitude", "longitude"]

IMPLIED_NON_ADDITIVE: frozenset[Kind] = frozenset({"percentage", "score"})

MAX_DECIMALS = 20
MAX_LABEL_LENGTH = 255
EXTENSION_PREFIX = "x-"

NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Label = Annotated[str, StringConstraints(min_length=1, max_length=MAX_LABEL_LENGTH)]
DecimalPlaces = Annotated[int, Field(strict=True, ge=0, le=MAX_DECIMALS)]
FiniteNumber = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Month = Annotated[int, Field(strict=True, ge=1, le=12)]
StrictBoolean = Annotated[bool, Field(strict=True)]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    errors: list[InitErrorDetails] = []
    for index, item in enumerate(values):
        if item in seen:
            errors.append(_custom_error((index,), "duplicate", f"duplicate entry {item!r}", item))
        seen.add(item)
    _raise("list", errors)
    return values


UniqueTexts = Annotated[
    list[NonEmptyStr],
    Field(min_length=1, json_schema_extra={"uniqueItems": True}),
    AfterValidator(_unique),
]
"""A non-empty list of distinct, non-empty strings, in a meaningful order."""


def implied_additivity(kind: Kind) -> Additivity | None:
    """
    Return the additivity a kind implies on its own, or ``None`` when it implies nothing.

    ``percentage`` and ``score`` imply ``non_additive``. Any other derivation (from dbt
    metric types, ``non_additive_dimension`` or ``NON ADDITIVE BY``) belongs to the tool
    that reads those definitions, not to this vocabulary.

    Example:
        .. code-block:: python

            implied_additivity("percentage")  # "non_additive"
            implied_additivity("currency")  # None
    """
    return "non_additive" if kind in IMPLIED_NON_ADDITIVE else None


# --------------------------------------------------------------------------------------
# Shared base: unknown keys are errors, ``x-`` keys are kept verbatim
# --------------------------------------------------------------------------------------


def _is_extension_key(key: object) -> bool:
    return isinstance(key, str) and key.startswith(EXTENSION_PREFIX) and len(key) > 2


def _extension_schema(schema: JsonDict) -> None:
    schema["additionalProperties"] = False
    schema["patternProperties"] = {f"^{EXTENSION_PREFIX}.+": {}}


def _custom_error(
    loc: tuple[str | int, ...], kind: str, message: str, value: object
) -> InitErrorDetails:
    return InitErrorDetails(
        type=PydanticCustomError(cast("LiteralString", kind), cast("LiteralString", message)),
        loc=loc,
        input=value,
    )


def _reraisable(error: ValidationError) -> list[InitErrorDetails]:
    """Turn a caught error's details back into ones that can be raised again."""
    return [
        InitErrorDetails(
            type=PydanticCustomError(
                cast("LiteralString", detail["type"]), cast("LiteralString", detail["msg"])
            ),
            loc=detail["loc"],
            input=detail["input"],
        )
        for detail in error.errors(include_url=False)
    ]


def _raise(title: str, errors: list[InitErrorDetails]) -> None:
    if errors:
        raise ValidationError.from_exception_data(title, errors)


class _Strict(BaseModel):
    """Closed object: no extra keys at all."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class _Extensible(BaseModel):
    """Closed object that also carries ``x-`` extension keys verbatim."""

    model_config = ConfigDict(extra="allow", frozen=True, json_schema_extra=_extension_schema)

    __pydantic_extra__: dict[str, JsonValue] = Field(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

    @model_validator(mode="wrap")
    @classmethod
    def _reject_unknown_keys(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        if not isinstance(data, Mapping):
            return handler(data)
        mapping = cast("Mapping[object, object]", data)
        unknown = [
            key for key in mapping if key not in cls.model_fields and not _is_extension_key(key)
        ]
        if not unknown:
            return handler(data)
        errors = [
            _custom_error(
                (key if isinstance(key, str) else str(key),),
                "unknown_key",
                "unknown key; only 'x-' extension keys may be added",
                mapping[key],
            )
            for key in unknown
        ]
        known = {key: item for key, item in mapping.items() if key not in unknown}
        try:
            handler(known)
        except ValidationError as error:
            errors.extend(_reraisable(error))
        _raise(cls.__name__, errors)
        raise AssertionError("unreachable")  # pragma: no cover

    @property
    def extensions(self) -> dict[str, JsonValue]:
        """The ``x-`` keys on this object, verbatim."""
        return dict(self.__pydantic_extra__ or {})


# --------------------------------------------------------------------------------------
# value: one model per kind, discriminated on ``kind``
# --------------------------------------------------------------------------------------


class NumberValue(_Extensible):
    """Generic quantity, decimal."""

    kind: Literal["number"]
    unit: NonEmptyStr | None = Field(default=None, description="Optional unit, as a UCUM code.")


class CountValue(_Extensible):
    """Whole number of things, zero baseline."""

    kind: Literal["count"]


class CurrencyValue(_Extensible):
    """Money amount."""

    kind: Literal["currency"]
    currency: CurrencyCode = Field(description="ISO-4217 currency code, such as USD.")


class PercentageValue(_Extensible):
    """A proportion; never summed."""

    kind: Literal["percentage"]
    scale: PercentageScale = Field(
        default="fraction", description="Whether 0.12 (fraction) or 12 (percent) means 12%."
    )


class DurationValue(_Extensible):
    """Elapsed time."""

    kind: Literal["duration"]
    unit: DurationUnit


class BytesValue(_Extensible):
    """Data size; compacts in 1000 or 1024 steps."""

    kind: Literal["bytes"]
    unit: BytesUnit = "B"


class QuantityValue(_Extensible):
    """Physical measure with a unit."""

    kind: Literal["quantity"]
    unit: NonEmptyStr = Field(description="UCUM unit code, such as km or kg.")


class ScoreValue(_Extensible):
    """Bounded scale; averaged, not summed."""

    kind: Literal["score"]
    range: tuple[FiniteNumber, FiniteNumber] = Field(description="[min, max], with min < max.")

    @model_validator(mode="after")
    def _check_range(self) -> Self:
        low, high = self.range
        if not low < high:
            _raise(
                type(self).__name__,
                [_custom_error(("range",), "score_range", "min must be less than max", self.range)],
            )
        return self


class CategoryValue(_Extensible):
    """Nominal or ordered label."""

    kind: Literal["category"]
    order: UniqueTexts | None = Field(
        default=None, description="Category values in order; makes the category ordinal."
    )


class GeoValue(_Extensible):
    """Place; enables maps."""

    kind: Literal["geo"]
    level: GeoLevel
    code: NonEmptyStr | None = Field(
        default=None, description="Coding scheme of the values, such as iso3166-1-alpha-2."
    )


class DateValue(_Extensible):
    """Temporal axis, calendar dates."""

    kind: Literal["date"]


class DatetimeValue(_Extensible):
    """Temporal axis, timestamps."""

    kind: Literal["datetime"]


class IdentifierValue(_Extensible):
    """Shown without grouping; never aggregated."""

    kind: Literal["identifier"]


class BooleanLabels(_Strict):
    """Display labels for the two values of a flag."""

    true: NonEmptyStr
    false: NonEmptyStr


class BooleanValue(_Extensible):
    """Two-valued flag."""

    kind: Literal["boolean"]
    labels: BooleanLabels | None = None


Value = Annotated[
    NumberValue
    | CountValue
    | CurrencyValue
    | PercentageValue
    | DurationValue
    | BytesValue
    | QuantityValue
    | ScoreValue
    | CategoryValue
    | GeoValue
    | DateValue
    | DatetimeValue
    | IdentifierValue
    | BooleanValue,
    Field(discriminator="kind"),
]
"""What the value means: one of the kind models, chosen by ``kind``."""


# --------------------------------------------------------------------------------------
# display, time, aggregation
# --------------------------------------------------------------------------------------


class Decimals(_Strict):
    """
    Fraction digits as a bound. ``min`` defaults to 0; ``min == max`` is exact.

    Accepts ``{min, max}`` or a ``[min, max]`` pair. The normal form is the pair.
    """

    min: DecimalPlaces = 0
    max: DecimalPlaces

    @model_validator(mode="after")
    def _check_bounds(self) -> Self:
        if self.min > self.max:
            _raise(
                type(self).__name__,
                [_custom_error(("min",), "decimals_bounds", "min must not exceed max", self.min)],
            )
        return self

    def as_pair(self) -> tuple[int, int]:
        """Return ``(min, max)``."""
        return (self.min, self.max)


def _decimals_from_pair(value: object) -> object:
    if not isinstance(value, list | tuple):
        return value
    items = cast("list[object] | tuple[object, ...]", value)
    if len(items) != 2:
        return items
    return {"min": items[0], "max": items[1]}


DecimalsInput = Annotated[
    Decimals,
    BeforeValidator(
        _decimals_from_pair,
        json_schema_input_type=Decimals | tuple[DecimalPlaces, DecimalPlaces],
    ),
]

DISPLAY_NUMBER_KEYS: frozenset[str] = frozenset({"decimals", "compact", "negative"})


class Display(_Extensible):
    """Rendering hints. All optional; meaning lives in ``value``."""

    decimals: DecimalsInput | None = None
    compact: Compact | None = None
    negative: Negative | None = Field(
        default=None, description="Defaults to minus on numeric kinds."
    )
    grouping: StrictBoolean | None = Field(
        default=None, description="Defaults to true on numeric kinds and false on identifier."
    )
    date_style: DateStyle | None = None


class Time(_Extensible):
    """Temporal settings for date and datetime dimensions."""

    grain: Grain | None = None
    fiscal_year_start: Month | None = Field(
        default=None, description="Month number (1-12) the fiscal year starts in."
    )


class Aggregation(_Extensible):
    """Additivity, stated only when nothing upstream declares it."""

    additivity: Additivity
    by: UniqueTexts | None = Field(
        default=None, description="Dimensions a semi_additive metric must not be summed over."
    )

    @model_validator(mode="after")
    def _check_by(self) -> Self:
        if self.additivity == "semi_additive" and self.by is None:
            _raise(
                type(self).__name__,
                [
                    _custom_error(
                        ("by",), "missing", "required when additivity is semi_additive", None
                    )
                ],
            )
        if self.additivity != "semi_additive" and self.by is not None:
            _raise(
                type(self).__name__,
                [
                    _custom_error(
                        ("by",), "by_not_allowed", "only allowed with semi_additive", self.by
                    )
                ],
            )
        return self


# --------------------------------------------------------------------------------------
# The block
# --------------------------------------------------------------------------------------


def _json_number(value: float) -> int | float:
    return int(value) if value.is_integer() else value


def _sorted(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return {key: _sorted(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted(item) for item in value]
    return value


def _dump(model: BaseModel) -> dict[str, JsonValue]:
    out: dict[str, JsonValue] = {}
    for name in type(model).model_fields:
        field_value: object = getattr(model, name)
        if field_value is None:
            continue
        dumped = _dump_field(field_value)
        if dumped == {}:  # an empty section such as `display: {}` says nothing
            continue
        out[name] = dumped
    for key, extra in (model.__pydantic_extra__ or {}).items():
        out[key] = copy.deepcopy(extra)
    return out


def _dump_field(value: object) -> JsonValue:
    if isinstance(value, Decimals):
        return list(value.as_pair())
    if isinstance(value, BaseModel):
        return _dump(value)
    if isinstance(value, tuple):
        numbers = cast("tuple[float, ...]", value)
        return [_json_number(number) for number in numbers]
    if isinstance(value, list):
        strings = cast("list[str]", value)
        return list(strings)
    if isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        return _json_number(value)
    raise TypeError(f"cannot dump {type(value).__name__}")  # pragma: no cover


def canonical_json(data: JsonValue) -> str:
    """Serialise JSON-ready data with sorted keys and compact separators."""
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


class SLayerBlock(_Extensible):
    """
    One ``s_layer`` block: what a metric, fact or dimension means.

    Validating a block fills in the defaults the vocabulary defines, so the attributes always
    hold the effective values. Two blocks are equal when their normal forms are equal.

    Example:
        .. code-block:: python

            block = SLayerBlock.model_validate(
                {"value": {"kind": "currency", "currency": "USD"}}
            )
            block.kind  # "currency"
    """

    model_config = ConfigDict(title="S-LAYER semantic format block")

    value: Value
    display: Display | None = None
    time: Time | None = None
    aggregation: Aggregation | None = None
    label: Label | None = Field(
        default=None, description="Only where the platform has no label slot."
    )
    synonyms: UniqueTexts | None = Field(
        default=None, description="Only where the platform has no synonyms slot."
    )

    @property
    def kind(self) -> Kind:
        """The block's ``value.kind``."""
        return self.value.kind

    @property
    def additivity(self) -> Additivity | None:
        """The stated additivity, else the one the kind implies, else ``None``."""
        if self.aggregation is not None:
            return self.aggregation.additivity
        return implied_additivity(self.kind)

    @model_validator(mode="after")
    def _check_and_fill(self) -> Self:
        errors = self._cross_field_errors()
        _raise(type(self).__name__, errors)
        filled = self._display_with_defaults()
        if filled is not self.display:
            object.__setattr__(self, "display", filled)
        return self

    def _cross_field_errors(self) -> list[InitErrorDetails]:
        kind = self.kind
        errors: list[InitErrorDetails] = []
        if self.time is not None:
            if kind not in TEMPORAL_KINDS:
                errors.append(
                    _custom_error(
                        ("time",), "not_applicable", f"not allowed on kind {kind!r}", None
                    )
                )
            elif kind == "date" and self.time.grain in SUB_DAY_GRAINS:
                errors.append(
                    _custom_error(
                        ("time", "grain"),
                        "not_applicable",
                        f"grain {self.time.grain!r} is finer than a date; use kind datetime",
                        self.time.grain,
                    )
                )
        if self.display is not None:
            errors.extend(self._display_errors(self.display))
        if (
            self.aggregation is not None
            and implied_additivity(kind) == "non_additive"
            and self.aggregation.additivity != "non_additive"
        ):
            errors.append(
                _custom_error(
                    ("aggregation", "additivity"),
                    "contradicts_kind",
                    f"kind {kind!r} implies non_additive",
                    self.aggregation.additivity,
                )
            )
        return errors

    def _display_errors(self, display: Display) -> list[InitErrorDetails]:
        kind = self.kind
        allowed: set[str] = set()
        if kind in NUMERIC_KINDS:
            allowed |= DISPLAY_NUMBER_KEYS | {"grouping"}
        if kind == "identifier":
            allowed.add("grouping")
        if kind in TEMPORAL_KINDS:
            allowed.add("date_style")
        errors: list[InitErrorDetails] = []
        for name in Display.model_fields:
            set_value: object = getattr(display, name)
            if set_value is not None and name not in allowed:
                errors.append(
                    _custom_error(
                        ("display", name),
                        "not_applicable",
                        f"not allowed on kind {kind!r}",
                        set_value,
                    )
                )
        if kind == "identifier" and display.grouping is True:
            errors.append(
                _custom_error(
                    ("display", "grouping"),
                    "contradicts_kind",
                    "kind 'identifier' implies grouping false",
                    True,
                )
            )
        return errors

    def _display_with_defaults(self) -> Display | None:
        kind = self.kind
        display = self.display
        if kind in NUMERIC_KINDS:
            base = display if display is not None else Display()
            return base.model_copy(
                update={
                    "negative": base.negative or "minus",
                    "grouping": True if base.grouping is None else base.grouping,
                }
            )
        if kind == "identifier":
            base = display if display is not None else Display()
            return base.model_copy(update={"grouping": False})
        return display

    def normal_form(self) -> dict[str, JsonValue]:
        """
        The block as JSON-ready data in normal form.

        Defaults are filled in, keys are sorted, absent optional keys are left out, decimals
        are a ``[min, max]`` pair and whole-number score bounds are integers.
        """
        data = _sorted(_dump(self))
        assert isinstance(data, dict)
        return data

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SLayerBlock):
            return NotImplemented
        return canonical_json(self.normal_form()) == canonical_json(other.normal_form())

    def __hash__(self) -> int:
        return hash(canonical_json(self.normal_form()))
