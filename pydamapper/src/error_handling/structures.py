from dataclasses import dataclass
from enum import Enum


class ErrorType(Enum):
    """Enumeration of possible mapping errors"""

    VALIDATION = "Attemp to match a value with the wrong type"
    REQUIRED_FIELD = "Required field not found in source data"
    PARTIAL_RETURN = "The new model was partially created"
    EMPTY_MODEL = "Non of the fields in the new model were found in the source data"
    FIELD_CREATION = "An unexpected error occurred while creating a field"
    TYPE_VALIDATION = "Field type validation failed"
    LIMIT_REACH = "The limit of new models for a list of new models was reached"


@dataclass
class ErrorDetails:
    """Represents the details of an error"""

    field_path: str
    error_type: ErrorType
    details: str
