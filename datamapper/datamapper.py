"""
datamapper.py
==============



"""

from typing import Optional, Sequence, Union, Any
from pydantic import BaseModel, ValidationError

from .src.path_manager import DynamicPathManager
from .src.logger_config import logger
from .src.field_meta_data import FieldMetaData, get_field_meta_data
from .src.error_manager import ErrorManager, ErrorList
from .src.field_cache import FieldCache
from .src.field_matcher import FieldMatcher
from .src.exceptions import NoMappableData, InvalidArguments
from .src.utils import partial_return
from .src.types import DataMapped, ModelType, DataMapperReturnType, MappedModelItem

# TODO: add get_origin for precise validation
# TODO: add report of coverage of the source data in %


class DataMapper:
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
        self._max_iter_list_new_model = max_iterations  # Safety limit for list processing
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

    def config(self) -> None:
        """Method to setup the mapper configuration:"""
        pass

    def map_models(
        self, source: BaseModel, target: ModelType, serialize: bool = False
    ) -> DataMapperReturnType:
        """
        Maps source model instance to target model type
        """
        if not isinstance(source, BaseModel):
            raise InvalidArguments(source.__class__.__name__)
        elif not issubclass(target, BaseModel):
            raise InvalidArguments(source.__class__.__name__)

        self._start(source, target)
        mapped_data = self._map_model_fields(source, target)
        return self._handle_return(mapped_data, target, serialize)

    def _map_model_fields(self, source: BaseModel, target: ModelType) -> DataMapped:
        """Maps all fields from source to target model structure"""
        mapped: DataMapped = {}

        for field_name, field_info in target.model_fields.items():
            with self._path_manager.track_segment("target", field_name):
                target_path = self._path_manager.get_path("target")

                field_meta_data = get_field_meta_data(field_info, self._target_name, target_path)
                value = self._map_field(source, field_meta_data)

                if value is not None or not field_info.is_required():
                    mapped[field_name] = value
                else:
                    self.error_manager.required_field(
                        target_path, self._source_name, field_meta_data.parent_name
                    )

        return mapped

    def _map_field(self, source: BaseModel, field_meta_data: FieldMetaData) -> Any:
        """Maps a single field through different possible cases"""

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

    def _handle_simple_field(self, source: BaseModel, field_meta_data: FieldMetaData) -> Any:
        """Attempts to map a simple field directly"""
        target_path = self._path_manager.get_path("target")
        value = self._field_matcher.get_value(source, target_path, field_meta_data)
        return value

    def _handle_new_model(self, source: BaseModel, new_model_type: ModelType) -> MappedModelItem:
        """Attempts to map and construct a nested Pydantic model field."""
        target_path = self._path_manager.get_path("target")

        new_model_mapped = self._build_new_model_mapped(source, new_model_type, target_path)

        if not new_model_mapped:
            self.error_manager.new_model_empty(target_path, new_model_type.__name__)
            return None

        return self._construct_model_instance(new_model_mapped, new_model_type, target_path)

    def _build_new_model_mapped(
        self, source: BaseModel, new_model_type: ModelType, target_path: str
    ) -> DataMapped:
        """Builds a dictionary of mapped values for the new model fields."""
        mapped_data: DataMapped = {}

        for field_name, field_info in new_model_type.model_fields.items():
            with self._path_manager.track_segment("target", field_name):
                value = self._process_field(
                    source, field_info, new_model_type.__name__, target_path
                )
                if value is not None:
                    mapped_data[field_name] = value

        return mapped_data

    def _process_field(
        self,
        source: BaseModel,
        field_info: Any,
        model_type_name: str,
        target_path: str,
    ) -> Optional[Any]:
        """Processes and maps a single field, handling errors appropriately."""
        meta_data = get_field_meta_data(field_info, model_type_name, target_path)
        value = self._map_field(source, meta_data)

        if value is not None or not field_info.is_required():
            return value
        else:
            self.error_manager.required_field(target_path, self._source_name, meta_data.parent_name)
        return None

    def _construct_model_instance(
        self, mapped_data: DataMapped, model_type: ModelType, target_path: str
    ) -> Optional[Union[BaseModel, DataMapped]]:
        """Attempts to construct the model instance with proper error handling."""
        try:
            return model_type(**mapped_data)
        except ValidationError:
            self.error_manager.new_model_partial(target_path, model_type.__name__)
            return mapped_data

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

        # Try to find direct instances first
        list_of_models = self._field_matcher.find_model_instances(
            source, field_meta_data.model_type_safe
        )
        if list_of_models:
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
    ) -> DataMapperReturnType:
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
        result = target(**mapped_data)
        return result


datamapper = DataMapper()
map_models = datamapper.map_models
