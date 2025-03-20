"""
pydamapper.py
==============



"""

from typing import Optional, Sequence, Union, Any
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo

from .src.path_manager import path_manager
from .src.meta_field import FieldMetaData, get_field_meta_data
from .src.error_manager import ErrorList, error_manager
from .src.field_cache import FieldCache
from .src.field_matcher import FieldMatcher
from .src.exceptions import NoMappableData, InvalidArguments
from .src.utils import partial_return
from .src.types import DataMapped, ModelType, DataMapperReturnType, MappedModelItem

# TODO: add get_origin for precise validation
# TODO: add report of coverage of the source data in % in the cache


class PyDaMapper:
    """
    Maps data between Pydantic models
    """

    _source_name: str = ""
    _target_name: str = ""
    _max_iter_list_new_model: int = 100  # Safety limit for list processing
    # add a property for the serialized config
    _serialize: bool = False
    _sort_keys: bool = False
    _indent: int = 4

    def __init__(self) -> None:
        self._path_manager = path_manager
        self.error_manager = error_manager
        self._field_matcher = FieldMatcher(self._max_iter_list_new_model)

    @property
    def errors(self) -> ErrorList:
        return self.error_manager.errors

    @property
    def cache(self) -> FieldCache:
        return self._field_matcher._cache

    def config(
        self,
        max_iterations: int = 100,
        serialize: bool = False,
        sort_keys: bool = False,
        indent: int = 4,
    ) -> None:
        """Method to setup the mapper configuration:"""
        self._max_iter_list_new_model = max_iterations
        self._serialize = serialize
        self._sort_keys = sort_keys
        self._indent = indent

    def _get_config(self) -> None:
        return

    def _start(self, source: BaseModel, target: ModelType) -> None:
        """Starts the mapper"""
        self._source_name = source.__class__.__name__
        self._target_name = target.__name__
        self.cache.clear()
        self.errors.clear()
        self._path_manager.clear()
        self._path_manager.create_path_type("source", self._source_name)
        self._path_manager.create_path_type("target", self._target_name)
        target.model_rebuild()  # TODO: https://docs.pydantic.dev/latest/concepts/models/#rebuilding-model-schema

    def map_models(self, source: BaseModel, target: ModelType) -> DataMapperReturnType:
        """
        Maps source model instance to target model type
        """
        if not isinstance(source, BaseModel):
            raise InvalidArguments(source.__class__.__name__)
        elif not issubclass(target, BaseModel):
            raise InvalidArguments(source.__class__.__name__)

        self._start(source, target)
        mapped_data = self._map_model_fields(source, target)
        return self._handle_return(mapped_data, target)

    def _map_model_fields(self, source: BaseModel, target: ModelType) -> DataMapped:
        """Maps all fields from source to target model structure"""
        mapped: DataMapped = {}

        for field_name, field_info in target.model_fields.items():
            with self._path_manager.track_segment("target", field_name):
                field_meta_data = get_field_meta_data(field_name, self._target_name, field_info)
                value = self._map_field(source, field_meta_data)

                if value is not None or not field_info.is_required():
                    mapped[field_name] = value
                else:
                    self.error_manager.required_field(
                        self._source_name, field_meta_data.parent_name
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
            value = self._handle_new_model(source, field_meta_data.model_type)
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
        value = self._field_matcher.get_value(source, field_meta_data)
        return value

    def _handle_new_model(self, source: BaseModel, new_model_type: ModelType) -> MappedModelItem:
        """Attempts to map and construct a nested Pydantic model field."""
        new_model_mapped = self._build_new_model_mapped(source, new_model_type)

        if not new_model_mapped:
            self.error_manager.new_model_empty(new_model_type.__name__)
            return None

        return self._construct_model_instance(new_model_mapped, new_model_type)

    def _build_new_model_mapped(self, source: BaseModel, new_model_type: ModelType) -> DataMapped:
        """Builds a dictionary of mapped values for the new model fields."""
        mapped_data: DataMapped = {}

        for field_name, field_info in new_model_type.model_fields.items():
            with self._path_manager.track_segment("target", field_name):
                value = self._process_field(source, field_name, new_model_type.__name__, field_info)
                if value is not None:
                    mapped_data[field_name] = value

        return mapped_data

    def _process_field(
        self, source: BaseModel, field_name: str, model_type_name: str, field_info: FieldInfo
    ) -> Optional[Any]:
        """Processes and maps a single field, handling errors appropriately."""
        meta_data = get_field_meta_data(field_name, model_type_name, field_info)
        value = self._map_field(source, meta_data)

        if value is not None or not field_info.is_required():
            return value
        else:
            self.error_manager.required_field(self._source_name, meta_data.parent_name)
        return None

    def _construct_model_instance(
        self, mapped_data: DataMapped, model_type: ModelType
    ) -> Optional[Union[BaseModel, DataMapped]]:
        """Attempts to construct the model instance with proper error handling."""
        try:
            return model_type(**mapped_data)
        except ValidationError:
            self.error_manager.new_model_partial(model_type.__name__)
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
        list_of_models = self._field_matcher.find_model_instances(source, field_meta_data)
        if list_of_models:
            return list_of_models

        # Try to build instances from scattered data
        built_items = self._field_matcher.build_list_of_model(
            source, field_meta_data, self._handle_new_model
        )
        if built_items:
            return built_items

        return None

    def _handle_return(self, mapped_data: DataMapped, target: ModelType) -> DataMapperReturnType:
        """
        Handles the return of the mapped data
        """

        # Check for no mapped data
        if not mapped_data:
            raise NoMappableData(self._source_name, self._target_name)

        # Handle errors if any
        if self.error_manager.has_errors():
            self.error_manager.display(self._target_name)
            return partial_return(mapped_data, self._serialize)

        # TODO: check for alias mismatches
        # Try to return the mapped data
        result = target(**mapped_data)
        return result


pymapper: PyDaMapper = PyDaMapper()
map_models = pymapper.map_models
