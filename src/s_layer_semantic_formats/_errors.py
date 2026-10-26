"""Errors raised by the library."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


class SLayerError(Exception):
    """Base class for every error this library raises."""


@dataclass(frozen=True, slots=True)
class Issue:
    """
    One problem found in a block.

    ``path`` is a dotted path into the block (``value.currency``, ``synonyms[1]``), or an
    empty string for the block itself.
    """

    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path or '(block)'}: {self.message}"


class SLayerValidationError(SLayerError, ValueError):
    """A block is not valid S-LAYER vocabulary, or not valid for its member type."""

    def __init__(self, issues: Iterable[Issue]) -> None:
        self.issues: tuple[Issue, ...] = tuple(issues)
        super().__init__(self._render())

    def _render(self) -> str:
        count = len(self.issues)
        noun = "problem" if count == 1 else "problems"
        lines = [f"invalid s_layer block ({count} {noun}):"]
        lines.extend(f"  {issue}" for issue in self.issues)
        return "\n".join(lines)


class SpecTooLongError(SLayerError, ValueError):
    """The compact ``S_LAYER_SPEC`` payload is longer than a tag value can hold."""

    def __init__(self, spec: str, limit: int) -> None:
        self.spec = spec
        self.limit = limit
        super().__init__(
            f"S_LAYER_SPEC payload is {len(spec)} characters, over the {limit}-character tag"
            f" limit: {spec}"
        )
