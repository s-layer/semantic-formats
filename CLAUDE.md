# s-layer-semantic-formats

The shared definition of the S-LAYER semantic format vocabulary (the `s_layer` block in dbt
`config.meta`). See AGENTS.md for the quality gates
and conventions.
After changing the models, regenerate the committed JSON Schema with `just schema`.

## Opening pull requests

When you open a pull request, ask the user whether it needs a review. If they say yes:

1. Mark the PR ready for review, since the review bot skips drafts.
2. Request a review from `anentropic-reviewbot`. Claude then posts inline comments and a summary on the PR.
3. Watch the PR and address the review comments and any CI failures as they come in, until CI is green and no blocking comments are left open.

To get another review after pushing fixes, request one from `anentropic-reviewbot` again.
