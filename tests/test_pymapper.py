import pytest
from .models import *
from .sources import *
from .expected import *

# Add to the test a type checking
# Add case when it's acceptable to receive a None in a target field
#

class TestCompleteMapper:
    """Tests for full model mapping functionality."""
    
    def test_complete_mapping(self, model_mapper):
        """Verifies that the complete mapping matches the expected result."""
        complete_mapping = model_mapper.map_models(source_data, TargetModelOrder)
        assert complete_mapping == expected_target


class TestFieldMapping:
    """Tests for individual field mapping scenarios."""
    
    def test_simple_field_match(self, model_mapper):
        """Tests mapping of a simple field with direct name match."""
        simple_field = model_mapper.map_models(source_data, SimpleAddressTarget)
        assert simple_field == expected_simple_target
    
    def test_nested_field_match(self, model_mapper):
        """Tests mapping a field from a nested structure."""
        nested_field = model_mapper.map_models(source_data, MetaUserTarget)
        assert nested_field == expected_nested_target


class TestNestedModelCreation:
    """Tests for building new models from scattered fields."""
    
    def test_build_new_models_from_scattered_fields(self, model_mapper):
        """Tests creation of a new nested model from scattered fields."""
        new_model = model_mapper.map_models(source_data, NestedAddressTarget)
        assert new_model == expected_new_model


class TestListHandling:
    """Tests for handling lists of models."""
    
    def test_list_of_existing_models(self, model_mapper):
        """Tests mapping a list of models that exist in the source."""
        result = model_mapper.map_models(ListSource(), ListTarget)
        assert len(result.items) == len(ExpectedListTarget.items)
        assert result.items[0].name == ExpectedListTarget.items[0].name
        assert result.items[1].value == ExpectedListTarget.items[1].value
    
    def test_list_of_models_with_new_models(self, model_mapper):
        """Tests mapping a list with models that need to be created from fields."""
        result = model_mapper.map_models(ListSource(), NewListTarget)
        assert len(result.new_items) == len(ExpectedNewListTarget.new_items)
        assert result.new_items[0].item_name == ExpectedNewListTarget.new_items[0].item_name
        assert result.new_items[1].item_value == ExpectedNewListTarget.new_items[1].item_value
    
    # def test_list_in_root(self, model_mapper):
    #     """Tests mapping a root-level list."""
    #     result = model_mapper.map_models(ListSource(), RootListTarget)
    #     assert result.root_list == ExpectedRootListTarget.root_list


class TestErrorCases:
    """Tests for error handling scenarios."""
    
    def test_field_in_target_not_found_in_source(self, model_mapper):
        """Tests handling when a target field doesn't exist in the source."""
        # Should return a dict since it can't fully build the model
        result = model_mapper.map_models(ErrorSource(), ErrorTarget)
        assert isinstance(result, dict)
        assert "missing_field" not in result
        
    def test_field_found_with_different_type(self, model_mapper):
        """Tests handling when a field exists but has an incompatible type."""
        # Should return a dict with the fields it could map
        result = model_mapper.map_models(ErrorSource(), ErrorTarget)
        assert isinstance(result, dict)
        assert "wrong_type" not in result  # Can't convert str to int


class TestPartialReturns:
    """Tests for partial return scenarios."""
    
    @pytest.mark.parametrize("source,target,expected", [
        (PartialSimpleSource(), PartialSimpleTarget, expected_partial_simple),
        (PartialNestedSource(), PartialNestedTarget, expected_partial_nested),
        (PartialListSource(), PartialListTarget, expected_partial_list_existing),
        (PartialNewListSource(), PartialNewListTarget, expected_partial_list_new),
        (PartialRootListSource(), PartialRootListTarget, expected_partial_list_root)
    ])
    def test_partial_returns(self, model_mapper, source, target, expected):
        """
        Parametrized test for partial return scenarios.
        Tests different partial return situations with a single test function.
        """
        result = model_mapper.map_models(source, target)
        
        # Verify the result is a dict (partial mapping)
        assert isinstance(result, dict)
        
        # Verify the expected fields are present and have the correct values
        for field, value in expected.items():
            assert field in result
            assert result[field] == value