# Persona Report

**Generated:** 2026-10-26
**Audience:** Analytics engineer (intermediate)
**Scenarios tested:** 4
**Results:** 3 PASS, 1 PARTIAL, 0 FAIL

## Summary

*Write an s_layer block in dbt YAML* answers the "what keys are allowed" question directly,
YAML first, and its troubleshooting table matches the messages this persona will see. The
tutorial gets them to a first success quickly. The one friction point is installing a
Python package on a machine where `pip install` into the system Python is refused.

---

## Scenario S1: semi-additive balance metric

**Verdict:** PASS

### Navigation Path

1. index.rst, How-to guides card, "For dbt YAML authors", *Write an s_layer block in dbt YAML*.
2. Step 1 table gives `currency` with its required key; Step 4 has the exact
   `account_balance` example with `semi_additive` and `by`.

---

## Scenario S2: keys for a date dimension

**Verdict:** PASS

### Navigation Path

1. *Write an s_layer block in dbt YAML*, Step 2 table (the Kinds column shows `date_style` for
   `date`, numeric-only for `decimals`), Step 3 (grain list, no sub-day grain on `date`,
   `fiscal_year_start` 1 to 12) with a YAML example.

---

## Scenario S3: fix "kind 'percentage' applies to a metric, not a fact"

**Verdict:** PASS

### Navigation Path

1. *Write an s_layer block in dbt YAML* > Troubleshooting: the row "kind 'currency' applies to
   a fact or metric, not a dimension" has the same shape; the fix points to the Step 1 table,
   where `number`, `currency`, `duration` and `quantity` are marked for facts.

---

## Scenario S4: check a block before a pull request

**Verdict:** PARTIAL

### Navigation Path

1. Tutorial "Install the package" and how-to Step 6 both give `pip install
   s-layer-semantic-formats pyyaml` and a copy-paste script.

### Gap Analysis

**Where:** tutorials/first-blocks.rst > Install the package
**What:** No word on virtual environments. On many systems `pip install` into the system
Python fails with an "externally managed environment" error.
**Impact:** The persona can be stuck at step one without knowing why.
**Suggested Fix:** In tutorials/first-blocks.rst, section "Install the package": create and
activate a virtual environment first, with the exact commands. In how-to/write-a-block.rst
Step 6, say that the pasted YAML can keep the indentation it had in the dbt file.

---

## Revision Recommendations

### FAIL Issues (trigger revision)

None.

### PARTIAL Issues (for project author approval)

| Scenario | Page | Gap | Suggested Fix |
|----------|------|-----|---------------|
| S4 | tutorials/first-blocks.rst | No virtual-environment step | Add venv commands before `pip install` |
| S4 | how-to/write-a-block.rst | Unclear whether pasted YAML may stay indented | Say that it can |

## Resolution

Both PARTIAL fixes were applied on 2026-10-26: virtual-environment commands in the
tutorial's install step, and a note on pasted indentation in Step 6 of *Write an s_layer
block in dbt YAML*.
