"""
Regenerate (or check) the committed JSON Schema.

Usage: ``uv run python scripts/regen_schema.py [--check]``.
"""

from __future__ import annotations

import sys

from s_layer_semantic_formats import SCHEMA_PATH, render_schema


def main(argv: list[str]) -> int:
    rendered = render_schema()
    current = SCHEMA_PATH.read_text(encoding="utf-8") if SCHEMA_PATH.exists() else None
    if "--check" in argv:
        if current != rendered:
            print(f"{SCHEMA_PATH} is out of date; run `just schema`", file=sys.stderr)
            return 1
        print(f"{SCHEMA_PATH} is up to date")
        return 0
    if current == rendered:
        print(f"{SCHEMA_PATH} unchanged")
    else:
        SCHEMA_PATH.write_text(rendered, encoding="utf-8")
        print(f"wrote {SCHEMA_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
