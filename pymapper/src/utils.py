"""
utils.py
==============



"""

from typing import Dict, Union, Any
from json import dumps
from pydantic import BaseModel

from .exceptions import ObjectNotJsonSerializable


def serializer(object: Any) -> Union[Dict[str, Any], str]:
    """Serializes a Pydantic model to a JSON string"""
    try:
        if isinstance(object, BaseModel):
            return object.model_dump()  # Convert Pydantic model to dict
        else:
            return str(object)
    except Exception as error:
        raise ObjectNotJsonSerializable(object.__class__.__name__, error)


def partial_return(
    mapped_data: Dict[str, Any], serialize: bool = False
) -> Union[Dict[str, Any], str]:
    """_summary_

    Args:
        mapped_data (Dict[str, Any]): _description_
        serialize (bool, optional): _description_. Defaults to False.

    Returns:
        Union[Dict[str, Any], str]: _description_
    """

    if serialize:
        serialized_data: str
        serialized_data = dumps(mapped_data, indent=4, default=serializer)
        return serialized_data
    else:
        return mapped_data
