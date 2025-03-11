"""
pymapper.py
==============



"""

from typing import Optional, Sequence, Any
from pydantic import BaseModel, ValidationError

from .src.path_manager import DynamicPathManager
from .src.logger_config import logger
from .src.field_meta_data import FieldMetaData, get_field_meta_data
from .src.error_manager import ErrorManager, ErrorList
from .src.field_cache import FieldCache
from .src.field_matcher import FieldMatcher
from .src.exceptions import MappingError, NoMappableData, InvalidArguments
from .src.utils import partial_return
from .src.types import DataMapped, ModelType, PyMapperReturnType, MappedModelItem

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

    @property
    def errors(self) -> ErrorList:
        return self.error_manager.errors

    @property
    def cache(self) -> FieldCache:
        return self._cache

    def _start(self, source: BaseModel, target: ModelType) -> None:
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
        self, source: BaseModel, target: ModelType, serialize: bool = False
    ) -> PyMapperReturnType:
        """
        Maps source model instance to target model type
        """

        if not isinstance(source, BaseModel):
            raise InvalidArguments(source.__class__.__name__)
        elif not issubclass(target, BaseModel):
            raise InvalidArguments(source.__class__.__name__)

        self._start(source, target)

        try:
            mapped_data = self._map_model_fields(source, target)

            return self._handle_return(mapped_data, target, serialize)

        except Exception as e:
            raise MappingError(self._source_name, self._target_name, e)

    def _map_model_fields(self, source: BaseModel, target: ModelType) -> DataMapped:
        """Maps all fields from source to target model structure"""
        mapped: DataMapped = {}

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
                    elif not field_info.is_required():
                        mapped[field_name] = value
                    else:
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
        except Exception as error:
            self.error_manager.error_creating_field(error)

        return None

    def _handle_new_model(
        self, source: BaseModel, new_model_type: ModelType
    ) -> MappedModelItem:
        """Attempts to map a nested Pydantic model field"""
        target_path = self._path_manager.get_path("target")
        self._logger.debug("📦 Trying model field mapping for: %s", target_path)

        new_model_mapped: DataMapped = {}

        for new_model_field, new_model_info in new_model_type.model_fields.items():
            with self._path_manager.track_segment("target", new_model_field):
                try:
                    nested_meta_data = get_field_meta_data(
                        new_model_info, new_model_type.__name__, target_path
                    )
                    nested_value = self._map_field(source, nested_meta_data)

                    if nested_value is not None:
                        new_model_mapped[new_model_field] = nested_value
                    elif not new_model_info.is_required():
                        new_model_mapped[new_model_field] = nested_value
                    else:
                        self.error_manager.required_field(
                            target_path, self._source_name, nested_meta_data.parent_name
                        )

                except Exception as e:
                    self.error_manager.error_creating_field(e)

        # can I simplify this try block?
        # First check if there were validation errors in the level
        # and act accordingly
        if new_model_mapped:
            try:
                self._logger.debug("✅ New model created for: %s", target_path)
                return new_model_type(**new_model_mapped)
            except ValidationError:
                self.error_manager.new_model_partial(
                    target_path, new_model_type.__name__
                )
                return new_model_mapped
            except Exception as e:
                self.error_manager.error_creating_field(e)
                return None
        elif not new_model_mapped:
            self.error_manager.new_model_empty(target_path, new_model_type.__name__)

        return None

    def _handle_list_of_model(
        self, source: BaseModel, field_meta_data: FieldMetaData
    ) -> Optional[Sequence[MappedModelItem]]:
        """
        Attempts to map a List[PydanticModel] field

        Uses Sequence in the return instead of List to:
            - Allow covariance (e.g., accept List[SubModel] as Sequence[BaseModel])
            - Support both list and tuple return types
            - Enable lazy evaluation patterns
        """
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
        built_items = self._field_matcher.build_list_of_model(
            source, field_meta_data, self._handle_new_model
        )
        if built_items:
            return built_items

        return None

    def _handle_return(
        self,
        mapped_data: DataMapped,
        target: ModelType,
        serialize: bool = False,
    ) -> PyMapperReturnType:
        """
        Handles the return of the mapped data
        """

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
            return partial_return(mapped_data, serialize)

        # TODO: check for alias mismatches
        # Try to return the mapped data
        try:
            result = target(**mapped_data)
            self._logger.info("🎉 Data successfully mapped to '%s'.", self._target_name)
            return result
        except Exception as error:
            self._logger.error(
                "💥 Cannot create the '%s' model due to the error: %s."
                ">>> Returning the mapped data from '%s'.",
                self._target_name,
                error,
                self._source_name,
            )
            return partial_return(mapped_data, serialize)


pymapper = PyMapper()
map_models = pymapper.map_models
