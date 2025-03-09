class PyMapperException(Exception):
    """Base class for all exceptions raised by PyMapper"""

    pass


class MappingError(PyMapperException):
    """Exception raised when an unindentified error happens"""

    def __init__(
        self, source_model_name: str, target_model_name: str, error: Exception
    ):
        self.source_model_name = source_model_name
        self.target_model_name = target_model_name
        super().__init__(
            f"Mapping between '{source_model_name}' and '{target_model_name}' failed due to the error: {str(error)}."
        )


class InvalidArguments(PyMapperException):
    """Exception raised when invalid arguments are passed"""

    pass


class NoMappableData(PyMapperException):
    """Exception raised when there's no mappable data"""

    def __init__(self, source_model_name: str, target_model_name: str) -> None:
        self.source_model_name = source_model_name
        self.target_model_name = target_model_name
        super().__init__(
            f"No mappable data found between '{source_model_name}' and '{target_model_name}'."
        )


class ErrorReturningPartial(PyMapperException):
    """Exception raised if an unindentified error happens when returning partial data"""

    def __init__(
        self, source_model_name: str, target_model_name: str, error: Exception
    ) -> None:
        self.source_model_name = source_model_name
        self.target_model_name = target_model_name
        super().__init__(
            f"Cannot return the partial data mapped from '{source_model_name}' to '{target_model_name}' due to the error: {str(error)}."
        )


class InvalidModelTypeError(PyMapperException):
    """Raised when a field requires a specific model type but receives invalid type"""

    def __init__(self, field_path: str, expected_type: type, actual_type: type):
        super().__init__(
            f"Field '{field_path}' requires model type {expected_type.__name__}, "
            f"but got {actual_type.__name__ if actual_type else 'None'}"
        )
        self.field_path = field_path
        self.expected_type = expected_type
        self.actual_type = actual_type


class UnknownPathTypeException(PyMapperException):
    """Exception raised when a path type is not recognized"""

    def __init__(self, path_type: str, available_paths: list[str]):
        self.path_type = path_type
        self.available_paths = available_paths
        super().__init__(
            f"Unknown path type: '{path_type}'. Available types: '{available_paths}'."
        )


class InvalidPathSegmentError(PyMapperException):
    """Raised when attempting invalid path segment operations"""

    def __init__(self, path_type: str, segment: str):
        self.path_type = path_type
        self.segment = segment
        super().__init__(
            f"Path '{path_type}': Cannot add list index without preceding field segment: (Segment: '{segment}')."
            "List indices must follow a field segment."
        )


class FieldMetaDataException(PyMapperException):
    """Exception raised when there's an error in the FieldMetaData"""

    pass


class ErrorManagerException(PyMapperException):
    """Exception raised when there's an error in the ErrorManager"""

    pass
