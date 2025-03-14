"""
field_cache.py
==============

This module provides a `FieldCache` class to manage path tracking during the data mapping process.
It ensures that each source field is only used once by storing the full source paths that have been matched.

"""

from typing import Set


class FieldCache:
    """
    Manages path tracking to prevent reusing the same source fields during mapping.
    The cache stores the full source paths that have been matched, ensuring each
    source field is only used once.
    """

    def __init__(self) -> None:
        """Initializes an empty cache to store source field paths."""
        self._cache: Set[str] = set()

    def is_cached(self, field_path: str) -> bool:
        """Checks if a field path is already cached."""
        return field_path in self._cache

    def add(self, field_path: str) -> None:
        """Adds a field path to the cache."""
        self._cache.add(field_path)

    def clear(self) -> None:
        """Clears the cache."""
        self._cache.clear()
