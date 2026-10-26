# Persona Report

**Generated:** 2026-10-26
**Audience:** Python integrator (advanced)
**Scenarios tested:** 5
**Results:** 3 PASS, 2 PARTIAL, 0 FAIL

## Summary

The how-to guides map one-to-one onto this persona's tasks, and each opens with runnable code
and its output. The overview's cards and the How-to index make every guide two clicks from the
homepage. Two gaps slow the persona down: getting the schema without Python, and reading
extension keys.

---

## Scenario S1: validate every block and report all problems

**Verdict:** PASS

### Navigation Path

1. Started at: index.rst. Found the summary of `validate_block`; followed the How-to guides card.
2. how-to/index.rst. "For tool builders" lists *Validate a block and report its problems*.
3. how-to/validate-a-block.rst. "Report every problem" shows `error.issues` with paths; the
   follow-on example collects issues across members. Troubleshooting covers `ValueError` for a
   bad member type.

---

## Scenario S2: write and read tags

**Verdict:** PASS

### Navigation Path

1. index.rst, then How-to guides, then *Round-trip a block through warehouse tags*.
2. The tag table in "Before you start" says what goes where; "Write the tags", "Handle a
   payload that is too long" and "Read the tags back" cover both directions and the limit.

---

## Scenario S3: detect drift

**Verdict:** PASS

### Navigation Path

1. How-to index, then *Compare blocks and detect drift*. "Detect drift between YAML and a
   warehouse" rebuilds from tags and compares; the link to the normal-form explanation
   answers why `compact: none` differs from a missing `compact`.

---

## Scenario S4: schema in a TypeScript service

**Verdict:** PARTIAL

### Navigation Path

1. How-to index, then *Use the JSON Schema in another tool*.
2. "Copy the schema for other languages" copies the file with Python. "Know what the schema
   does not check" is clear.

### Gap Analysis

**Where:** how-to/use-the-json-schema.rst > Copy the schema for other languages
**What:** The only way shown to get the file is to install the Python package and copy it.
**Impact:** A service with no Python toolchain has to install one just to get a JSON file.
**Suggested Fix:** In how-to/use-the-json-schema.rst, section "Copy the schema for other
languages": say that the file is also in the source repository, with a link, and that the
copy should match the package version the Python side uses.

---

## Scenario S5: read x- extension keys

**Verdict:** PARTIAL

### Navigation Path

1. explanation/the-block.rst explains `x-` keys; how-to/write-a-block.rst shows where they are
   allowed in YAML.
2. No how-to shows how to get them back from a parsed block. The reference lists
   `extensions` only as an inherited property.

### Gap Analysis

**Where:** how-to/validate-a-block.rst (no section)
**What:** `block.extensions` and `block.value.extensions` are not shown on any narrative page.
**Impact:** The persona has to find the property in the reference by guessing.
**Suggested Fix:** In how-to/validate-a-block.rst, add a short section after "Validate for a
member type" showing `extensions` on the block and on a section.

---

## Revision Recommendations

### FAIL Issues (trigger revision)

None.

### PARTIAL Issues (for project author approval)

| Scenario | Page | Gap | Suggested Fix |
|----------|------|-----|---------------|
| S4 | how-to/use-the-json-schema.rst | Schema only obtainable via Python | Link the file in the repository |
| S5 | how-to/validate-a-block.rst | `extensions` not shown | Add a "Read extension keys" section |

## Resolution

Both PARTIAL fixes were applied on 2026-10-26: a repository link for the schema file in
*Use the JSON Schema in another tool*, and a "Read extension keys" section in *Validate a
block and report its problems*.
