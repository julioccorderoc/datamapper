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

    def add(self, error_type: ErrorType, error_details: ErrorDetails) -> None:
        """
        Adds a mapping error to the error list with context.

        Args:
            error_type (ErrorType): The type of error to add.
            error_details (ErrorDetails): The details of the error.
        """
        self.errors[error_type].append(error_details)

    def remove(self, error_type: ErrorType) -> None:
        """
        Removes mapping errors of the specified type that match the current path context.
        For nested model errors (REQUIRED_FIELD), removes errors in child paths.
        For other error types, removes only exact path matches.

        Args:
            error_type (ErrorType): The type of error to remove.
        """
        field_path = self._path_manager.get_path("target")
        error_list = self.errors[error_type]  # Direct access to target type's list

        original_count = len(error_list)
        if original_count == 0:
            return

        # Apply path-based filtering to the specific error type's list
        filtered_errors = [
            error for error in error_list if self._should_keep_error(error, error_type, field_path)
        ]

        removed_count = original_count - len(filtered_errors)
        if removed_count > 0:
            if filtered_errors:  # If there are still errors left, update the list
                self.errors[error_type] = filtered_errors
            else:  # If no errors are left, remove the key entirely
                del self.errors[error_type]

    def _should_keep_error(
        self, error_details: ErrorDetails, target_type: ErrorType, current_path: str
    ) -> bool:
        """
        Path-based retention criteria for a known error type.

        Args:
            error: The error to evaluate
            target_type: Error type to match for removal
            current_path: Field path context for removal criteria

        Returns:
            True if the error should be kept, False if it should be removed
        """
        if target_type == ErrorType.REQUIRED_FIELD:
            return not error_details.field_path.startswith(current_path)
        return error_details.field_path != current_path

    def clear(self) -> None:
        """Clears all errors from the error list."""
        self.errors.clear()
