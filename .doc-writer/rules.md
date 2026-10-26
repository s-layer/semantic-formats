# Project Documentation Rules

These rules are specific to this project and extend the universal quality rules
enforced by all doc-writer agents. Edit this file to add project-specific
documentation guidelines.

## How Rules Work

- Universal rules (no internal details, working examples, consistent structure,
  cross-references, persona calibration) are always enforced and cannot be
  overridden.
- Rules in this file are additive — they add project-specific requirements on
  top of the universal baseline.
- Write rules as natural language instructions. Agents interpret them directly.
- Be specific. "Use clear language" is too vague. "Always include a Requirements
  section in how-to guides listing minimum dependency versions" is actionable.

## Project Rules

- Every Python example must run as shown against the installed package (`uv run python`),
  and any output shown in the page (comments, printed text, doctest results) must be the
  exact output of that run. Re-run the examples whenever the library changes.
- Where an example shows what an analytics engineer writes, show it as dbt YAML
  (`config.meta.s_layer`) first, then the Python that reads it.
- The README's numbered "Decisions not in the design doc" are the rules the package
  applies. The explanation pages may group or rephrase them but must not contradict them.
- Use "block" for the `s_layer` mapping and "member type" for metric, fact or dimension,
  consistently across pages.
- The author is "Anentropic". Never write a personal name for the maintainer.

<!-- Add your project-specific documentation rules below. Examples: -->

<!-- - Always include a "Requirements" section in how-to guides listing minimum versions -->
<!-- - Use American English spelling throughout -->
<!-- - Code examples must show error handling, not just the happy path -->
<!-- - Reference the changelog entry when documenting breaking changes -->
<!-- - Include performance characteristics in reference pages for I/O operations -->
<!-- - Prefer async examples over sync when both are available -->
