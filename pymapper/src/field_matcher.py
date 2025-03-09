from typing import Type, List, Any  # , Optional
from pydantic import BaseModel

from .error_manager import ErrorManager
from .field_cache import FieldCache
from .field_meta_data import FieldMetaData, get_field_meta_data
from .path_manager import DynamicPathManager
from .logger_config import logger


class FieldMatcher:
    def __init__(
        self,
        path_manager: DynamicPathManager,
        error_manager: ErrorManager,
        cache: FieldCache,
        match_by_alias: bool = True,
        max_iteration: int = 100,
    ):
        self._logger = logger
        self._max_iter_list_new_model = max_iteration
        self._match_by_alias = match_by_alias
        self._path_manager = path_manager
        self._error_manager = error_manager
        self._cache = cache

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
        model_to_traverse: Any,  # Should this be a BaseModel?
        field_to_match: str,
        field_meta_data: FieldMetaData,
    ) -> Any:
        target_path = self._path_manager.get_path("target")
        # validar si es necesario o se cambia por el field meta data, el asunto es que este perderia contexto cada vez que agrego algo al path

        if hasattr(model_to_traverse, field_to_match):
            value_matched = getattr(
                model_to_traverse, field_to_match
            )  # TODO: try block to avoid unexpected exceptions
            if value_matched is not None:
                with self._path_manager.track_segment("source", field_to_match):
                    source_path = self._path_manager.get_path("source")
                    if not self._cache.is_cached(source_path):
                        self._error_manager.validate_type(
                            target_path,
                            field_meta_data.field_type_safe,
                            value_matched,
                            type(value_matched),
                        )
                        self._logger.debug(
                            "🔍 Source field: '%s' matched with target field: '%s'",
                            source_path,
                            target_path,
                        )
                        self._cache.add(source_path)
                        return value_matched
                    # Should I handle the case when it's in the cache?
            # Should I handle the case when the value is None?

        # Try searching nested structures
        for nested_name, nested_info in model_to_traverse.model_fields.items():
            with self._path_manager.track_segment("source", nested_name):
                value = getattr(model_to_traverse, nested_name)
                nested_meta_data = get_field_meta_data(
                    nested_info, nested_name, target_path
                )

                if nested_meta_data.is_model:
                    nested_value = self.get_value(
                        value, field_to_match, field_meta_data
                    )
                    if nested_value is not None:
                        return nested_value

                elif nested_meta_data.is_collection_of_models:
                    for index, model_in_list in enumerate(value):
                        with self._path_manager.track_segment("source", f"[{index}]"):
                            nested_value = self.get_value(
                                model_in_list, field_to_match, field_meta_data
                            )
                            if nested_value is not None:
                                return nested_value
        return None

    def find_model_instances(
        self, source: BaseModel, model_type: Type[BaseModel]
    ) -> List[BaseModel]:
        """Finds all instances of a specific model type in source data"""
        instances: List[BaseModel] = []
        with self._path_manager.track_segment("source", ""):
            self.search_instances(source, model_type, instances)
        return instances

    def search_instances(
        self, value: Any, model_type: Type[BaseModel], instances: List[BaseModel]
    ) -> None:
        """Recursively searches for instances of model_type"""
        if isinstance(value, model_type):
            instances.append(value)

        elif isinstance(value, BaseModel):
            for field in value.model_fields:
                with self._path_manager.track_segment("source", field):
                    self.search_instances(getattr(value, field), model_type, instances)

        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                with self._path_manager.track_segment("source", f"[{index}]"):
                    self.search_instances(item, model_type, instances)

    # # TODO: use a callable to pass the build new model method
    # def _build_list_of_model(
