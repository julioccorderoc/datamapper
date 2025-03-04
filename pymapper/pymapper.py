from pydantic import BaseModel, ValidationError
from typing import Type, Any, List, Optional, Dict, Union

from .src.path_manager import DynamicPathManager
from .src.logger_config import logger
from .src.field_meta_data import FieldMetaData, get_field_meta_data
from .src.error_manager import ErrorManager
from .src.field_cache import FieldCache
from .src.field_matcher import FieldMatcher


class PyMapper:
    """Maps data between Pydantic models"""

    def __init__(self, match_by_alias: bool = True, max_iter_list_new_model: int = 100):
        self.logger = logger
        self._cache = FieldCache()
        self._path_manager = DynamicPathManager()
        self.error_manager = ErrorManager(self._path_manager)
        self._match_by_alias = match_by_alias
        self._source_name: str = ""
        self._target_name: str = ""
        self._max_iter_list_new_model = (
            max_iter_list_new_model  # Safety limit for list processing
        )
        self._field_matcher = FieldMatcher(
            self._path_manager,
            self.error_manager,
            self._cache,
            self._match_by_alias,
            self._max_iter_list_new_model,
        )

    def _start(self, source: BaseModel, target: Type[BaseModel]) -> None:
        """Starts the mapper"""
        self._cache.clear()
        self.error_manager.errors.clear()
        self._path_manager.clear()
        self._path_manager = DynamicPathManager("source", "target")
        target.model_rebuild()  # TODO: protect from errors
        self._source_name = source.__class__.__name__
        self._target_name = target.__name__

    def map_models(
        self, source: BaseModel, target: Type[BaseModel]
    ) -> Union[BaseModel, Dict[str, Any]]:
        """Maps source model instance to target model type"""
        self._start(source, target)
        self.logger.debug(
            f"🚀 Starting mapping from {self._source_name} to {self._target_name}"
        )

        try:
            with self._path_manager.track_segment("source", self._source_name):
                with self._path_manager.track_segment("target", self._target_name):
                    mapped_data = self._map_model_fields(source, target)

            # If no data was mapped, raise an error
            if not mapped_data:
                self.logger.critical(
                    f"No mappable data found between {self._source_name} and {self._target_name}"
                )
                raise ValueError  # TODO: change this to a custom exception

            # If some data was mapped, display errors if any and return the partial data
            if self.error_manager.has_errors():
                try:
                    self.error_manager.display(self._target_name)
                    self.logger.error(
                        "⚠️ Returning partial data dictionary due to mapping errors"
                    )
                    return mapped_data
                except Exception as e:
                    self.logger.critical(f"💥 Partial mapping failed: {str(e)}")
                    raise  # TODO: change this to a custom exception

            # If no errors were found, create the target model instance
            try:
                result = target(
                    **mapped_data
                )  # TODO: revisar antes si hay un mismatch con los aliases
                self.logger.info("🎉 Successfully created target model instance")
                return result
            except Exception as e:
                self.logger.error(
                    f"💥 Could not create the '{self._target_name}' model: {str(e)}. Returning the mapped data."
                )
                return mapped_data  # TODO: decide if it's better to return incomplete or incorrect data

        except Exception as e:
            self.logger.critical(f"💥 Mapping failed: {str(e)}")
            raise  # TODO: change this to a custom exception

    def _map_model_fields(
        self, source: BaseModel, target: Type[BaseModel]
    ) -> Dict[str, Any]:
        """Maps all fields from source to target model structure"""
        mapped = {}

        for field_name, field_info in target.model_fields.items():
            with self._path_manager.track_segment("target", field_name):
                try:
                    target_path = self._path_manager.get_path("target")
                    field_meta_data = get_field_meta_data(
                        field_info, self._target_name, target_path
                    )

                    value = self._map_field(source, field_meta_data)

                    if value is not None:
                        mapped[field_name] = value
                    elif field_info.is_required():
                        self.error_manager.required_field(
                            target_path, self._source_name, field_meta_data.parent_name
                        )

                except Exception as e:
                    self.error_manager.error_creating_field()

        return mapped

    def _map_field(self, source: BaseModel, field_meta_data: FieldMetaData) -> Any:
        """Maps a single field through different possible cases"""
        target_path = self._path_manager.get_path("target")
        self.logger.debug(f"⏳ Attempting to map field: {target_path}")

        # Try simple field mapping first
        value = self._handle_simple_field(source, field_meta_data)
        if value is not None:
            return value

        # Try creating a new model from scattered data
        if field_meta_data.is_model:
            value = self._handle_new_model(source, field_meta_data.field_type)
            if value is not None:
                return value

        # Try mapping as Collention[PydanticModel]
        if field_meta_data.is_collection_of_models:
            value = self._handle_list_of_model(source, field_meta_data)
            if value is not None:
                return value

        return None

    def _handle_simple_field(
        self, source: BaseModel, field_meta_data: FieldMetaData
    ) -> Any:
        """Attempts to map a simple field directly"""
        target_path = self._path_manager.get_path("target")

        try:
            value = self._field_matcher.get_value(source, target_path, field_meta_data)
            if value is not None:
                self.logger.debug(
                    f"✅ Simple field mapping successful for: {target_path}"
                )
                return value
        except TypeError as e:  # should't this be added to the mapping error list?
            self.logger.debug(f"⚠️ Type conversion failed for {target_path}: {str(e)}")

        return None

    def _handle_new_model(
        self, source: BaseModel, new_model_type: Type[BaseModel]
    ) -> Optional[BaseModel]:
        """Attempts to map a nested Pydantic model field"""
        target_path = self._path_manager.get_path("target")
        self.logger.debug(f"📦 Trying model field mapping for: {target_path}")
        nested_data = {}

        for nested_field, nested_info in new_model_type.model_fields.items():
            with self._path_manager.track_segment("target", nested_field):
                try:
                    nested_meta_data = get_field_meta_data(
                        nested_info, new_model_type.__name__, target_path
                    )
                    nested_value = self._map_field(source, nested_meta_data)

                    if nested_value is not None:
                        nested_data[nested_field] = nested_value
                    elif nested_info.is_required():
                        self.error_manager.required_field(
                            target_path, self._source_name, nested_meta_data.parent_name
                        )

                except Exception as e:
                    self.error_manager.error_creating_field()

        if nested_data:  # can I simplify this try block? First check if there were validation errors in the level and act accordingly
            try:
                self.logger.debug(f"✅ New model created for: {target_path}")
                return new_model_type(**nested_data)
            except ValidationError:
                self.error_manager.new_model_partial(
                    target_path, new_model_type.__name__
                )
                return nested_data
            except Exception as e:
                self.error_manager.error_creating_model()
                return None
        # If there's not data, I have to remove the required field error to avoid redundancy
        elif not nested_data:
            self.error_manager.new_model_empty(target_path, new_model_type.__name__)

        return None

    def _handle_list_of_model(
        self, source: BaseModel, field_meta_data: FieldMetaData
    ) -> Optional[List[BaseModel]]:
        """Attempts to map a List[PydanticModel] field"""
        target_path = self._path_manager.get_path("target")
        self.logger.debug(f"📑 Trying list field mapping for: {target_path}")

        # Try to find direct instances first
        list_of_models = self._field_matcher.find_model_instances(
            source, field_meta_data.model_type
        )
        if list_of_models:
            self.logger.debug(f"✅ List of direct instances found for: {target_path}")
            return list_of_models

        # Try to build instances from scattered data
        built_items = self._build_list_of_model(source, field_meta_data)
        if built_items:
            return built_items

        return None

    def _build_list_of_model(
        self, source: BaseModel, field_meta_data: FieldMetaData
    ) -> Optional[List[BaseModel]]:
        """Attempts to build list of models from scattered data"""
        list_of_models = []
        index = 0
        target_path = self._path_manager.get_path("target")
        self.logger.debug(f"📑 Trying to build list of models for: {target_path}")

        while index <= self._max_iter_list_new_model:
            if index == self._max_iter_list_new_model:
                self.logger.warning(
                    f"📑 Reached max iteration to build list of models for: {target_path}"
                )

            with self._path_manager.track_segment("target", f"[{index}]"):
                try:
                    model = self._handle_new_model(
                        source,
                        field_meta_data.model_type,
                    )

                    # The last model will be empty, because the index won't exists in the source.
                    # I have to remove the error created in the "_handle_new_model" method
                    if model is None:
                        if list_of_models:  # or index > 0, same thing
                            self.error_manager.last_available_index()
                        break

                    list_of_models.append(model)
                    index += 1

                except (
                    Exception
                ) as e:  # should't this be added to the mapping error list?
                    self.logger.debug(
                        f"⚠️ Stopped building list of models at index {index}: {str(e)}"
                    )
                    break

        if list_of_models:
            self.logger.debug(f"✅ List of models built for: {target_path}")
            return list_of_models
        return None

    # def _get_value(
    #     self,
    #     model_with_value: BaseModel,
    #     field_path: str,  # esto se puede simplificar, no se necesita el path_tracker, solo el nombre del campo
    #     field_meta_data: FieldMetaData,
    # ) -> Any:
    #     """
    #     Searches for a field value, through nested structures if needed. Handles:
    #         > Direct match
    #         > Nested match (e.g., source.nested.field)
    #         > List match (e.g., source.list_field[0].nested_field)
    #         > Alias match (e.g., source.alias_field)
    #     """
    #     # field_path = self._path_manager.get_path("target")
    #     path_part = field_path.split(".")[-1]
    #     current_model = model_with_value  # simplificar esta linea para que sea una sola
    #     current_model = self._traverse_model(
    #         current_model, path_part, field_meta_data
    #     )  # cambiar nombre de variable a value

    #     return current_model

    # def _traverse_model(
    #     self,
    #     model_to_traverse: Any,  # Should this be a BaseModel?
    #     field_to_match: str,
    #     field_meta_data: FieldMetaData,
    # ) -> Any:
    #     target_path = self._path_manager.get_path(
    #         "target"
    #     )  # validar si es necesario o se cambia por el field meta data, el asunto es que este perderia contexto cada vez que agrego algo al path

    #     if hasattr(model_to_traverse, field_to_match):
    #         value_matched = getattr(
    #             model_to_traverse, field_to_match
    #         )  # TODO: try block to avoid unexpected exceptions
    #         if value_matched is not None:
    #             with self._path_manager.track_segment("source", field_to_match):
    #                 source_path = self._path_manager.get_path("source")
    #                 if not self._cache.is_cached(source_path):
    #                     self.error_manager.validate_type(
    #                         target_path,
    #                         field_meta_data.field_type,
    #                         value_matched,
    #                         type(value_matched),
    #                     )
    #                     self.logger.debug(
    #                         f"🔍 Source field: '{source_path}' matched with target field: '{target_path}'"
    #                     )
    #                     self._cache.add(source_path)
    #                     return value_matched
    #                 # Should I handle the case when it's in the cache?
    #         # Should I handle the case when the value is None?

    #     # Try searching nested structures
    #     for nested_name, nested_info in model_to_traverse.model_fields.items():
    #         with self._path_manager.track_segment("source", nested_name):
    #             value = getattr(model_to_traverse, nested_name)
    #             nested_meta_data = get_field_meta_data(
    #                 nested_info, nested_name, target_path
    #             )

    #             if nested_meta_data.is_model:
    #                 nested_value = self._get_value(
    #                     value, field_to_match, field_meta_data
    #                 )
    #                 if nested_value is not None:
    #                     return nested_value

    #             elif (
    #                 nested_meta_data.is_collection_of_models
    #             ):  # modificar a lista de objetos
    #                 for index, model_in_list in enumerate(value):
    #                     with self._path_manager.track_segment("source", f"[{index}]"):
    #                         nested_value = self._get_value(
    #                             model_in_list, field_to_match, field_meta_data
    #                         )
    #                         if nested_value is not None:
    #                             return nested_value
    #     return None

    # def _find_model_instances(
    #     self, source: BaseModel, model_type: Type[BaseModel]
    # ) -> List[BaseModel]:
    #     """Finds all instances of a specific model type in source data"""
    #     instances = []
    #     with self._path_manager.track_segment("source", ""):
    #         self._search_instances(source, model_type, instances)
    #     return instances

    # def _search_instances(
    #     self, value: Any, model_type: Type[BaseModel], instances: list
    # ) -> None:
    #     """Recursively searches for instances of model_type"""
    #     if isinstance(value, model_type):
    #         instances.append(value)

    #     elif isinstance(value, BaseModel):
    #         for field in value.model_fields:
    #             with self._path_manager.track_segment("source", field):
    #                 self._search_instances(getattr(value, field), model_type, instances)

    #     elif isinstance(value, (list, tuple)):
    #         for index, item in enumerate(value):
    #             with self._path_manager.track_segment("source", f"[{index}]"):
    #                 self._search_instances(item, model_type, instances)
