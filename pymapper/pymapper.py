from typing import Type, Any, List, Optional, Dict, Union, Sequence
from pydantic import BaseModel, ValidationError

from .src.path_manager import DynamicPathManager
from .src.logger_config import logger
from .src.field_meta_data import FieldMetaData, get_field_meta_data
from .src.error_manager import ErrorManager
from .src.field_cache import FieldCache
from .src.field_matcher import FieldMatcher
from .src.exceptions import MappingError, NoMappableData

# TODO: add type aliases like ModelType = Type[BaseModel]
# TODO: add support for the return of a serialized dict
# TODO: add get_origin for precise validation


class PyMapper:
    """
    Maps data between Pydantic models
    """

    def __init__(self, match_by_alias: bool = True, max_iterations: int = 100):
        self._logger = logger
        self._cache = FieldCache()
        self._path_manager = DynamicPathManager()
        self.error_manager = ErrorManager(self._path_manager)
        self._match_by_alias = match_by_alias
        self._source_name: str = ""
        self._target_name: str = ""
        self._max_iter_list_new_model = (
            max_iterations  # Safety limit for list processing
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
        self._source_name = source.__class__.__name__
        self._target_name = target.__name__
        # self._max_iter_list_new_model
        self._cache.clear()
        self.error_manager.errors.clear()
        self._path_manager.clear()
        self._path_manager.create_path_type("source", self._source_name)
        self._path_manager.create_path_type("target", self._target_name)
        target.model_rebuild()  # TODO: protect from errors
        self._logger.info(
            "🚀 Starting mapping from '%s' to '%s'.",
            self._source_name,
            self._target_name,
        )

    def map_models(
        self, source: BaseModel, target: Type[BaseModel], serialize: bool = False
    ) -> Union[BaseModel, Dict[str, Any]]:
        """
        Maps source model instance to target model type
        """
        # TODO: validate models

        self._start(source, target)

        try:
            mapped_data = self._map_model_fields(source, target)

            return self._handle_return(mapped_data, target, serialize)

        except Exception as e:
            raise MappingError(self._source_name, self._target_name, e)

    def _map_model_fields(
        self, source: BaseModel, target: Type[BaseModel]
    ) -> Dict[str, Any]:
        """Maps all fields from source to target model structure"""
        mapped: dict[str, Any] = {}

        for field_name, field_info in target.model_fields.items():
            with self._path_manager.track_segment("target", field_name):
                try:
                    target_path = self._path_manager.get_path("target")

                    # try:
                    field_meta_data = get_field_meta_data(
                        field_info, self._target_name, target_path
                    )
                    value = self._map_field(source, field_meta_data)
                    # except InvalidModelTypeError as e:
                    #     self.error_manager.type_error(e)
                    #     value = None

                    if value is not None:
                        mapped[field_name] = value
                    elif field_info.is_required():
                        self.error_manager.required_field(
                            target_path, self._source_name, field_meta_data.parent_name
                        )

                except Exception as e:
                    self.error_manager.error_creating_field(e)

        return mapped

    def _map_field(self, source: BaseModel, field_meta_data: FieldMetaData) -> Any:
        """Maps a single field through different possible cases"""
        target_path = self._path_manager.get_path("target")
        self._logger.debug("⏳ Attempting to map field: %s", target_path)

        # Try simple field mapping first
        value = self._handle_simple_field(source, field_meta_data)
        if value is not None:
            return value

        # Try creating a new model from scattered data
        if field_meta_data.is_model:
            value = self._handle_new_model(source, field_meta_data.model_type_safe)
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
                self._logger.debug(
                    "✅ Simple field mapping successful for: %s", target_path
                )
                return value
        except Exception as e:  # should't this be added to the mapping error list?
            self.error_manager.error_creating_field(e)

        return None

    def _handle_new_model(
        self, source: BaseModel, new_model_type: Type[BaseModel]
    ) -> Union[BaseModel, dict[str, Any], None]:
        """Attempts to map a nested Pydantic model field"""
        target_path = self._path_manager.get_path("target")
        self._logger.debug("📦 Trying model field mapping for: %s", target_path)

        nested_data: dict[str, Any] = {}

        for nested_field, nested_info in new_model_type.model_fields.items():
            with self._path_manager.track_segment("target", nested_field):
                try:
                    # try:
                    nested_meta_data = get_field_meta_data(
                        nested_info, new_model_type.__name__, target_path
                    )
                    nested_value = self._map_field(source, nested_meta_data)
                    # except InvalidModelTypeError as e:
                    #     self.error_manager.type_error(e)
                    #     nested_value = None

                    if nested_value is not None:
                        nested_data[nested_field] = nested_value
                    elif nested_info.is_required():
                        self.error_manager.required_field(
                            target_path, self._source_name, nested_meta_data.parent_name
                        )

                except Exception as e:
                    self.error_manager.error_creating_field(e)

        if nested_data:  # can I simplify this try block? First check if there were validation errors in the level and act accordingly
            try:
                self._logger.debug("✅ New model created for: %s", target_path)
                return new_model_type(**nested_data)
            except ValidationError:
                self.error_manager.new_model_partial(
                    target_path, new_model_type.__name__
                )
                return nested_data
            except Exception as e:
                self.error_manager.error_creating_field(e)
                return None
        elif not nested_data:
            self.error_manager.new_model_empty(target_path, new_model_type.__name__)

        return None

    # Using Sequence (not List) for covariance: allows List[BaseModel] to be
    # assigned to Sequence[Union[BaseModel, Dict]], maintaining type safety
    # for read operations while allowing flexibility in return types
    def _handle_list_of_model(
        self, source: BaseModel, field_meta_data: FieldMetaData
    ) -> Optional[Sequence[Union[BaseModel, Dict[str, Any]]]]:
        """Attempts to map a List[PydanticModel] field"""
        target_path = self._path_manager.get_path("target")
        self._logger.debug("📑 Trying list field mapping for: %s", target_path)

        # Try to find direct instances first
        list_of_models = self._field_matcher.find_model_instances(
            source, field_meta_data.model_type_safe
        )
        if list_of_models:
            self._logger.debug("✅ List of direct instances found for: %s", target_path)
            return list_of_models

        # Try to build instances from scattered data
        built_items = self._build_list_of_model(source, field_meta_data)
        if built_items:
            return built_items

        return None

    def _build_list_of_model(
        self, source: BaseModel, field_meta_data: FieldMetaData
    ) -> Optional[List[Union[BaseModel, Dict[str, Any]]]]:
        """Attempts to build list of models from scattered data"""
        target_path = self._path_manager.get_path("target")
        self._logger.debug("📑 Trying to build list of models for: %s", target_path)

        list_of_models: List[Union[BaseModel, Dict[str, Any]]] = []
        index = 0

        while index <= self._max_iter_list_new_model:
            if index == self._max_iter_list_new_model:
                self._logger.warning(
                    "📑 Reached max iteration to build list of models for: %s",
                    target_path,
                )

            with self._path_manager.track_segment("target", f"[{index}]"):
                try:
                    model = self._handle_new_model(
                        source,
                        field_meta_data.model_type_safe,
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
                    self.error_manager.error_creating_field(e)
                    break

        if list_of_models:
            self._logger.debug("✅ List of models built for: %s", target_path)
            return list_of_models
        return None

    def _handle_return(
        self,
        mapped_data: Dict[str, Any],
        target: Type[BaseModel],
        serialize: bool = False,
    ) -> Union[BaseModel, Dict[str, Any]]:
        """
        Handles the return of the mapped data
        """
        # TODO: add support for the return of a serialized dict
        if serialize:
            pass

        # Check for no mapped data
        if not mapped_data:
            self._logger.critical(
                "No mappable data found between %s and %s",
                self._source_name,
                self._target_name,
            )
            raise NoMappableData(self._source_name, self._target_name)

        # Handle errors if any
        if self.error_manager.has_errors():
            self.error_manager.display(self._target_name)
            self._logger.error("⚠️ Returning partially mapped data.")
            return mapped_data

        # Try to return the mapped data
        # TODO: revisar antes si hay un mismatch con los aliases
        try:
            result = target(**mapped_data)
            self._logger.info("🎉 Successfully created target model instance")
            return result
        except Exception as error:
            self._logger.error(
                "💥 Cannot create the '%s' model due to the error: %s. >>> Returning the mapped data from '%s'.",
                self._target_name,
                error,
                self._source_name,
            )
            return mapped_data  # TODO: decide if it's better to return incomplete or incorrect data


pymapper = PyMapper()
map_models = pymapper.map_models
