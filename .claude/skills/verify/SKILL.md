---
name: verify
description: Prove a change to s-layer-semantic-formats works end to end. Use before saying a change is done, before committing, and before opening or updating a pull request.
---

# Verify a change

Run from the repository root:

```bash
uv sync --locked --dev
uv tool install prek  # once; skip if prek is already on PATH
prek run --all-files
CI=true uv run pytest --hypothesis-profile=ci
```

It passes when every command exits 0. prek includes the check that the committed JSON
Schema matches the models; `just schema` regenerates it. The `ci` Hypothesis profile
runs more examples than the default.

`CI=true` turns on `tests/ci_skips.py`, which fails the run on any skip not allowed
there, as CI does. Without it a skipped test only shows in the summary, and a run that
skipped what you changed is not a pass. It is set on each test line rather than
exported, so it still holds when each line runs in a fresh shell, and other tools that
read `CI` (Playwright, for one) keep their local behaviour.

Take each command's exit status from the command itself. In a pipeline `$?` is the last
command's status, so `cmd | tail` hides a failure. Redirect long output to a file, then
read the file.

## What this covers

- the models, the JSON Schema and their agreement on valid and invalid blocks

## What it does not cover

- consumers: a vocabulary change also needs dbt-s-layer's and semolina's suites run
  against it
- Python versions other than the one you ran: CI runs a version matrix

## When it fails

- Read the first failure and fix its cause. Do not rerun hoping for a green, and do not
  skip, loosen or delete the failing test to get one.
- If the failure is real but outside the change, say so in the PR and in your report
  rather than working around it.
