# Author Notes for Editor

Internal notes are kept here rather than as comments in the RST pages, so nothing needs
stripping before publication. Every Python example was executed against the package with
`uv run python` (python blocks with their following `text` output block, `python file.py`
runs, and `pycon` blocks through doctest) and every `s_layer` block in the YAML examples was
run through `validate_block` for its member type. All output shown is the exact output.

## docs/tutorials/first-blocks.rst
- Type: tutorial (skills/diataxis/references/tutorials.md)
- Sources: _api.py (validate_block, normalize, spec_tag_value), _models.py (CurrencyCode pattern, Display defaults)
- Accuracy: the first metrics.yml deliberately has `currency: usd`; the error text is the pydantic pattern message.
- API links: validate_block, SLayerValidationError, normalize, spec_tag_value

## docs/how-to/write-a-block.rst
- Type: how-to (skills/diataxis/references/how-to-guides.md)
- Sources: _models.py (Kind, KIND_MEMBER_TYPES, value models, Display, Time, Aggregation, _display_errors, _cross_field_errors, BooleanLabels._yaml_bool_keys), _api.py (_issue messages, member_type_issues)
- Accuracy: troubleshooting messages copied from actual runs; `Extra inputs are not permitted` comes from the closed `Decimals` and `BooleanLabels` objects.
- Known limitation: shape errors and cross-section errors are reported in two rounds (pydantic field validation, then the model validator).

## docs/how-to/validate-a-block.rst
- Type: how-to
- Sources: _api.py (validate_block, parse_block, member_type_issues), _errors.py (Issue, SLayerValidationError, SpecTooLongError bases)
- API links: validate_block, SemanticFormat, SLayerValidationError, Issue, parse_block, member_type_issues, KIND_MEMBER_TYPES, SpecTooLongError, SLayerError

## docs/how-to/compare-blocks.rst
- Type: how-to
- Sources: _models.py (SemanticFormat.__eq__/__hash__, canonical_json, _dump), _api.py (normalize, from_compact_json)
- Accuracy: `block == dict` returns False (NotImplemented on both sides falls back to identity).

## docs/how-to/round-trip-tags.rst
- Type: how-to
- Sources: _api.py (MAX_TAG_LENGTH, SPEC_EXCLUDED_KEYS, to_compact_json, spec_tag_value, from_compact_json)
- Accuracy: do not print SPEC_EXCLUDED_KEYS (frozenset order depends on hash seed).

## docs/how-to/use-the-json-schema.rst
- Type: how-to
- Sources: _schema.py, s_layer.schema.json; jsonschema 4.26 behaviour (best_match, no discriminator support)
- Accuracy: every rule in "does not check" was confirmed by running Draft202012Validator.is_valid on a counter-example.

## docs/explanation/the-block.rst, normal-form.rst, design-decisions.rst
- Type: explanation (skills/diataxis/references/explanation.md)
- Sources: README "Decisions not in the design doc" 1-17, _models.py, _api.py
- Accuracy: design-decisions.rst bracket numbers match README numbering; no rule is restated differently.

## Section indexes and docs/index.rst
- Overview uses tab sets (pip/uv, YAML/Python) and grid cards to each section.
- reference/index.rst includes the autoapi page `api/s_layer_semantic_formats/index`.
