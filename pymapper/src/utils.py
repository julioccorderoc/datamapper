"""
utils.py
========

This module provides utility functions for serializing data and handling partial returns in the data mapping process.
It includes functions to convert Pydantic models to JSON strings and to optionally serialize mapped data.

"""

from typing import Union, Any
from json import dumps
from pydantic import BaseModel

from .exceptions import ObjectNotJsonSerializable
from .types import DataMapped


def _serializer(object: Any) -> Union[DataMapped, str]:
    """Serializes a Pydantic model to a JSON string"""
    try:
        if isinstance(object, BaseModel):
            return object.model_dump()  # Convert Pydantic model to dict
        else:
            return str(object)
    except Exception as error:
        raise ObjectNotJsonSerializable(object.__class__.__name__, error)


def partial_return(
    mapped_data: DataMapped, serialize: bool = False
) -> Union[DataMapped, str]:
    """Returns mapped data, optionally serialized to a JSON string.

    Args:
        mapped_data (DataMapped): The data to be returned, typically a dictionary of mapped values.
        serialize (bool, optional): Flag indicating whether to serialize the data to a JSON string. Defaults to False.

    Returns:
        Union[DataMapped, str]: The mapped data as a dictionary if serialize is False, or as a JSON string if serialize is True.
    """

    if serialize:
        return dumps(mapped_data, indent=4, default=_serializer)
    else:
        return mapped_data
