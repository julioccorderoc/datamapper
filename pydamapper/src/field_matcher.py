"""
field_matcher.py
==============

"""

from typing import Any, Iterable, List, Optional

from pydantic import BaseModel

from .error_manager import error_manager
from .field_cache import matched_fields_cache
from .meta_field import FieldMetaData, get_field_meta_data
from .path_manager import path_manager
from .types import MappedModelItem, NewModelHandler


class FieldMatcher:
    def __init__(self, max_iteration: int = 100):
        self._cache = matched_fields_cache
        self._path_manager = path_manager
        self._error_manager = error_manager
        self._max_iter_list_new_model = max_iteration

    def get_value(
        self,
        model_with_value: BaseModel,
        field_meta_data: FieldMetaData,
    ) -> Any:
        """
        Searches for a field value, through nested structures if needed. Handles:
            > Direct match
            > Nested match (e.g., source.nested.field)
            > List match (e.g., source.list_field[0].nested_field)
            > Alias match (e.g., source.alias_field)
        """
        current_model = model_with_value  # simplificar esta linea para que sea una sola
        current_model = self.traverse_model(
            current_model, field_meta_data
        )  # cambiar nombre de variable a value

        return current_model

    def traverse_model(
        self,
        model_to_traverse: BaseModel,
        field_meta_data: FieldMetaData,
    ) -> Any:
        """Traverse model hierarchy to find matching field value."""

        # Direct match attempt
        direct_value = self._try_direct_match(model_to_traverse, field_meta_data)
        if direct_value is not None:
            return direct_value

        # Nested structure search
        return self._traverse_nested_structures(model_to_traverse, field_meta_data)

    def _try_direct_match(self, model: BaseModel, meta_data: FieldMetaData) -> Any:
        """Attempt to find value through direct field access."""
        field_path = self._path_manager.get_path("target")
        field_name = field_path.split(".")[-1]

        if not hasattr(model, field_name):
            return None

        # TODO: check this logic, there might be an issue with non required fields
        value = getattr(model, field_name)
        if value is None:
            return None  # TODO: Decide policy for None values - propagate or consider not found?

        with self._path_manager.track_segment("source", field_name):
            source_path = self._path_manager.get_path("source")
            if self._cache.is_cached(source_path):
                return None
            if self._is_valid_type(value, meta_data):
                return value
            return None

    def _traverse_nested_structures(self, model: BaseModel, meta_data: FieldMetaData) -> Any:
        """Coordinate search through nested models and collections."""
        for field_name, field_info in model.model_fields.items():
            with self._path_manager.track_segment("source", field_name):
                nested_value = getattr(model, field_name)
                nested_meta = get_field_meta_data(meta_data.field_name, field_name, field_info)

                if nested_meta.is_model:
                    found = self._handle_single_model(nested_value, meta_data)
                elif nested_meta.is_collection_of_models:
                    found = self._handle_model_collection(nested_value, meta_data)
                else:
                    continue

                if found is not None:
                    return found
        return None

    def _handle_single_model(self, model: BaseModel, meta_data: FieldMetaData) -> Any:
        """Process single nested model instance."""
        return self.get_value(model, meta_data)

    def _handle_model_collection(
        self, collection: Iterable[BaseModel], meta_data: FieldMetaData
    ) -> Any:
        """Process collection of models, searching each element."""
        for index, model in enumerate(collection):
            with self._path_manager.track_segment("source", f"[{index}]"):
                result = self.get_value(model, meta_data)
                if result is not None:
                    return result
        return None

    def _is_valid_type(
        self, value: Any, meta_data: FieldMetaData, is_instance: bool = False
    ) -> bool:
        """Centralize validation and caching logic."""
        source_path = self._path_manager.get_path("source")
        target_path = self._path_manager.get_path("target")
        is_valid: bool

        # This is for the building lists of existing models
        # The target_type will be a collection but we want
        # to validate against what's inside the collection
        if is_instance:
            type_to_validate = meta_data.model_type
        else:
            type_to_validate = meta_data.field_type

        # If not valid, it won't be mapped. It might be useful to return the value
        # but it has to be considered, depends on the use case
        is_valid = self._error_manager.is_valid_type(
            target_path, type_to_validate, value, type(value)
        )
        self._cache.add(source_path)
        return is_valid

    def find_model_instances(self, source: BaseModel, meta_data: FieldMetaData) -> List[BaseModel]:
        """Finds all instances of a specific model type in source data"""
        # FIXME: Not necessarily a list, the type of collection is defined by the target model
        instances: List[BaseModel] = []
        self._search_instances(source, meta_data, instances)
        return instances

    def _search_instances(
        self, value: Any, meta_data: FieldMetaData, instances: List[BaseModel]
    ) -> None:
        """Recursively searches for instances of model_type"""
        # TODO: avoid fields in the cache
        # source_path = self._path_manager.get_path("source")
        # if self._cache.is_cached(source_path):
        #     return

        if isinstance(value, meta_data.model_type):
            if self._is_valid_type(value, meta_data, True):
                instances.append(value)

        elif isinstance(value, BaseModel):
            for field in value.model_fields:  # TODO: just fields that haven't been checked
                with self._path_manager.track_segment("source", field):
                    self._search_instances(getattr(value, field), meta_data, instances)

        elif isinstance(value, (list, tuple, set)):
            for index, item in enumerate(value):  # TODO: just fields that haven't been checked
                with self._path_manager.track_segment("source", f"[{index}]"):
                    with self._path_manager.track_segment("target", f"[{index}]"):
                        self._search_instances(item, meta_data, instances)

    def build_list_of_model(
        self,
        source: BaseModel,
        field_meta_data: FieldMetaData,
        handle_new_model: NewModelHandler,
    ) -> Optional[List[MappedModelItem]]:
        """Attempts to build list of models from scattered data"""

        list_of_models: List[MappedModelItem] = []
        index = 0

        while index <= self._max_iter_list_new_model:
            if index == self._max_iter_list_new_model:
                # TODO: handle this with error manager
                pass

            with self._path_manager.track_segment("target", f"[{index}]"):
                model = handle_new_model(
                    source,
                    field_meta_data.model_type,
                )

                # Prevented error when no data for next model (empty last).
                if model is None:
                    if list_of_models:  # or index > 0, same thing
                        self._error_manager.last_available_index()
                    break

                list_of_models.append(model)
                index += 1

        if list_of_models:
            return list_of_models
        return None
