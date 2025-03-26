from collections import defaultdict

from pydamapper.src.path_manager import DynamicPathManager
from pydamapper.src.error_handling.structures import ErrorDetails, ErrorType


class ErrorRegistry(defaultdict[ErrorType, list[ErrorDetails]]):
    """Manages errors grouped by type with path-aware removal."""

    def __init__(self, path_manager: DynamicPathManager):
        super().__init__(list)
        self._path_manager = path_manager

    def __setitem__(self, key: ErrorType, value: list[ErrorDetails]) -> None:
        """Prevent invalid assignments (e.g., non-list values)."""
        if not isinstance(value, list):
            raise TypeError("Values must be lists of ErrorDetails")
        super().__setitem__(key, value)

    def __len__(self) -> int:
        """Total number of errors across all types."""
        return sum(len(errors) for errors in self.values())

    def __str__(self) -> str:
        """Returns a string representation of the error list."""
        return f"{self.generate_summary()}\n\n{self.generate_details()}\n"

    def add(self, error_details: ErrorDetails) -> None:
        """Adds an error to the registry under its type."""
        self[error_details.error_type].append(error_details)

    def remove(
        self,
        error_type: ErrorType,
        just_children: bool = False,
    ) -> None:
        """Removes errors matching the current path (and children if specified)."""
        current_path = self._path_manager.get_path("target")
        if not self.get(error_type):
            return

        filtered_errors = [
            error
            for error in self[error_type]
            if not self._is_error_match(error, current_path, just_children)
        ]
        self[error_type] = filtered_errors

    @staticmethod
    def _is_error_match(error: ErrorDetails, current_path: str, just_children: bool) -> bool:
        """Determines if an error's path matches the current context."""
        error_path = error.field_path
        return error_path.startswith(current_path) if just_children else error_path == current_path

    def generate_summary(self) -> str:
        """Generates a summary report of errors found during mapping."""
        summary = [f"Error(s) found: '{len(self)}':\n"]
        for error_type, errors in self.items():
            summary.append(f"  > {len(errors)} {error_type.name}")
        return "\n".join(summary)

    def generate_details(self) -> str:
        """Generates a detailed report of all errors in the error list."""
        details = []
        for error_type, errors in self.items():
            for error in errors:
                details.append(
                    f"      + Field: {error.field_path}\n"
                    f"        Type: {error_type.name}\n"
                    f"        Description: {error_type.value}\n"
                    f"        Message: {error.details}"
                )
        return "\n".join(details) if details else "No errors found."
