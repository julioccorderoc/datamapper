from collections import defaultdict
from typing import Iterable, Optional, DefaultDict, List

from pydamapper.src.path_manager import DynamicPathManager
from pydamapper._errors_handling.structures import ErrorDetails, ErrorType


class ErrorRegistry:
    """A class to manage and store errors associated with different error types."""

    def __init__(self, path_manager: DynamicPathManager) -> None:
        """Initializes the ErrorRegistry with a path manager."""
        self.errors: DefaultDict[ErrorType, List[ErrorDetails]] = defaultdict(list)
        self._path_manager = path_manager

    def __len__(self) -> int:
        """Returns the total number of errors across all error types."""
        return sum(len(errors) for errors in self.errors.values())

    def __contains__(self, error_type: ErrorType) -> bool:
        """Checks if a specific error type is present in the error list."""
        return error_type in self.errors

    def __bool__(self) -> bool:
        """Returns True if there are any errors in the list, False otherwise."""
        return bool(self.errors)

    def __repr__(self) -> str:
        """Returns a string representation of the error list."""
        return repr(self.errors)

    def items(self) -> Iterable[tuple[ErrorType, list[ErrorDetails]]]:
        """Returns an iterable view of the error type and error details pairs."""
        return self.errors.items()

    def keys(self) -> list[ErrorType]:
        """Returns a list of all error types present in the error list."""
        return list(self.errors.keys())

    def get(self, error_type: ErrorType) -> Optional[list[ErrorDetails]]:
        """Retrieves the list of error details for a specific error type."""
        return self.errors.get(error_type)

    def values(self) -> list[list[ErrorDetails]]:
        """Returns a list of all error details lists for each error type."""
        return list(self.errors.values())

    def add(self, error_details: ErrorDetails) -> None:
        """
        Adds a mapping error to the error list with context.

        Args:
            error_type (ErrorType): The type of error to add.
            error_details (ErrorDetails): The details of the error.
        """
        self.errors[error_details.error_type].append(error_details)

    def remove(
        self,
        error_type: ErrorType,
        just_children: bool = False,
    ) -> None:
        """
        Removes errors matching current path context with option to include child paths.

        Args:
            error_type: Type of error to remove
            just_children: When True, removes errors in child paths (default: False)
        """
        current_path = self._path_manager.get_path("target")

        if not self.errors[error_type]:
            return

        original_errors = self.errors[error_type]
        kept_errors = []
        for error in original_errors:
            if not self._is_error_match(error, current_path, just_children):
                kept_errors.append(error)

        self.errors[error_type] = kept_errors

    @staticmethod
    def _is_error_match(error: ErrorDetails, current_path: str, just_children: bool) -> bool:
        """Helper function to check if an error matches the current path context."""
        error_path = error.field_path

        if just_children:
            return error_path.startswith(current_path)
        return error_path == current_path

    def clear(self) -> None:
        """Clears all errors from the error list."""
        self.errors.clear()
