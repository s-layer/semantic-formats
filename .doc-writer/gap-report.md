# Gap Report

**Generated:** 2026-10-26
**Source root:** src/s_layer_semantic_formats/
**Language:** python
**Total undocumented symbols:** 44 (of 47 in `__all__`)

The only narrative page is `docs/index.rst`, whose quick start mentions `validate_block`,
`normalize` and `spec_tag_value`. Every other public symbol appears only in the autoapi
reference.

## Undocumented Symbols

### src/s_layer_semantic_formats/_api.py
- `parse_block` (function)
- `member_type_issues` (function)
- `to_compact_json` (function)
- `from_compact_json` (function)
- `MAX_TAG_LENGTH` (constant)
- `SPEC_EXCLUDED_KEYS` (constant)

### src/s_layer_semantic_formats/_errors.py
- `SLayerError`, `SLayerValidationError`, `SpecTooLongError` (exception classes)
- `Issue` (dataclass)

### src/s_layer_semantic_formats/_schema.py
- `SCHEMA_PATH` (constant)
- `json_schema`, `load_schema`, `render_schema` (functions)

### src/s_layer_semantic_formats/_models.py
- `SemanticFormat` (class) and its `kind`, `additivity`, `extensions`, `normal_form` members
- `Display`, `Decimals`, `Time`, `Aggregation` (section classes)
- `NumberValue`, `CountValue`, `CurrencyValue`, `PercentageValue`, `DurationValue`,
  `BytesValue`, `QuantityValue`, `ScoreValue`, `CategoryValue`, `GeoValue`, `DateValue`,
  `DatetimeValue`, `IdentifierValue`, `BooleanValue`, `BooleanLabels` (value classes)
- `Value`, `Kind`, `MemberType`, `Additivity` (type aliases)
- `KINDS`, `KIND_MEMBER_TYPES`, `NUMERIC_KINDS`, `TEMPORAL_KINDS` (constants)
- `implied_additivity` (function)
