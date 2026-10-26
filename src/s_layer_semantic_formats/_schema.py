"""The JSON Schema for the block, generated from the models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from s_layer_semantic_formats._models import SLayerBlock

__all__ = ["SCHEMA_PATH", "json_schema", "load_schema", "render_schema"]

SCHEMA_PATH = Path(__file__).with_name("s_layer.schema.json")
"""The committed schema file, shipped inside the package."""

_DRAFT = "https://json-schema.org/draft/2020-12/schema"
_DESCRIPTION = (
    "The s_layer block written in dbt config.meta on a metric, dimension or fact. "
    "This schema checks shape only: which kinds apply to which member type, and rules "
    "between sections (time only on date and datetime kinds, display keys per kind, "
    "implied additivity), are checked by s_layer_semantic_formats.validate_block."
)


def json_schema() -> dict[str, Any]:
    """Generate the JSON Schema for an ``s_layer`` block from the models."""
    generated = SLayerBlock.model_json_schema()
    generated.pop("description", None)
    return {"$schema": _DRAFT, "description": _DESCRIPTION, **generated}


def render_schema() -> str:
    """Return the schema exactly as it is committed: two-space indent, trailing newline."""
    return json.dumps(json_schema(), indent=2, ensure_ascii=False) + "\n"


def load_schema() -> dict[str, Any]:
    """Load the committed schema that ships with the package."""
    loaded: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return loaded
