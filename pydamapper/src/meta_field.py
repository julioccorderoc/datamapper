"""
meta_field.py
==================

This module provides functionality for analyzing and
storing metadata about Pydantic model fields.
"""

from dataclasses import asdict, dataclass
from typing import Any, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from .types import CollectionTypes, ModelType


@dataclass
class _BaseMetaData:
    """Contains the results of the type analysis"""

    is_model: bool
    model_type: ModelType  # Optional[ModelType]
    is_collection_of_models: bool
    collection_type: Optional[Type[Any]]
    collection_depth: int


@dataclass
class FieldMetaData(_BaseMetaData):
    """
    Contains metadata about a field in a Pydantic model.

    Attributes:
        field_name: Name of the field
        field_type: The Python type of the field
        parent_name: Name of the class that contains this field
        is_required: Whether the field is required in the model
        is_model: Whether the field type is '**just**' a Pydantic model
        model_type: The model class | **Type safe only if used after is_model=True**
        is_collection_of_models: Whether the field contains a collection of Pydantic models
        collection_type: the type of the collection, if any
        collection_depth: How deeply nested the collection is (0 = not a collection)
    """

    field_name: str
    field_type: Type[Any]
    parent_name: str
    is_required: bool


def get_field_meta_data(field_name: str, parent_name: str, field_info: FieldInfo) -> FieldMetaData:
    """
    Analyzes a field's type and returns structured metadata information.

    Args:
        field_name: Name of the field
        parent_name: Name of class that contains the field
        field_info: Pydantic V2 FieldInfo object containing annotation and metadata

    Returns:
        FieldMetaData: Structured information about the field's type
    """
    field_type = _extract_from_optional(field_info.annotation)
    type_analysis = _analyze_type_structure(field_type)

    field_meta = FieldMetaData(
        field_name=field_name,
        field_type=field_type,
        parent_name=parent_name,
        is_required=field_info.is_required(),
        **asdict(type_analysis),
    )

    return field_meta


def _extract_from_optional(type_annotation: Any) -> Any:
    """Extracts the core type from Optional/Union[..., None] annotations.

    Why this exists: Optional[T] is syntax sugar for Union[T, None]. This unwraps
    that structure while preserving other Union types unchanged.
    """
    # Exit early for non-Union types to avoid unnecessary processing
    if get_origin(type_annotation) is not Union:
        return type_annotation

    # Unpack Union components and filter out None type
    args = get_args(type_annotation)
    non_none_types = []

    for arg in args:
        # Skip None type checks - we want actual data types
        if arg is type(None):
            continue
        non_none_types.append(arg)

    # Decision logic with clear exit points
    if not non_none_types:
        # Edge case: Union[None, None] - return original
        return type_annotation

    if len(non_none_types) == 1:
        # Ideal Optional case: Union[Something, None] → return Something
        return non_none_types[0]

    # Preserve original Union if multiple non-None types exist
    # This prevents losing type information in complex cases
    return type_annotation


def _analyze_type_structure(field_type: Any) -> _BaseMetaData:
    # Default values for non-model types
    is_model = False
    model_type: ModelType = BaseModel  # Use BaseModel as sentinel
    is_collection_of_models = False
    collection_depth = 0
    collection_type = None

    # Direct Pydantic model case
    if isinstance(field_type, type) and issubclass(field_type, BaseModel):
        is_model = True
        model_type = field_type
    else:
        origin = get_origin(field_type)
        args = get_args(field_type)

        # Handle collection types
        if origin in CollectionTypes and args:
            inner_analysis = _analyze_type_structure(args[0])

            is_collection_of_models = (
                inner_analysis.is_model or inner_analysis.is_collection_of_models
            )
            model_type = inner_analysis.model_type
            collection_depth = 1 + inner_analysis.collection_depth
            collection_type = origin

            # Collections can never be direct models
            is_model = False

    return _BaseMetaData(
        is_model=is_model,
        model_type=model_type,
        is_collection_of_models=is_collection_of_models,
        collection_depth=collection_depth,
        collection_type=collection_type,
    )
