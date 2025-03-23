import pytest
from pydantic import BaseModel

from pydamapper import PyDaMapper, map_models
from pydamapper.src.error_manager import ErrorType
from pydamapper.src.types import ModelType, DataMapped
from pydamapper.src.exceptions import NoMappableData, InvalidArguments
from pydamapper.tutorial import models
from pydamapper.tutorial import dummy_data as dummy


class TestCompleteMapper:
    """Tests for full model mapping functionality."""

    def test_complete_mapping(self) -> None:
        """Verifies that the complete mapping matches the expected result."""
        complete_mapping = map_models(dummy.source_data, models.AccountingOrder)
        assert complete_mapping == dummy.expected_target


class TestSimpleCases:
    """Tests for individual field mapping scenarios."""

    def test_simple_field_match(self) -> None:
        """Tests mapping of a simple field with direct name match."""
        simple_field = map_models(dummy.address, models.SimpleTarget)
        assert simple_field == dummy.expected_simple_match

    def test_nested_field_match(self) -> None:
        """Tests mapping a field from a nested structure."""
        nested_field = map_models(dummy.source_data, models.NestedTarget)
        assert nested_field == dummy.expected_nested_match


class TestBuildingCases:
    """Tests for building new models and lists."""

    def test_build_new_models_from_scattered_fields(self) -> None:
        """Tests creation of a new nested model from scattered fields."""
        new_model = map_models(dummy.address, models.NewModelTarget)
        assert new_model == dummy.expected_building_scattered

    def test_list_of_existing_models(self) -> None:
        """Tests mapping a list of models that exist in the source."""
        result = map_models(dummy.source_data, models.PaymentInfo)
        assert result == dummy.payment_info

    def test_list_of_models_with_new_models(self) -> None:
        """Tests mapping a list with models that need to be created from fields."""
        result = map_models(dummy.source_data, models.CartInfo)
        assert result == dummy.cart_info

    # def test_list_in_root(self):
    #     """Tests mapping a root-level list."""
    #     result = mapper.map_models(ListSource(), RootListTarget)
    #     assert result.root_list == ExpectedRootListTarget.root_list


# TODO: use the errors property
class TestErrorCases:
    """Tests for error handling scenarios."""

    def test_field_in_target_not_found_in_source(self) -> None:
        """Tests handling when a target field doesn't exist in the source."""
        required_field_error = ErrorType.REQUIRED_FIELD
        mapper = PyDaMapper()
        result = mapper.map_models(dummy.address, models.MissingFieldCase)
        assert isinstance(result, dict)
        assert required_field_error in mapper.error_manager.errors
        assert len(mapper.error_manager.errors) == 1
        assert result == dummy.expected_missing_field

    def test_field_found_with_different_type(self) -> None:
        """Tests handling when a field exists but has an incompatible type."""
        validation_error = ErrorType.VALIDATION
        mapper = PyDaMapper()
        result = mapper.map_models(dummy.address, models.TypeErrorCase)
        assert isinstance(result, dict)
        assert validation_error in mapper.error_manager.errors
        assert len(mapper.error_manager.errors) == 2
        assert result == dummy.expected_type_mismatch

    def test_new_model_empty(self):
        """Tests handling when a new model is empty."""
        empty_model_error = ErrorType.EMPTY_MODEL
        mapper = PyDaMapper()
        result = mapper.map_models(dummy.newproduct1, models.Product)
        assert isinstance(result, dict)
        assert empty_model_error in mapper.error_manager.errors
        assert len(mapper.error_manager.errors) == 2
        assert result == dummy.expected_empty_new_model

    def test_no_mappable_data(self):
        """Tests handling when no mappable data is found."""
        with pytest.raises(NoMappableData):
            map_models(dummy.customer_details, models.Address)

    def test_invalid_arguments_source(self):
        """Tests handling when an invalid source argument is passed."""
        with pytest.raises(InvalidArguments):
            map_models(models.Address, models.Address)

    def test_invalid_arguments_target(self):
        """Tests handling when an invalid target argument is passed."""
        with pytest.raises(InvalidArguments):
            map_models(dummy.address, dummy.address)


class TestPartialReturns:
    """Tests for partial return scenarios."""

    @pytest.mark.parametrize(
        "source,target,expected",
        [
            (dummy.address, models.PartialNewModel, dummy.expected_partial_simple),
            (dummy.source_data, models.PartialListNewModel, dummy.expected_partial_scattered),
        ],
    )
    def test_partial_returns(
        self, source: BaseModel, target: ModelType, expected: DataMapped
    ) -> None:
        """
        Tests partial return scenarios when building new models.
        """
        partial_return = ErrorType.PARTIAL_RETURN
        mapper = PyDaMapper()
        result = mapper.map_models(source, target)

        # Verify the result is a dict (partial mapping)
        assert isinstance(result, dict)
        assert partial_return in mapper.error_manager.errors
        assert result == expected
