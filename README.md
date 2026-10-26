# s-layer-semantic-formats

The shared definition of the S-LAYER semantic format vocabulary: the `s_layer` block that
says what a metric, fact or dimension *means* (a currency in USD, a fraction shown as a
percentage, a duration in seconds, a monthly date), written once in dbt `config.meta`.

- [dbt-s-layer](https://github.com/s-layer/dbt-s-layer) validates blocks and writes them into
  each warehouse.
- [semolina](https://github.com/s-layer/semolina) reads them back.

This package holds what both sides must agree on:

- typed pydantic v2 models for the block, with `validate_block()` for a member type;
- the normal form that defines equality (`normalize()`);
- the compact `S_LAYER_SPEC` tag payload used by Snowflake and DuckDB semantic views, and its
  inverse;
- the JSON Schema, generated from the models and shipped as
  `s_layer_semantic_formats/s_layer.schema.json`.

It contains no warehouse code and no dbt code.

## The block

```yaml
metrics:
  - name: revenue
    config:
      meta:
        s_layer:
          value: {kind: currency, currency: USD}
          display: {decimals: {max: 0}, compact: auto}
          synonyms: [sales, turnover]
```

| Part          | Keys                                                                         |
| ------------- | ---------------------------------------------------------------------------- |
| `value`       | `kind` (required) plus the kind's own keys, such as `currency` or `unit`     |
| `display`     | `decimals {min, max}`, `compact`, `negative`, `grouping`, `date_style`       |
| `time`        | `grain`, `fiscal_year_start` (date and datetime dimensions only)             |
| `aggregation` | `additivity`, plus `by` when `semi_additive` (metrics only)                  |
| `label`       | only where the platform has no label slot                                    |
| `synonyms`    | only where the platform has no synonyms slot                                 |
| `x-<vendor>`  | extension keys, carried verbatim but not interpreted                         |

Kinds: `number`, `count`, `currency`, `percentage`, `duration`, `bytes`, `quantity`, `score`
(metrics, and some facts) and `category`, `geo`, `date`, `datetime`, `identifier`, `boolean`
(dimensions). `KIND_MEMBER_TYPES` has the exact table.

## Usage

```python
from s_layer_semantic_formats import (
    SLayerValidationError,
    from_compact_json,
    normalize,
    spec_tag_value,
    validate_block,
)

block = validate_block(
    {
        "value": {"kind": "currency", "currency": "USD"},
        "display": {"decimals": {"max": 0}, "compact": "auto"},
    },
    "metric",
)

normalize(block)
# {'display': {'compact': 'auto', 'decimals': [0, 0],
#              'grouping': True, 'negative': 'minus'},
#  'value': {'currency': 'USD', 'kind': 'currency'}}

# The S_LAYER_SPEC tag value (raises SpecTooLongError past 256 chars)
spec = spec_tag_value(block)
# '{"display":{"compact":"auto","decimals":[0,0],"grouping":true,"negative":"minus"},"value":{"currency":"USD"}}'

# Reading the tags back gives an equal block
assert from_compact_json("currency", spec) == block

try:
    validate_block({"value": {"kind": "currency"}}, "dimension")
except SLayerValidationError as error:
    print(error)
    # invalid s_layer block (1 problem):
    #   value.currency: required key is missing
```

`SLayerValidationError.issues` lists every problem as an `Issue(path, message)`.

## Public API

| Name                                                     | What it does                                                    |
| -------------------------------------------------------- | --------------------------------------------------------------- |
| `validate_block(data, member_type)`                      | Parse a block and check its kind applies to the member type     |
| `parse_block(data)`                                      | Parse a block without the member-type check                     |
| `member_type_issues(block, member_type)`                 | The member-type problems of a parsed block, as a list           |
| `normalize(block)`                                       | The normal form as JSON-ready data                              |
| `to_compact_json(block)`                                 | The `S_LAYER_SPEC` payload                                      |
| `spec_tag_value(block, limit=256)`                       | `to_compact_json`, raising `SpecTooLongError` when too long      |
| `from_compact_json(kind, spec, *, label, synonyms, ...)` | Rebuild a block from `S_LAYER_KIND`, `S_LAYER_SPEC` and label   |
| `implied_additivity(kind)`                               | `"non_additive"` for percentage and score, else `None`          |
| `json_schema()`, `load_schema()`, `SCHEMA_PATH`          | The generated schema, and the committed copy                    |
| `SemanticFormat` and the section and value models           | The typed block; `block.kind`, `block.additivity`, `.extensions` |

Blocks compare equal (`==`, `hash`) on their normal form, so `{max: 2}` and
`{min: 0, max: 2}` are the same value.

## Decisions not in the design doc

The design doc is a draft. Where it is silent, this package picks the simplest rule it could
find:

1. **Defaults the normal form fills in are only the ones the doc states**: percentage
   `scale: fraction`, bytes `unit: B`, decimals `min: 0`, and on numeric kinds
   `negative: minus` and `grouping: true`; `identifier` gets `grouping: false`. Every other
   optional key (`compact`, `date_style`, `grain`, `fiscal_year_start`, `code`, number
   `unit`) is left out when absent, so a missing `compact` is not equal to `compact: none`.
2. **Implied additivity is not written into the block.** `percentage` and `score` imply
   `non_additive`, exposed by `implied_additivity()` and `SemanticFormat.additivity`, but the
   normal form and `S_LAYER_SPEC` only carry an `aggregation` someone wrote ("derive, don't
   duplicate"). A stated `aggregation` on those kinds must be `non_additive`.
3. **Required kind keys**: `duration.unit`, `score.range` and `geo.level` are required, as
   their table rows have no `?` and no default. `boolean.labels` needs both `true` and
   `false`; unquoted YAML `true:` / `false:` keys (read as booleans) are accepted too.
4. **Allowed values the doc leaves open**: bytes units are `B`, `KB` … `EB` and `KiB` …
   `EiB`. A number's optional `unit` is any non-empty string, like quantity's UCUM code.
   Currency is checked against `^[A-Z]{3}$` only. A geo `code` is any non-empty string.
5. **Score range**: two finite numbers with `min < max`; whole numbers are written as
   integers in the normal form, so `[0.0, 10]` and `[0, 10]` are equal.
6. **Decimals**: integers 0-20, `max` is required when `decimals` is given, `min <= max`.
   Both `{min, max}` and `[min, max]` are accepted; the normal form is the pair.
7. **Display keys must fit the kind**: `decimals`, `compact` and `negative` only on numeric
   kinds; `grouping` on numeric kinds and on `identifier` (where only `false` is allowed);
   `date_style` only on `date` and `datetime`.
8. **`time` only on `date` and `datetime`**, and a `date` cannot take a grain finer than a
   day (`second`, `minute`, `hour`).
9. **`aggregation` only on metrics** (checked by `validate_block`). `by` is required exactly
   when `semi_additive`.
10. **Lists** (`category.order`, `aggregation.by`, `synonyms`) are non-empty lists of
    distinct non-empty strings. Their order is kept, since it can carry meaning.
11. **`label`** is 1-255 characters, which fits both Databricks `display_name` (255) and the
    256-character tag limit. Whether a platform has a native slot (and so whether `label` or
    `synonyms` belong in the block at all) is left to dbt-s-layer.
12. **Extension keys** are allowed on the block and on `value`, `display`, `time` and
    `aggregation`, not inside `decimals`, `labels` or `range`. A key is an extension when it
    starts with lower-case `x-` and has at least one more character. Values can be any JSON
    (so no NaN or Infinity) and are kept as they are; only object key order is sorted in the normal form.
13. **`null` means absent** for any optional key, and an empty `display: {}` or `time: {}`
    is the same as leaving it out.
14. **Strict scalar types**: no coercion from strings or between bools and numbers
    (`grouping: "yes"`, `fiscal_year_start: "4"` and `decimals.max: 2.0` are errors).
15. **`S_LAYER_SPEC` keeps the block's nesting** (`{"display": {...}, "value": {...}}`)
    minus `value.kind`, `label` and `synonyms`; an empty `value` object is dropped, so a bare
    `date` block's spec is `{}`. Non-ASCII text is written as is, and the 256 limit counts
    characters and is inclusive. `from_compact_json` rejects a spec that contains `kind`,
    `label` or `synonyms`, or NaN or Infinity. It treats an empty label or synonyms list
    as none, and rejects a bare string of synonyms.
16. **Equality compares the canonical JSON text** of the normal form, so extension values
    `1`, `1.0` and `true` are different.
17. **The JSON Schema checks shape only.** Which kinds apply to which member type, and the
    rules between sections (items 2, 7, 8, 9), are enforced by the Python models and
    `validate_block`. So are a few rules within one key that the schema does not state: `2.0`
    where an integer is required (item 14), `min <= max` for decimals and `min < max` for a score
    range (items 5, 6), `by` being present exactly when `semi_additive` (item 9), and finite
    extension values (item 12). A block that passes the schema can still fail
    `validate_block`. The schema accepts `null` for optional keys, matching item 13.

## Development

```sh
uv sync --dev
prek install             # git hooks
uv run pytest            # tests, including hypothesis property tests
prek run --all-files     # ruff, basedpyright, uv lock and schema checks
just schema              # regenerate s_layer.schema.json after changing the models
```

Without `just`, regenerate the schema with `uv run python scripts/regen_schema.py`
(`--check` only compares). See [DEVELOP.md](DEVELOP.md) for the full guide.

## License

MIT
