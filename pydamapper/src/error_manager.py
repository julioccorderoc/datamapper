"""
error_manager.py
================

Provides functionality for managing errors.
Takes care of tracking, formatting, and managing error states.
"""

from typing import Any
from pydantic import ConfigDict, ValidationError, create_model

from pydamapper.src.path_manager import DynamicPathManager, path_manager
from pydamapper._errors_handling.messages import (
    generate_summary,
    generate_details,
    field_required,
    type_validation,
    partial_model,
    empty_model,
    limit_reach,
)
from pydamapper._errors_handling.structures import ErrorDetails, ErrorType
from pydamapper._errors_handling.registry import ErrorRegistry


class ErrorManager:
    """
    Manages errors during the data mapping process, providing methods to log,
    format, and handle various error types.
    """

    def __init__(self, path_manager: DynamicPathManager) -> None:
        """Initializes the ErrorManager with a path manager."""
        self._path_manager = path_manager
        self.error_registry = ErrorRegistry(self._path_manager)

    @property
    def errors(self) -> ErrorRegistry:
        """Returns the list of errors managed by this instance."""
        return self.error_registry

    def has_errors(self) -> bool:
        """Returns: True if there are errors, False otherwise."""
        return len(self.error_registry) > 0

    def display(self, target_model_name: str) -> None:
        """Displays a summary and detailed report of the errors."""
        summary = generate_summary(self.error_registry, target_model_name)
        details = generate_details(self.error_registry)
        disclaimer = "⚠️ Returning partially mapped data."
        display = f"{summary}\n\n{details}\n\n{disclaimer}\n"
        print(display)

    def required_field(self, source_model_name: str, parent_model_name: str) -> None:
        """Adds an error for a required field that is missing."""
        field_path = self._path_manager.get_path("target")
        field_name = field_path.split(".")[-1]
        error_message = field_required.substitute(
            field_name=field_name,
            parent_model_name=parent_model_name,
            source_model_name=source_model_name,
        )
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.REQUIRED_FIELD,
            details=error_message,
        )
        self.error_registry.add(ErrorType.REQUIRED_FIELD, new_error)

    def is_valid_type(
        self, target_path: str, target_type: type, source_value: Any, source_type: type
    ) -> bool:
        """Validates if the source value can be coerced to the target type."""
        is_valid: bool = self._can_be_assigned(source_value, target_type)
        if is_valid:
            return True

        self.add_validation_error(target_path, target_type, str(source_value), source_type)
        return False

    def new_model_partial(self, new_model_name: str) -> None:
        """Adds an error indicating that a new model was partially built."""
        field_path = self._path_manager.get_path("target")
        error_message = partial_model.substitute(new_model_name=new_model_name)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.PARTIAL_RETURN,
            details=error_message,
        )
        self.error_registry.add(ErrorType.PARTIAL_RETURN, new_error)

    def new_model_empty(self, new_model_name: str) -> None:
        """Adds an error indicating that no data was found to build a new model."""
        field_path = self._path_manager.get_path("target")
        error_message = empty_model.substitute(new_model_name=new_model_name)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.EMPTY_MODEL,
            details=error_message,
        )
        # If there's not data, I have to remove the required field error to avoid redundancy
        self.error_registry.remove(ErrorType.REQUIRED_FIELD)
        self.error_registry.add(ErrorType.EMPTY_MODEL, new_error)

    def reach_limit_iter(self, limit: int, model_name: str) -> None:
        """Adds an error indicating that the limit of new models was reached."""
        field_path = self._path_manager.get_path("target")
        error_message = limit_reach.substitute(limit=limit, new_model_name=model_name)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.LIMIT_REACH,
            details=error_message,
        )
        self.error_registry.add(ErrorType.LIMIT_REACH, new_error)

    def last_available_index(self) -> None:
        """Removes the empty model error created after the last available index."""
        self.error_registry.remove(ErrorType.EMPTY_MODEL)

    def add_validation_error(
        self, field_path: str, target_type: type, source_value: str, source_type: type
    ) -> None:
        """Adds an error for a validation error."""
        field_name = field_path.split(".")[-1]
        error_message = type_validation.substitute(
            field_name=field_name,
            field_type=target_type.__name__,
            value=source_value,
            value_type=source_type.__name__,
        )
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.VALIDATION,
            details=error_message,
        )
        self.error_registry.add(ErrorType.VALIDATION, new_error)

    def _can_be_assigned(self, source_value: Any, target_type: type, strict: bool = False) -> bool:
        """Checks if a value can be coerced to a type."""

        TempModel = create_model(
            "TempModel", field=(target_type, ...), __config__=ConfigDict(strict=strict)
        )

        try:
            TempModel(field=source_value)
            return True
        except ValidationError:
            return False


error_manager = ErrorManager(path_manager)
