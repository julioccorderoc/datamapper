import pytest
from pymapper.pymapper import ModelMapper
from .sources import source_data
from .models import *

@pytest.fixture
def model_mapper():
    """Provides a fresh ModelMapper instance for each test."""
    return ModelMapper()

@pytest.fixture
def complete_mapping(model_mapper):
    """Provides the result of mapping the complete source data to TargetModelOrder."""
    return model_mapper.map_models(source_data, TargetModelOrder)