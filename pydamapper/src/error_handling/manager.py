"""
error_manager.py
================

Provides functionality for managing errors.
Takes care of tracking, formatting, and managing error states.
"""

from typing import Any
from pydantic import ConfigDict, ValidationError, create_model
from string import Template

from pydamapper.src.path_manager import DynamicPathManager, path_manager
from pydamapper.src.error_handling.structures import ErrorDetails, ErrorType
from pydamapper.src.error_handling.registry import ErrorRegistry


# ----------------------------
# Templates for error messages
# ----------------------------

field_required = Template(
    "The field '$field_name' is required in the '$parent_model_name' model "
    "and could not be matched in the '$source_model_name' model."
)

type_validation = Template(
    "The field '$field_name' of type '$field_type' cannot match "
    "the value '$value' of type '$value_type'"
)

partial_model = Template("The new model '$new_model_name' was partially built.")

empty_model = Template("No data found to build the new model '$new_model_name'.")

limit_reach = Template(
    "Limit of '$limit' reach for building list of '$new_model_name' models. "
    "IF YOU WANT TO EXTEND THE LIMIT UPDATE THE CONFIG."
)


class ErrorManager:
    """
    Manages errors during the data mapping process, providing methods to log,
    format, and handle various error types.
    """

    def __init__(self, path_manager: DynamicPathManager) -> None:
        """Initializes the ErrorManager with a path manager."""
        self._path_manager = path_manager
        self.error_registry = ErrorRegistry(self._path_manager)

    def __str__(self) -> str:
        """Displays a summary and detailed report of the errors."""
        errors_summary: str = str(self.error_registry)
        disclaimer: str = "⚠️ Returning partially mapped data."
        display: str = f"{errors_summary}\n{disclaimer}\n"
        return display

    @property
    def errors(self) -> ErrorRegistry:
        """Returns the list of errors managed by this instance."""
        return self.error_registry

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
        self.errors.add(new_error)

    def is_valid_type(
        self, target_path: str, target_type: type, source_value: Any, source_type: type
    ) -> bool:
        """Validates if the source value can be coerced to the target type."""
        can_be_assigned: bool = self._can_be_assigned(source_value, target_type)
        if can_be_assigned:
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
        self.errors.add(new_error)

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
        self.errors.remove(ErrorType.REQUIRED_FIELD, just_children=True)
        self.errors.add(new_error)

    def reach_limit_iter(self, limit: int, model_name: str) -> None:
        """Adds an error indicating that the limit of new models was reached."""
        field_path = self._path_manager.get_path("target")
        error_message = limit_reach.substitute(limit=limit, new_model_name=model_name)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.LIMIT_REACH,
            details=error_message,
        )
        self.errors.add(new_error)

    def last_available_index(self) -> None:
        """Removes the empty model error created after the last available index."""
        self.errors.remove(ErrorType.EMPTY_MODEL)

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
        self.errors.add(new_error)

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
