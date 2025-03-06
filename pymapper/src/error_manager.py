from dataclasses import dataclass
from enum import Enum
from typing import Any, List, DefaultDict
from collections import defaultdict
from pydantic import BaseModel, ValidationError, ConfigDict

from .path_manager import DynamicPathManager
from .logger_config import logger


class ErrorType(Enum):
    """Enumeration of possible mapping errors"""

    VALIDATION = "Attemp to match a value with the wrong type"
    REQUIRED_FIELD = "Required field not found in source data"
    PARTIAL_RETURN = "The new model was partially created"
    EMPTY_MODEL = "Non of the fields in the new model were found in the source data"
    FIELD_CREATION = "An unexpected error occurred while creating a field"


@dataclass
class ErrorDetails:
    """Represents the details of an error"""

    field_path: str
    error_type: ErrorType
    details: str


class ErrorList:
    def __init__(self, path_manager: DynamicPathManager):
        self.errors: DefaultDict[ErrorType, List[ErrorDetails]] = defaultdict(list)
        self.logger = logger
        self._path_manager = path_manager

    def __len__(self) -> int:
        return sum(len(errors) for errors in self.errors.values())

    def __contains__(self, error_type: ErrorType) -> bool:
        return error_type in self.errors

    def __bool__(self) -> bool:
        return bool(self.errors)

    def __repr__(self) -> str:
        return repr(self.errors)

    def items(self):
        return self.errors.items()

    def keys(self) -> List[ErrorType]:
        return self.errors.keys()

    def get(self, error_type: ErrorType) -> List[ErrorDetails]:
        return self.errors.get(error_type)

    def values(self) -> List[List[ErrorDetails]]:
        return self.errors.values()

    def add(self, error_type: ErrorType, error_details: ErrorDetails) -> None:
        """Adds a mapping error to the error list with context"""

        field_path = self._path_manager.get_path("target")

        self.errors[error_type].append(error_details)

        self.logger.warning(
            f"❌ Error in field '{field_path}': [{error_type.name}] >>> {error_details.details}"
        )

    def remove(self, error_type: ErrorType) -> None:
        """
        Removes mapping errors of the specified type that match the current path context.

        For nested model errors (REQUIRED_FIELD), removes errors in child paths.
        For other error types, removes only exact path matches.
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
            self.logger.warning(
                f"🗑️ Removed '{removed_count}' {error_type.name} error(s) in path: '{field_path}'"
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
        self.errors.clear()


class ErrorFormatter:
    """SRP: Formats error data into structured reports"""

    @staticmethod
    def generate_summary(error_list: ErrorList, target_name: str) -> str:
        summary = [
            f"'{len(error_list)}' error(s) found while mapping '{target_name}':\n"
        ]
        for error_type, errors in error_list.items():
            summary.append(f"  > {len(errors)} {error_type.name}")
        return "\n".join(summary)

    @staticmethod
    def generate_details(error_list: ErrorList) -> str:
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
        message = f"The field '{field_name}' is required in the '{parent_model_name}' model and could not be matched in the '{source_model_name}' model."
        return message

    @staticmethod
    def validation_detail(
        field_name: str, field_type: str, value: str, value_type: str
    ) -> str:
        message = f"The field '{field_name}' of type '{field_type}' cannot match the value '{value}' of type '{value_type}'"
        return message

    @staticmethod
    def partial_detail(new_model_name: str) -> str:
        message = f"The new model '{new_model_name}' was partially built."
        return message

    @staticmethod
    def empty_detail(new_model_name: str) -> str:
        message = f"No data found to build the new model '{new_model_name}'."
        return message

    @staticmethod
    def field_creation_detail(error: Exception) -> str:
        message = f"An unexpected error occurred while creating a field: {str(error)}"
        return message


class ErrorManager:
    def __init__(self, path_manager: DynamicPathManager):
        self.logger = logger
        self._path_manager = path_manager
        self.error_list = ErrorList(self._path_manager)
        self.formatter = ErrorFormatter()

    @property
    def errors(self):
        return self.error_list

    def has_errors(self) -> bool:
        return len(self.error_list) > 0

    def display(self, target_model_name: str) -> None:
        summary: str
        details: str
        display: str

        summary = self.formatter.generate_summary(self.error_list, target_model_name)
        details = self.formatter.generate_details(self.error_list)
        display = f"{summary}\n\n{details}\n"

        self.logger.error(display)

    def required_field(
        self, field_path: str, source_model_name: str, parent_model_name: str
    ) -> None:
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
        self, target_path: str, target_type: str, source_value: str, source_type: str
    ) -> None:
        if self.is_valid_type(source_value, target_type):
            return

        self.add_validation_error(target_path, target_type, source_value, source_type)

    def new_model_partial(self, field_path: str, new_model_name: str) -> None:
        error_message = self.formatter.partial_detail(new_model_name)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.PARTIAL_RETURN,
            details=error_message,
        )
        self.error_list.add(ErrorType.PARTIAL_RETURN, new_error)

    def error_creating_field(self, error: Exception) -> None:
        field_path = self._path_manager.get_path("target")
        error_message = self.formatter.field_creation_detail(error)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.FIELD_CREATION,
            details=error_message,
        )
        self.error_list.add(ErrorType.FIELD_CREATION, new_error)

    def new_model_empty(self, field_path: str, new_model_name: str) -> None:
        error_message = self.formatter.empty_detail(new_model_name)
        new_error = ErrorDetails(
            field_path=field_path,
            error_type=ErrorType.EMPTY_MODEL,
            details=error_message,
        )
        # If there's not data, I have to remove the required field error to avoid redundancy
        self.error_list.remove(ErrorType.REQUIRED_FIELD)
        self.error_list.add(ErrorType.EMPTY_MODEL, new_error)

    def last_available_index(self) -> None:
        self.error_list.remove(ErrorType.EMPTY_MODEL)

    def add_validation_error(
        self, field_path: str, target_type: str, source_value: str, source_type: str
    ) -> None:
        field_name = field_path.split(".")[-1]
        error_message = self.formatter.validation_detail(
            field_name, target_type, source_value, source_type
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

        class TempModel(BaseModel):
            model_config = ConfigDict(strict=strict)
            field: target_type  # I get a warning because types shouldn't been variables

        try:
            TempModel(field=source_value)
            return True
        except ValidationError:
            return False
