"""
exceptions.py
=============

This module defines custom exceptions used within the pydamapper package.

"""


class PyDaMapperException(Exception):
    """Base class for all exceptions raised by pydamapper"""


class MappingError(PyDaMapperException):
    """Raised when an unindentified error happens"""

    def __init__(self, source_model_name: str, target_model_name: str, error: Exception):
        self.source_model_name = source_model_name
        self.target_model_name = target_model_name
        super().__init__(
            f"Mapping between '{source_model_name}' and '{target_model_name}' "
            f"failed due to the error: {str(error)}."
        )


class InvalidArguments(PyDaMapperException):
    """Raised when invalid arguments are passed"""

    def __init__(self, invalid_model_name: str):
        self.invalid_model_name = invalid_model_name
        super().__init__(f"The '{invalid_model_name}' argument is not valid.")


class NoMappableData(PyDaMapperException):
    """Raised when there's no mapped data"""

    def __init__(self, source_model_name: str, target_model_name: str) -> None:
        self.source_model_name = source_model_name
        self.target_model_name = target_model_name
        super().__init__(
            f"No mappable data found between '{source_model_name}' and '{target_model_name}'."
        )


class ErrorReturningPartial(PyDaMapperException):
    """Raised if an unindentified error happens when returning partial data"""

    def __init__(self, source_model_name: str, target_model_name: str, error: Exception) -> None:
        self.source_model_name = source_model_name
        self.target_model_name = target_model_name
        super().__init__(
            f"Cannot return the partial data mapped from '{source_model_name}' "
            f"to '{target_model_name}' due to the error: {str(error)}."
        )


# This is not used
class InvalidModelTypeError(PyDaMapperException):
    """Raised when a field requires a specific model type but receives invalid type"""

    def __init__(self, field_path: str, expected_type: type, actual_type: type):
        self.field_path = field_path
        self.expected_type = expected_type
        self.actual_type = actual_type
        super().__init__(
            f"Field '{field_path}' requires model type {expected_type.__name__}, "
            f"but got {actual_type.__name__ if actual_type else 'None'}"
        )


class UnknownPathTypeException(PyDaMapperException):
    """Raised when a path type is not recognized on the DynamicPathManager class"""

    def __init__(self, path_type: str, available_paths: list[str]):
        self.path_type = path_type
        self.available_paths = available_paths
        super().__init__(f"Unknown path type: '{path_type}'. Available types: '{available_paths}'.")


class InvalidPathSegmentError(PyDaMapperException):
    """Raised when attempting invalid path segment operations on the DynamicPathManager class"""

    def __init__(self, path_type: str, segment: str):
        self.path_type = path_type
        self.segment = segment
        super().__init__(
            f"Path '{path_type}': Cannot add list index without preceding field segment: "
            f"(Segment: '{segment}'). List indices must follow a field segment."
        )


class ObjectNotJsonSerializable(PyDaMapperException):
    """Raised during serialization, if an object is not JSON serializable"""

    def __init__(self, object_type: str, error: Exception):
        self.object_type = object_type
        self.error = error
        super().__init__(
            f"Object of type '{object_type}' is not JSON serializable. Error: {str(error)}"
        )
