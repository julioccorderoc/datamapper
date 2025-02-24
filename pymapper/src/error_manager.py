from dataclasses import dataclass
from enum import Enum
from typing import List
import logging

from .path_manager import DynamicPathManager

class MappingErrorType(Enum):
    """Enumeration of possible mapping error types"""
    REQUIRED_TARGET_FIELD_MISSING = "required_target_field_missing"
    TYPE_CONVERSION_ERROR = "type_conversion_error"
    NESTED_MODEL_CREATION = "nested_model_creation"
    NESTED_MODEL_MAPPING = "nested_model_mapping"
    NESTED_MODEL_REQUIRED_FIELD = "nested_model_required_field"
    NESTED_MODEL_PARTIAL_RETURN = "nested_model_partial_return"
    NESTED_MODEL_EMPTY = "nested_model_empty"
    LIST_MAPPING_ERROR = "list_mapping_error"

@dataclass
class MappingError:
    """Represents a single mapping error"""
    field_path: str
    error_type: MappingErrorType
    details: str


class ErrorHandler:
    def __init__(self, logger: logging.Logger):
        self.mapping_errors: List[MappingError] = []
        self.logger = logger
        self._path_manager = DynamicPathManager()

    def add(self, error_type: MappingErrorType, details: str) -> None:
        """Adds a mapping error to the error list with context"""
        field_path = self._path_manager.get_path("target")
        self.mapping_errors.append(MappingError(field_path=field_path,
                                                error_type=error_type, 
                                                details=details))
        
        self.logger.warning(f"❌ Mapping error for field '{field_path}': [{error_type.value}] {details}")


    def remove(self, error_type: MappingErrorType) -> None:
        """
        Removes mapping errors that match the given type and current path.
        
        For REQUIRED_FIELD_MISSING, matches any errors whose paths start with the current path.
        This is to remove the case for the las try to build list of models, where it won't find
        the last model due to the iterative nature of the process
        """

        field_path = self._path_manager.get_path("target")
         
        def should_keep_error(error: MappingError) -> bool:
            if error.error_type != error_type:
                return True
            if error_type == MappingErrorType.NESTED_MODEL_REQUIRED_FIELD:
                return not error.field_path.startswith(field_path)
            else:
                return error.field_path != field_path

        original_count = len(self.mapping_errors)
        self.mapping_errors = [error for error in self.mapping_errors if should_keep_error(error)]

        removed_count = original_count - len(self.mapping_errors)
        if removed_count > 0:
            self.logger.debug(f"👉 Removed {removed_count} mapping error(s) [{error_type.value}] in: '{field_path}'")

    def display(self) -> None:
        """Logs all accumulated mapping errors"""
        if self.mapping_errors:
            self.logger.error("📊 Mapping completed with the following issues:")
            for error in self.mapping_errors:
                print(f"  - Target field: {error.field_path}\n"
                      f"    Error type: {error.error_type.name}\n"
                      f"    Error details: {error.details}")

