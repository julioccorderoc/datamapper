"""
types.py
==============

Central type definitions for Pydantic model mapping operations.

This module provides standardized type aliases to simplify complex type annotations
and ensure consistency across the data mapping package. All types are derived from
Python's standard typing module and Pydantic's BaseModel.

"""

from typing import Type, Callable, Union, Dict, List, Set, Tuple, Any
from pydantic import BaseModel


CollectionTypes = (list, set, tuple, List, Set, Tuple)
"""
Collection types supported by the mapper.
"""

DataMapped = Dict[str, Any]
"""
Represents raw mapped data in dictionary format before conversion to Pydantic models.
Typically used for intermediate data representation during mapping operations.
"""

ModelType = Type[BaseModel]
"""
Type alias for Pydantic model classes (not instances). Used for type hints where 
model classes are expected as parameters or return values.
"""

DataMapperReturnType = Union[BaseModel, DataMapped, str]
"""
Holds the return types of the main mapping method. Can be:
- Instantiated Pydantic model
- Raw dictionary of mapped data
- Serialized data (string)
"""

MappedModelItem = Union[BaseModel, DataMapped, None]
"""
Extended return type for model creation operations that might fail. Adds explicit 
None case for fields that could not be found/created.
"""

NewModelHandler = Callable[
    [BaseModel, ModelType],  # (source, model_type)
    MappedModelItem,
]
"""
Type signature for model instantiation handlers. Used to type-check factory methods
that create new model instances from source data.

Parameters:
- source: BaseModel containing original data
- model_type: Target Pydantic model class to instantiate

Returns:
- Instantiated model, raw dictionary, or None if creation fails
"""

PathEntryType = Dict[str, Union[str, List[str]]]
"""
Type alias representing a single entry in the path registry.

Each entry contains a 'model' (str) and 'segments' (list[str]) key.
"""

PathRegistryType = Dict[str, PathEntryType]
"""
Type alias representing the complete path registry.

The registry maps path identifiers (str) to PathEntryType instances.
"""
