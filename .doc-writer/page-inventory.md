# Page Inventory

**Mode:** create (the only narrative page is `docs/index.rst`, a scaffold quick start)
**Navigation:** sections as top tabs (Tutorials, How-to guides, Explanation, Reference) plus Release notes

## Proposed Documentation

| # | Type | Title | Key Sections | File Path | Persona |
|---|------|-------|--------------|-----------|---------|
| 1 | (index) | Overview | What the package is, who uses it, install, a first look, cards into each section | docs/index.rst | both |
| 2 | (section-index) | Tutorials | One-line abstract per tutorial | docs/tutorials/index.rst | both |
| 3 | tutorial | Check the s_layer blocks in a dbt file | Install, write a dbt YAML file, load and validate it, read an error and fix it, see the normal form and the tag value, what you learned | docs/tutorials/first-blocks.rst | both |
| 4 | (section-index) | How-to guides | One-line abstract per guide | docs/how-to/index.rst | both |
| 5 | how-to | Write an s_layer block in dbt YAML | Pick a kind for the member type, fill required keys, display hints, time, aggregation, label/synonyms, extension keys, check it, fix common errors | docs/how-to/write-a-block.rst | analytics engineer |
| 6 | how-to | Validate a block and report its problems | validate_block per member type, catch SLayerValidationError, use issues, parse first and check member type later, wrong member_type | docs/how-to/validate-a-block.rst | integrator |
| 7 | how-to | Compare blocks and detect drift | == and hash, normalize for storage/diffs, dedupe in sets/dicts, compare YAML with what a warehouse holds | docs/how-to/compare-blocks.rst | integrator |
| 8 | how-to | Round-trip a block through warehouse tags | Write S_LAYER_KIND/SPEC/LABEL and synonyms, handle SpecTooLongError, read tags with from_compact_json, unset tags, check member type on read | docs/how-to/round-trip-tags.rst | integrator |
| 9 | how-to | Use the JSON Schema in another tool | Find SCHEMA_PATH, load_schema with jsonschema, export the file for other languages, what the schema does not check | docs/how-to/use-the-json-schema.rst | integrator |
| 10 | (section-index) | Explanation | One-line abstract per page | docs/explanation/index.rst | both |
| 11 | explanation | Understanding the s_layer block | Sections and what each carries, kinds and member types, where a block travels (dbt, dbt-s-layer, tags, semolina), extensions | docs/explanation/the-block.rst | both |
| 12 | explanation | The normal form and equality | Why a normal form, defaults filled in, absent vs explicit, decimals pair and numbers, null means absent, equality on canonical text, how S_LAYER_SPEC derives from it | docs/explanation/normal-form.rst | integrator |
| 13 | explanation | Design decisions | The 17 README decisions grouped by theme with the reasoning | docs/explanation/design-decisions.rst | both |
| 14 | (section-index) | Reference | autoapi package page, the JSON Schema file, release notes | docs/reference/index.rst | integrator |

README.md and a MAINTAINER guide were offered and excluded: the README is the maintained
source of truth for the public API table and decisions, and DEVELOP.md already covers
maintainer setup.

## API Reference status

Detected: sphinx-autoapi. Moved to `docs/reference/api/` (`autoapi_root = "reference/api"`,
`autoapi_add_toctree_entry = False`), included from `docs/reference/index.rst`. Pages link
symbols with `:py:func:` / `:py:class:` roles under `.. py:currentmodule:: s_layer_semantic_formats`.

## Audience targeting

- Python integrator: 6, 7, 8, 9, 12, 14.
- Analytics engineer: 5 (written for them), 3, 11, 13.

## Coverage gaps

- `render_schema()` is only mentioned in passing (it exists for the package's own schema
  file); the reference covers it.
- `Decimals.as_pair()` and the individual value classes are covered by the reference only.
