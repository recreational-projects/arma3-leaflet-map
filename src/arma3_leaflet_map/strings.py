"""String handling functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def format_iterable_of_str(iterable: Iterable[str]) -> str:
    """Format iterable as string."""
    return ", ".join(f"'{i}'" for i in iterable)
