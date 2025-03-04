from pydantic import BaseModel
from typing import Optional, Type, List, Any

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
        self.logger = logger
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
        target_path = self._path_manager.get_path(
            "target"
        )  # validar si es necesario o se cambia por el field meta data, el asunto es que este perderia contexto cada vez que agrego algo al path

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
                            field_meta_data.field_type,
                            value_matched,
                            type(value_matched),
                        )
                        self.logger.debug(
                            f"🔍 Source field: '{source_path}' matched with target field: '{target_path}'"
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

                elif (
                    nested_meta_data.is_collection_of_models
                ):  # modificar a lista de objetos
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
        instances = []
        with self._path_manager.track_segment("source", ""):
            self.search_instances(source, model_type, instances)
        return instances

    def search_instances(
        self, value: Any, model_type: Type[BaseModel], instances: list
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

    # def _build_list_of_model(
    #     self, source: BaseModel, field_meta_data: FieldMetaData
    # ) -> Optional[List[BaseModel]]:
    #     """Attempts to build list of models from scattered data"""
    #     list_of_models = []
    #     index = 0
    #     target_path = self._path_manager.get_path("target")
    #     self.logger.debug(f"📑 Trying to build list of models for: {target_path}")

    #     while index <= self._max_iter_list_new_model:
    #         if index == self._max_iter_list_new_model:
    #             self.logger.warning(
    #                 f"📑 Reached max iteration to build list of models for: {target_path}"
    #             )

    #         with self._path_manager.track_segment("target", f"[{index}]"):
    #             try:
    #                 model = self._handle_new_model(
    #                     source,
    #                     field_meta_data.model_type,
    #                 )

    #                 # The last model will be empty, because the index won't exists in the source.
    #                 # I have to remove the error created in the "_handle_new_model" method
    #                 if model is None:
    #                     if list_of_models:  # or index > 0, same thing
    #                         self._error_manager.last_available_index()
    #                     break

    #                 list_of_models.append(model)
    #                 index += 1

    #             except (
    #                 Exception
    #             ) as e:  # should't this be added to the mapping error list?
    #                 self.logger.debug(
    #                     f"⚠️ Stopped building list of models at index {index}: {str(e)}"
    #                 )
    #                 break

    #     if list_of_models:
    #         self.logger.debug(f"✅ List of models built for: {target_path}")
    #         return list_of_models
    #     return None
