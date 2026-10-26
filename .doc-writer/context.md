# Doc Writer Context

**Generated:** 2026-10-26
**Source:** /doc-writer:setup researcher
**Editable:** Yes -- manual edits are preserved until the next --refresh-context run. To make permanent changes, edit config.yaml and re-run setup.

## Project Summary

`s-layer-semantic-formats` (import name `s_layer_semantic_formats`) is the shared definition of
the S-LAYER semantic format vocabulary: the `s_layer` block written in dbt `config.meta` on a
metric, fact or dimension that says what its values mean (currency in USD, a fraction shown as
a percentage, a duration in seconds, a date at month grain). It ships typed pydantic v2 models,
`validate_block()`, the normal form that defines equality (`normalize()`), the compact
`S_LAYER_SPEC` tag payload and its inverse (`to_compact_json`, `spec_tag_value`,
`from_compact_json`), and a JSON Schema generated from the models (`SCHEMA_PATH`,
`load_schema()`, `json_schema()`). No warehouse or dbt code. dbt-s-layer writes blocks into
warehouses; semolina reads them back. Version 0.1.0, Python >= 3.11, depends only on pydantic >= 2.11.
Inferred from: README, pyproject.toml, `__init__.__all__`.

## User Persona: Python integrator

### Profile
- **Skill level:** advanced
- **What they know:** pydantic v2 (model_validate, frozen models, ValidationError), type hints,
  JSON Schema and validator libraries, dbt semantic manifests, warehouse tags.
- **What to always explain:** the block's sections and what belongs in each; the kind to member
  type table; that the normal form fills defaults and is what `==` and `hash` compare; the tag
  split (`S_LAYER_KIND`, `S_LAYER_SPEC`, `S_LAYER_LABEL`, native synonyms) and the inclusive
  256-character limit; which rules the JSON Schema leaves to Python.
- **Their world:** code generators and query libraries that sit between dbt YAML and the
  warehouse, and must agree with each other byte for byte.
- **How they found this library:** a dependency of dbt-s-layer or semolina, or needed to read
  `s_layer` blocks in their own tool.

### Common Tasks
- Validate a block for a member type: `validate_block(data, "metric")`, catch `SLayerValidationError`, read `.issues`.
- Compare blocks / detect drift: `==` on `SLayerBlock`, or `normalize()` output.
- Tag round trip: `spec_tag_value(block)` to write, `from_compact_json(kind, spec, label=..., synonyms=...)` to read.
- JSON Schema: `load_schema()` / `SCHEMA_PATH` with `jsonschema`, editors or other languages.
- Typed access: `block.kind`, `block.additivity`, `block.value.currency`, `block.extensions`.

### Writing Guidance for This Persona
- Skip pydantic basics; do explain the vocabulary-specific behaviour (strict scalars, null means absent).
- Lead with runnable code and real output; keep prose short.
- Use realistic members: revenue, order_count, conversion_rate, session_duration, order_date.

## User Persona: Analytics engineer

### Profile
- **Skill level:** intermediate
- **What they know:** dbt YAML, semantic models, metrics, dimensions, `config.meta`, SQL,
  additive vs semi-additive measures; can run a command they are given.
- **What to always explain:** every allowed key per section and kind, required keys, defaults,
  extension keys, what an error path such as `value.currency` points at.
- **Their world:** writing and reviewing dbt property files so dashboards format numbers right.
- **How they found this library:** a validation error or a teammate's dbt-s-layer setup.

### Common Tasks
- Pick a kind for a member and fill its required keys.
- Add display hints and time settings that fit the kind.
- Declare `aggregation` for a semi-additive metric (`by` required).
- Read an error message and fix the YAML.

### Writing Guidance for This Persona
- Show YAML first; the Python check is a one-liner they can copy.
- Explain keys in tables they can scan; link to the explanation page for the "why".

## Use Cases

### Validate blocks in a dbt tool
**Problem:** a code generator must reject bad `s_layer` YAML before writing it to a warehouse.
**What's possible:** `validate_block` reports every problem with a path in one exception.
**Outcome:** one error listing all issues; the generator stops before any DDL.
**Relevant persona(s):** Python integrator. **Source:** inferred

### Round-trip through warehouse tags
**Problem:** a query library reads tag strings back and must get the same meaning that was written.
**What's possible:** `spec_tag_value` / `from_compact_json` are inverses on the normal form.
**Outcome:** the rebuilt block compares equal to the original.
**Relevant persona(s):** Python integrator. **Source:** inferred

### Check YAML outside Python
**Problem:** editors and non-Python tools need to check block shape.
**What's possible:** the packaged JSON Schema.
**Outcome:** shape errors flagged in the editor; cross-section rules still need `validate_block`.
**Relevant persona(s):** both. **Source:** inferred

> These use cases were inferred from persona context and codebase analysis. To promote use cases to a documentation section, run `/doc-writer:setup` and provide explicit use cases.

## Tone: warm-businesslike

### Writing Rules
- Brief (1-2 sentence) introduction saying what the page covers and why.
- Basic usage first, then common variations.
- Troubleshooting or common-mistakes sections where relevant.
- Transition sentences between major sections.
- Admonitions for tips, warnings and important notes; never stacked.
- Warm but professional: no jokes, no first person, no casual asides. Second person ("you").

## Framework Preferences: sphinx-shibuya

### Navigation Strategy
- Strategy: Sections as top tabs. `nav_links` in conf.py lists Tutorials, How-to guides,
  Explanation, Reference (each a section `index.rst`) plus Release notes. nav_links are static
  URLs, not derived from the toctree; update them when pages move.
- Each section index lists its children with a 1-sentence abstract; each child has
  `.. meta:: :description:`.
- Root `index.rst` is the "Overview" page; it holds a hidden toctree of section indexes.

### Features to Use
- sphinx-design grids and cards on the Overview and section landing pages.
- Tab sets (`:sync-group:`) for YAML vs Python views of the same block.
- Dropdowns for long optional content (full kind tables, extra error examples).
- Admonitions: tip, warning, note.
- `:ref:` labels for internal links; `:py:func:` / `:py:class:` roles for API symbols
  (autoapi under `reference/api`); intersphinx for python, pydantic and jsonschema.
- MyST is enabled (changelog.md); write new pages in RST.

### Features NOT to Use
- Mermaid: sphinxcontrib-mermaid is not installed.
- Hand-written API reference pages: autoapi owns the Reference section.
- `:doc:` links for internal navigation.
