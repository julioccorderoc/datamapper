from typing import Set

class FieldCache:
    """
    Manages path tracking to prevent reusing the same source fields during mapping.
    The cache stores the full source paths that have been matched, ensuring each
    source field is only used once.
    """
    
    def __init__(self):
        self._cache: Set[str] = set()
    
    def is_cached(self, field_path: str) -> bool:
        return field_path in self._cache
    
    def add(self, field_path: str) -> None:
        self._cache.add(field_path)
    
    def clear(self) -> None:
        self._cache.clear()