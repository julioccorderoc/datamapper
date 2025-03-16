"""
field_matcher.py
==============

"""

from typing import Type, List, Optional, Iterable, Any
from pydantic import BaseModel


from .field_cache import FieldCache
from .path_manager import path_manager
from .error_manager import error_manager
from .meta_field import FieldMetaData, get_field_meta_data
from .types import NewModelHandler, MappedModelItem


class FieldMatcher:
    def __init__(self, max_iteration: int = 100):
        self._cache = FieldCache()
        self._path_manager = path_manager
        self._error_manager = error_manager
        self._max_iter_list_new_model = max_iteration

    def get_value(
        self,
        model_with_value: BaseModel,
        field_path: str,  # esto se puede simplificar, no se necesita el path_tracker, solo el nombre del campo
        field_meta_data: FieldMetaData,
    ) -> Any:
        """
        Searches for a field value, through nested structures if needed. Handles:
            > Direct match
            > Nested match (e.g., source.nested.field)
            > List match (e.g., source.list_field[0].nested_field)
            > Alias match (e.g., source.alias_field)
        """
        # field_path = self._path_manager.get_path("target")
        path_part = field_path.split(".")[-1]
        current_model = model_with_value  # simplificar esta linea para que sea una sola
        current_model = self.traverse_model(
            current_model, path_part, field_meta_data
        )  # cambiar nombre de variable a value

        return current_model

    def traverse_model(
        self,
        model_to_traverse: BaseModel,
        field_to_match: str,
        field_meta_data: FieldMetaData,
    ) -> Any:
        """Traverse model hierarchy to find matching field value."""

        # Direct match attempt
        direct_value = self._try_direct_match(model_to_traverse, field_to_match, field_meta_data)
        if direct_value is not None:
            return direct_value

        # Nested structure search
        return self._traverse_nested_structures(model_to_traverse, field_to_match, field_meta_data)

    def _try_direct_match(self, model: BaseModel, field_name: str, meta_data: FieldMetaData) -> Any:
        """Attempt to find value through direct field access."""
        if not hasattr(model, field_name):
            return None

        value = getattr(model, field_name)
        if value is None:
            return None  # TODO: Decide policy for None values - propagate or consider not found?

        with self._path_manager.track_segment("source", field_name):
            source_path = self._path_manager.get_path("source")
            if self._cache.is_cached(source_path):
                return None

            self._validate_and_cache(value, meta_data, source_path)
            return value

    def _traverse_nested_structures(
        self, model: BaseModel, field_to_match: str, meta_data: FieldMetaData
    ) -> Any:
        """Coordinate search through nested models and collections."""
        target_path = self._path_manager.get_path("target")
        for field_name, field_info in model.model_fields.items():
            with self._path_manager.track_segment("source", field_name):
                nested_value = getattr(model, field_name)
                nested_meta = get_field_meta_data(field_info, field_name, target_path)

                if nested_meta.is_model:
                    found = self._handle_single_model(nested_value, field_to_match, meta_data)
                elif nested_meta.is_collection_of_models:
                    found = self._handle_model_collection(nested_value, field_to_match, meta_data)
                else:
                    continue

                if found is not None:
                    return found
        return None

    def _handle_single_model(
        self, model: BaseModel, target_field: str, meta_data: FieldMetaData
    ) -> Any:
        """Process single nested model instance."""
        return self.get_value(model, target_field, meta_data)

    def _handle_model_collection(
        self, collection: Iterable[BaseModel], target_field: str, meta_data: FieldMetaData
    ) -> Any:
        """Process collection of models, searching each element."""
        for index, model in enumerate(collection):
            with self._path_manager.track_segment("source", f"[{index}]"):
                result = self.get_value(model, target_field, meta_data)
                if result is not None:
                    return result
        return None

    def _validate_and_cache(self, value: Any, meta_data: FieldMetaData, source_path: str) -> None:
        """Centralize validation and caching logic."""
        target_path = self._path_manager.get_path("target")
        self._error_manager.validate_type(
            target_path, meta_data.field_type_safe, value, type(value)
        )
        self._cache.add(source_path)

    def find_model_instances(
        self, source: BaseModel, model_type: Type[BaseModel]
    ) -> List[BaseModel]:
        """Finds all instances of a specific model type in source data"""
        instances: List[BaseModel] = []
        with self._path_manager.track_segment("source", ""):
            self._search_instances(source, model_type, instances)
        return instances

    def _search_instances(
        self, value: Any, model_type: Type[BaseModel], instances: List[BaseModel]
    ) -> None:
        """Recursively searches for instances of model_type"""
        if isinstance(value, model_type):
            instances.append(value)

        elif isinstance(value, BaseModel):
            for field in value.model_fields:
                with self._path_manager.track_segment("source", field):
                    self._search_instances(getattr(value, field), model_type, instances)

        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                with self._path_manager.track_segment("source", f"[{index}]"):
                    self._search_instances(item, model_type, instances)

    def build_list_of_model(
        self,
        source: BaseModel,
        field_meta_data: FieldMetaData,
        new_model_handler: NewModelHandler,
    ) -> Optional[List[MappedModelItem]]:
        """Attempts to build list of models from scattered data"""

        list_of_models: List[MappedModelItem] = []
        index = 0

        while index <= self._max_iter_list_new_model:
            if index == self._max_iter_list_new_model:
                # handle this with error manager
                pass

            with self._path_manager.track_segment("target", f"[{index}]"):
                model = new_model_handler(
                    source,
                    field_meta_data.model_type_safe,
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
