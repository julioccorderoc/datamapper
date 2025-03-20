"""
path_manager.py
===============

This module provides the `DynamicPathManager` class to handle
dynamic path tracking during data mapping operations.

"""

from contextlib import contextmanager
from typing import Generator, Tuple, cast

from .exceptions import InvalidPathSegmentError, UnknownPathTypeException
from .types import PathEntryType, PathRegistryType


class DynamicPathManager:
    """
    Handles dynamic path tracking during mapping operations.
    Maintains separate path stacks that can be created on demand for different path types.
    Each path includes its main model name and current path segments.

    Example paths:
        - CustomModel.field_name
        - AnotherModel.nested.field.path
        - SourceModel.list_field[0].nested_field
    """

    def __init__(self, *path_configs: Tuple[str, str]):
        """
        Initialize with path configurations containing (path_type, model_name)

        Args:
            path_configs: Tuples of (path_identifier, associated_model_name)

        Example:
            >>> tracker = DynamicPathManager(("source", "UserModel"), ("target", "ProfileModel"))
            >>> tracker = DynamicPathManager(
            ...     ("input", "RequestModel"),
            ...     ("output", "ResponseModel"),
            ...     ("intermediate", "ProcessModel")
            ... )
        """
        self._path_registry: PathRegistryType = {}
        for path_type, model_name in path_configs:
            self.create_path_type(path_type, model_name)

    def create_path_type(self, path_identifier: str, model_name: str) -> None:
        """
        Create new path type with associated model name

        Args:
            path_identifier: Unique identifier for the path type
            model_name: Associated model name for path formatting
        """
        if self._is_valid_path(path_identifier):
            print(f"Path type '{path_identifier}' already exists.")
            return

        self._path_registry[path_identifier] = {"model": model_name, "segments": []}

    @contextmanager
    def track_segment(self, path_identifier: str, segment: str) -> Generator[None, None, None]:
        """
        Context manager for tracking path segments for any path type.

        Args:
            path_identifier: Identifier for the path type
            segment: Path segment to append (e.g., "field_name" or "[0]")

        Raises:
            UnknownPathTypeException: If path_identifier is not recognized
            InvalidPathSegmentError: If trying to add list index without a preceding segment

        Example:
            >>> with tracker.track_segment("source", "user"):
            >>>     with tracker.track_segment("source", "[0]"):
            >>>         # Path will be "SourceModel.user[0]"
        """
        self._validate_path_exists(path_identifier)
        registry_entry = self._path_registry[path_identifier]

        try:
            self._append_segment(path_identifier, registry_entry, segment)
            yield
        finally:
            self._remove_segment(registry_entry, segment)

    def get_path(self, path_identifier: str) -> str:
        """
        Get the path for a specific path type, including the model name.

        Args:
            path_identifier: Identifier for the path type

        Returns:
            str: Full path including model name and all segments

        Raises:
            UnknownPathTypeException: If path_identifier is not recognized
        """
        self._validate_path_exists(path_identifier)
        entry = self._path_registry[path_identifier]
        model_name = cast(str, entry["model"])
        segments = cast(list[str], entry["segments"])
        return f"{model_name}.{'.'.join(segments)}" if segments else model_name

    def _is_valid_path(self, path_identifier: str) -> bool:
        """Validate if the path type exists in the registry"""
        return path_identifier in self._path_registry

    def _validate_path_exists(self, path_identifier: str) -> None:
        """Centralized validation with improved error message"""
        if not self._is_valid_path(path_identifier):
            available = list(self._path_registry.keys())
            raise UnknownPathTypeException(path_identifier, available)

    def _append_segment(
        self,
        path_identifier: str,
        registry_entry: PathEntryType,
        segment: str,
    ) -> None:
        """Segment appending logic"""
        segments = cast(list[str], registry_entry["segments"])

        if self._is_list_index(segment):
            if not segments:
                raise InvalidPathSegmentError(path_type=path_identifier, segment=segment)
            segments[-1] += segment
        else:
            segments.append(segment)

    def _remove_segment(self, registry_entry: PathEntryType, segment: str) -> None:
        """Extracted segment removal logic"""
        segments = cast(list[str], registry_entry["segments"])

        if self._is_list_index(segment):
            segments[-1] = segments[-1].replace(segment, "", 1)
        else:
            segments.pop()

    @staticmethod
    def _is_list_index(segment: str) -> bool:
        """Validation for list index format"""
        return segment.startswith("[") and segment.endswith("]")

    def list_path_types(self) -> list[str]:
        """
        Returns:
            list[str]: List of path type identifiers
        """
        return list(self._path_registry.keys())

    def clear(self) -> None:
        """
        Clears all path types and their associated segments.
        """
        self._path_registry.clear()


path_manager = DynamicPathManager()
