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


class InvalidArguments(MappingError):
    """Exception raised when invalid arguments are passed"""

    pass


class NoMappableData(MappingError):
    """Exception raised when there's no mappable data"""

    def __init__(self, source_model_name: str, target_model_name: str):
        self.source_model_name = source_model_name
        self.target_model_name = target_model_name
        super().__init__(
            f"No mappable data found between '{source_model_name}' and '{target_model_name}'."
        )


class ErrorReturningPartial(MappingError):
    """Exception raised if an unindentified error happens when returning partial data"""

    def __init__(
        self, source_model_name: str, target_model_name: str, error: Exception
    ):
        self.source_model_name = source_model_name
        self.target_model_name = target_model_name
        super().__init__(
            f"Cannot return the partial data mapped from '{source_model_name}' to '{target_model_name}' due to the error: {str(error)}."
        )


class DynamicPathManagerException(PyMapperException):
    """Exception raised when there's an error in the DynamicPathManager"""

    pass


class FieldMetaDataException(PyMapperException):
    """Exception raised when there's an error in the FieldMetaData"""

    pass


class ErrorManagerException(PyMapperException):
    """Exception raised when there's an error in the ErrorManager"""

    pass
