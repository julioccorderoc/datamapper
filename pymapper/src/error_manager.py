"""
error_manager.py
================

This module provides functionality for managing and formatting errors during the data mapping process.
It includes classes for tracking errors, formatting error messages, and managing error states.

Classes:
--------
- `ErrorType`: Enumeration of possible mapping errors.
- `ErrorDetails`: Data class representing the details of an error.
- `ErrorList`: Manages a list of errors with methods to add, remove, and query errors.
- `ErrorFormatter`: Provides static methods to format error data into structured reports.
- `ErrorManager`: Manages errors during the data mapping process, providing methods to log,
  format, and handle various error types.

"""

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional, Any, List, DefaultDict
from collections import defaultdict
from pydantic import ValidationError, ConfigDict, create_model

from .path_manager import DynamicPathManager
from .logger_config import logger


class ErrorType(Enum):
    """Enumeration of possible mapping errors"""

    VALIDATION = "Attemp to match a value with the wrong type"
    REQUIRED_FIELD = "Required field not found in source data"
    PARTIAL_RETURN = "The new model was partially created"
    EMPTY_MODEL = "Non of the fields in the new model were found in the source data"
    FIELD_CREATION = "An unexpected error occurred while creating a field"
    TYPE_VALIDATION = "Field type validation failed"


@dataclass
class ErrorDetails:
    """Represents the details of an error"""

    field_path: str
    error_type: ErrorType
    details: str


class ErrorList:
    """A class to manage and store errors associated with different error types."""

    def __init__(self, path_manager: DynamicPathManager) -> None:
        """Initializes the ErrorList with a path manager."""
        self.errors: DefaultDict[ErrorType, List[ErrorDetails]] = defaultdict(list)
        self._logger = logger
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
        field_path = self._path_manager.get_path("target")

        self.errors[error_type].append(error_details)

        self._logger.warning(
            "❌ Error in field '%s': [%s] >>> %s",
            field_path,
            error_type.name,
            error_details.details,
        )

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
            error
            for error in error_list
            if self._should_keep_error(error, error_type, field_path)
        ]

        removed_count = original_count - len(filtered_errors)
        if removed_count > 0:
            if filtered_errors:  # If there are still errors left, update the list
                self.errors[error_type] = filtered_errors
            else:  # If no errors are left, remove the key entirely
                del self.errors[error_type]
            self._logger.warning(
                "🗑️ Removed '%s' %s error(s) in path: '%s'",
                removed_count,
                error_type.name,
                field_path,
            )

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


class ErrorFormatter:
    """Formats error data into structured reports"""

    @staticmethod
    def generate_summary(error_list: ErrorList, target_name: str) -> str:
        """Generates a summary report of errors found during mapping."""
        summary = [
            f"'{len(error_list)}' error(s) found while mapping '{target_name}':\n"
        ]
        for error_type, errors in error_list.items():
            summary.append(f"  > {len(errors)} {error_type.name}")
        return "\n".join(summary)

    @staticmethod
    def generate_details(error_list: ErrorList) -> str:
        """Generates a detailed report of all errors in the error list."""
        details = []
        for error_type, errors in error_list.items():
            for error in errors:
                details.append(
                    f"      + Field: {error.field_path}\n"
                    f"        Type: {error_type.name}\n"
                    f"        Description: {error_type.value}\n"
                    f"        Message: {error.details}"
                )
        return "\n".join(details) if details else "No errors found."

    @staticmethod
    def required_detail(
        field_name: str, source_model_name: str, parent_model_name: str
    ) -> str:
        """Generates a detailed message for a required field error."""
        message = message = (
            f"The field '{field_name}' is required in the '{parent_model_name}' model"
            f"and could not be matched in the '{source_model_name}' model."
        )
        return message

    @staticmethod
    def validation_detail(
        field_name: str, field_type: str, value: str, value_type: str
    ) -> str:
        """Generates a detailed message for a validation error."""
        message = (
            f"The field '{field_name}' of type '{field_type}' cannot match"
            f"the value '{value}' of type '{value_type}'"
        )
        return message

    @staticmethod
    def partial_detail(new_model_name: str) -> str:
        """Generates a message indicating that a new model was partially built."""
        message = f"The new model '{new_model_name}' was partially built."
        return message

    @staticmethod
    def empty_detail(new_model_name: str) -> str:
        """Generates a message indicating that no data was found to build a new model."""
        message = f"No data found to build the new model '{new_model_name}'."
        return message

    @staticmethod
    def field_creation_detail(error: Exception) -> str:
        """Generates a message for an unexpected error during field creation."""
        message = f"An unexpected error occurred while creating a field: {str(error)}"
        return message


class ErrorManager:
    """
    Manages errors during the data mapping process, providing methods to log,
    format, and handle various error types.
    """

    def __init__(self, path_manager: DynamicPathManager) -> None:
        """Initializes the ErrorManager with a path manager."""
        self._logger = logger
        self._path_manager = path_manager
        self.error_list = ErrorList(self._path_manager)
        self.formatter = ErrorFormatter()

    @property
    def errors(self) -> ErrorList:
        """Returns the list of errors managed by this instance."""
        return self.error_list

    def has_errors(self) -> bool:
        """
        Checks if there are any errors in the error list.

        Returns:
            bool: True if there are errors, False otherwise.
        """
        return len(self.error_list) > 0

    def display(self, target_model_name: str) -> None:
        """Displays a summary and detailed report of the errors."""

        summary = self.formatter.generate_summary(self.error_list, target_model_name)
        details = self.formatter.generate_details(self.error_list)
        display = f"{summary}\n\n{details}\n"

        self._logger.error(display)

    def required_field(
        self, field_path: str, source_model_name: str, parent_model_name: str
    ) -> None:
        """Adds an error for a required field that is missing."""
        field_path = self._path_manager.get_path("target")
        field_name = field_path.split(".")[-1]
        error_message = self.formatter.required_detail(
            field_name, source_model_name, parent_model_name
        )
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.REQUIRED_FIELD,
            details=error_message,
        )
        self.error_list.add(ErrorType.REQUIRED_FIELD, new_error)

    def validate_type(
        self, target_path: str, target_type: type, source_value: Any, source_type: type
    ) -> None:
        """Validates if the source value can be coerced to the target type."""
        if self.is_valid_type(source_value, target_type):
            return

        self.add_validation_error(
            target_path, target_type, str(source_value), source_type
        )

    def new_model_partial(self, field_path: str, new_model_name: str) -> None:
        """Adds an error indicating that a new model was partially built."""
        error_message = self.formatter.partial_detail(new_model_name)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.PARTIAL_RETURN,
            details=error_message,
        )
        self.error_list.add(ErrorType.PARTIAL_RETURN, new_error)

    def error_creating_field(self, error: Exception) -> None:
        """Adds an error for an unexpected error during field creation."""
        field_path = self._path_manager.get_path("target")
        error_message = self.formatter.field_creation_detail(error)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.FIELD_CREATION,
            details=error_message,
        )
        self.error_list.add(ErrorType.FIELD_CREATION, new_error)

    def new_model_empty(self, field_path: str, new_model_name: str) -> None:
        """Adds an error indicating that no data was found to build a new model."""
        error_message = self.formatter.empty_detail(new_model_name)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.EMPTY_MODEL,
            details=error_message,
        )
        # If there's not data, I have to remove the required field error to avoid redundancy
        self.error_list.remove(ErrorType.REQUIRED_FIELD)
        self.error_list.add(ErrorType.EMPTY_MODEL, new_error)

    def type_error(self, error: Exception) -> None:
        """Logs model type validation errors"""
        field_path = self._path_manager.get_path("target")
        error_details = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.TYPE_VALIDATION,
            details=f"Type mismatch: {str(error)}",
        )
        self.error_list.add(ErrorType.TYPE_VALIDATION, error_details)

    def last_available_index(self) -> None:
        """Removes the empty model error created after the last available index."""
        self.error_list.remove(ErrorType.EMPTY_MODEL)

    def add_validation_error(
        self, field_path: str, target_type: type, source_value: str, source_type: type
    ) -> None:
        """Adds an error for a validation error."""
        field_name = field_path.split(".")[-1]
        error_message = self.formatter.validation_detail(
            field_name, target_type.__name__, source_value, source_type.__name__
        )
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.VALIDATION,
            details=error_message,
        )
        self.error_list.add(ErrorType.VALIDATION, new_error)

    def is_valid_type(
        self, source_value: Any, target_type: type, strict: bool = False
    ) -> bool:
        """Checks if a value can be coerced to a type."""

        TempModel = create_model(
            "TempModel", field=(target_type, ...), __config__=ConfigDict(strict=strict)
        )

        try:
            TempModel(field=source_value)
            return True
        except ValidationError:
            return False
