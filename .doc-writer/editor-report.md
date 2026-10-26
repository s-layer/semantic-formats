# Editor Report

**Generated:** 2026-10-26
**Files reviewed:** 14 (docs/**/*.rst, excluding the generated API reference)
**Changes made:** 11
  - BLOCKING: 2
  - SUGGESTION: 6
  - NITPICK: 3

## Summary

The pages were accurate against source: every example ran with the output shown, and every
error message in the troubleshooting tables matched a real run. The edits fixed one
cross-reference that did not resolve, one inaccurate claim about other languages, examples
whose dbt time granularity contradicted the `s_layer` grain, and some wording.

---

## docs/how-to/use-the-json-schema.rst

### BLOCKING

| Section | Description | Fix |
|---------|-------------|-----|
| Check a block with jsonschema | `:py:class:` target `jsonschema.Draft202012Validator` did not resolve through intersphinx (nitpicky build) | Pointed it at `jsonschema.validators.Draft202012Validator` |

### SUGGESTION

| Section | Description | Fix |
|---------|-------------|-----|
| Troubleshooting | Definition term used plain ``json_schema()`` / ``load_schema()`` (Rule 4) | Linked both with `:py:func:` |
| Know what the schema does not check | `grouping` on `identifier` passes the schema but was not listed | Added it to the list |

## docs/explanation/normal-form.rst

### BLOCKING

| Section | Description | Fix |
|---------|-------------|-----|
| How equality works | Claimed a reader in another language "sees 1 and 1.0 as written"; JavaScript, for one, parses both to the same number | Rewrote: comparing text gives an answer any language can reproduce from the JSON |

### NITPICK

| Section | Description | Fix |
|---------|-------------|-----|
| How equality works | "the text that json.dumps writes" was vague | Named the properties: sorted keys, no whitespace, non-ASCII as is |

## docs/tutorials/first-blocks.rst

### SUGGESTION

| Section | Description | Fix |
|---------|-------------|-----|
| Write the dbt YAML | `time_granularity: day` next to `grain: month` read as a contradiction | Changed the `s_layer` grain to `day` (both copies of the file) |
| Write the dbt YAML | "member" used before it was introduced | Introduced the term in the sentence |

## docs/how-to/write-a-block.rst

### SUGGESTION

| Section | Description | Fix |
|---------|-------------|-----|
| Step 3 | Same granularity/grain mismatch | Example is now an `order_month` dimension with month granularity and grain |
| Troubleshooting | `Extra inputs are not permitted` (from `decimals` and boolean `labels`) was missing | Added a row |

### NITPICK

| Section | Description | Fix |
|---------|-------------|-----|
| Step 2 | Default column said "none filled in" next to the value `none` | "not filled in" (2 instances) |

## docs/explanation/design-decisions.rst

### SUGGESTION

| Section | Description | Fix |
|---------|-------------|-----|
| Open value lists | Gave a rationale for the currency pattern that the README does not state | Replaced with a factual statement of what the pattern does and does not check |

### NITPICK

| Section | Description | Fix |
|---------|-------------|-----|
| (all) | Checked bracket numbers against the README's 17 decisions | No change needed |

---

## Pass notes

- Pass 1 (terminology): "block", "member type", "payload" (for `S_LAYER_SPEC`) and "tag
  value" are used consistently. British "normalise" appears only in source docstrings, not
  in the pages.
- Pass 2 (Diataxis): the tables in *Write an s_layer block* are kept as decision aids for the
  analytics-engineer persona, who has no YAML-key reference page (the autoapi reference
  documents Python classes, not YAML keys). Explanation pages contain only illustrative
  examples.
- Pass 3 (humanizer): no em dashes, chatbot artifacts or promotional words found. The
  ` -- ` separators on section index pages follow the sphinx-shibuya guidance format.
- Pass 4 (cross-references): every `:py:` role on the narrative pages resolves (checked
  with a nitpicky build). The remaining nitpicky warnings are all inside the generated API
  reference (see the report to the maintainer).

## Terminology Changes

| Term | Before | After | Authority |
|------|--------|-------|-----------|
| member | used without definition in the tutorial | defined on first use | persona never_assume |
