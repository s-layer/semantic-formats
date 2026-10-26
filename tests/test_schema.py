"""The committed JSON Schema."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from s_layer_semantic_formats import SCHEMA_PATH, json_schema, load_schema, render_schema

ROOT = Path(__file__).resolve().parents[1]


def test_committed_schema_matches_the_models() -> None:
    committed = SCHEMA_PATH.read_text(encoding="utf-8")
    assert committed == render_schema(), (
        "s_layer.schema.json is out of date: run `just schema` "
        "(or `uv run python scripts/regen_schema.py`) and commit the result"
    )


def test_committed_schema_is_a_valid_draft_2020_12_schema() -> None:
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    assert schema == json_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_regen_script_check_mode() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "regen_schema.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "data",
    [
        {"value": {"kind": "ratio"}},
        {"value": {"kind": "currency"}},
        {"value": {"kind": "currency", "currency": "usd"}},
        {"value": {"kind": "quantity"}},
        {"value": {"kind": "count"}, "format": "usd"},
        {"value": {"kind": "count"}, "display": {"decimals": {"min": 1}}},
        {"value": {"kind": "count"}, "display": {"grouping": "no"}},
        {"display": {"compact": "auto"}},
    ],
)
def test_schema_rejects_invalid_blocks(data: dict[str, Any]) -> None:
    assert not Draft202012Validator(load_schema()).is_valid(data)  # pyright: ignore[reportUnknownMemberType]


def test_schema_accepts_extension_keys() -> None:
    data = {"value": {"kind": "count", "x-acme": 1}, "x-lightdash": {"hidden": True}}
    assert Draft202012Validator(load_schema()).is_valid(data)  # pyright: ignore[reportUnknownMemberType]
