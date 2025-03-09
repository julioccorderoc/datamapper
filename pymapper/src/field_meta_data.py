"""
field_meta_data.py
==================

This module provides functionality for analyzing and
storing metadata about fields in Pydantic models.

"""

from dataclasses import dataclass
from typing import Any, Type, Optional, Union
from pydantic import BaseModel
from typing_extensions import get_origin, get_args


@dataclass
class FieldMetaData:
    """
    Contains field's data.
    Used as an interface to facilitate the mapping process.
    """

    is_model: bool = False
    is_collection_of_models: bool = False
    is_required: bool = False
    field_type: Optional[Type[Any]] = None
    model_type: Optional[Type[BaseModel]] = None
    parent_name: str = ""
    field_path: str = ""

    # model_type_safe: Provides type-safe access to model_type
    # Use after verifying is_model/is_collection_of_models to satisfy mypy
    @property
    def model_type_safe(self) -> Type[BaseModel]:
        """
        Returns model_type when it's guaranteed to be a valid BaseModel type.
        Should only be called after checking is_model or is_collection_of_models.

        Raises ValueError if model_type is None to catch runtime errors.
        """
        # Ensures model_type exists at runtime
        if self.model_type is None:
            raise ValueError(f"model_type is None for field {self.field_path}")
        return self.model_type

    # field_type_safe: Non-optional accessor that ensures type safety
    # Use when passing to functions requiring a definite type object
    @property
    def field_type_safe(self) -> Type[Any]:
        """
        Returns field_type when it's guaranteed to be a valid type.
        Raises ValueError if field_type is None to catch runtime errors.
        """
        if self.field_type is None:
            raise ValueError(f"field_type is None for field {self.field_path}")
        return self.field_type


def get_field_meta_data(
    field_info: Any, parent_name: str, field_path: str
) -> FieldMetaData:
    """
    Analyzes a field's type and returns structured information.

    Args:
        field_info (Any): Field info object from pydantic containing annotation and metadata.
        parent_name (str): Name of class that contains the field.
        field_path (str): The path of the field within the model structure.

    Returns:
        FieldMetaData: Structured information about the field's type.
    """
    # Extract the base type from Optional fields
    field_type = field_info.annotation
    origin = get_origin(field_type)
    args = get_args(field_type)

    # Handle Optional types (which are represented as Union[Type, None])
    if origin is Union and type(None) in args:
        field_type = next(arg for arg in args if arg is not type(None))
        # Re-analyze the extracted type
        origin = get_origin(field_type)
        args = get_args(field_type)

    # Determine if the field is a collection (list, set, tuple)
    is_collection = origin in (list, set, tuple)

    # Extract model_type from collections
    model_type = None
    if is_collection and args:
        potential_model_type = args[0]
        # Only set model_type if it's a BaseModel subclass
        if isinstance(potential_model_type, type) and issubclass(
            potential_model_type, BaseModel
        ):
            model_type = potential_model_type

    # Update model type checks with explicit type guards
    is_model = False
    if isinstance(field_type, type) and issubclass(field_type, BaseModel):
        model_type = field_type
        is_model = True

    # Determine if the field is a collection of Pydantic models
    is_collection_of_models = False
    if (
        is_collection
        and args
        and isinstance(args[0], type)
        and issubclass(args[0], BaseModel)
    ):
        model_type = args[0]
        is_collection_of_models = True

    # Handles potential non-Pydantic field info objects
    try:
        is_required = field_info.is_required()
    except AttributeError:
        is_required = False

    return FieldMetaData(
        is_model=is_model,
        is_collection_of_models=is_collection_of_models,
        is_required=is_required,
        field_type=field_type,
        model_type=model_type,
        parent_name=parent_name,
        field_path=field_path,
    )
