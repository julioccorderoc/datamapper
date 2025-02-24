from dataclasses import dataclass
from typing import Any, Type, Optional
from pydantic import BaseModel
from typing_extensions import get_origin, get_args

@dataclass
class FieldMetaData:
    """
    Contains field's data.
    Used as an interface to facilitate the mapping process.
    """
    is_model: bool = False  # True if the field is a Pydantic model
    is_collection_of_models: bool = False  # True if the field is a collection (list, set, tuple) of Pydantic models
    is_required: bool = False  # True if the field is required
    field_type: Type = None  # The type of the field
    model_type: Optional[Type[BaseModel]] = None  # The type of the model (or the type of the elements in a collection of models)
    parent_name: str = ""  # The name of class that contains the field
    field_path: str = ""  # The path of the field within the model structure

def get_field_meta_data(field_info: Any, parent_name: str, field_path: str) -> FieldMetaData:
    """
    Analyzes a field's type and returns structured information.

    Args:
        field_info (Any): Field info object from pydantic containing annotation and metadata.
        parent_name (str): Name of class that contains the field.
        field_path (str): The path of the field within the model structure.

    Returns:
        FieldMetaData: Structured information about the field's type.
    """
    field_type = field_info.annotation
    origin = get_origin(field_type)
    args = get_args(field_type)

    # Determine if the field is a collection (list, set, tuple)
    is_collection = origin in (list, set, tuple)
    model_type = args[0] if is_collection and args else None

    # Determine if the field is a Pydantic model
    is_model = isinstance(field_type, type) and issubclass(field_type, BaseModel)

    # Determine if the field is a collection of Pydantic models
    is_collection_of_models = (is_collection and
                               model_type and
                               issubclass(model_type, BaseModel))

    if is_model:
        model_type = field_type

    # Determine if the field is required
    is_required = field_info.is_required()

    return FieldMetaData(is_model=is_model,
                         is_collection_of_models=is_collection_of_models,
                         is_required=is_required,
                         field_type=field_type,
                         model_type=model_type,
                         parent_name=parent_name,
                         field_path=field_path)
