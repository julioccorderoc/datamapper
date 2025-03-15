import pytest
from pydantic import BaseModel

from datamapper import DataMapper, map_models
from datamapper.src.error_manager import ErrorType
from datamapper.src.types import ModelType, DataMapped

from .sources import source_data, address

from .models import (
    TargetModelOrder,
    PaymentInfo,
    CartInfo,
    SimpleAddressTarget,
    MetaUserTarget,
    NestedAddressTarget,
    TypeErrorAddress,
    MissingFieldAddress,
    PartialNewModelNestedAddress,
    PartialListNewCartInfo,
)

from .expected import (
    expected_target,
    payment_info,
    cart_info,
    expected_simple_target,
    expected_nested_target,
    expected_new_model,
    expected_new_model_partial,
    expected_list_new_partial,
)


# Add case when it's acceptable to receive a None in a target field
#


class TestCompleteMapper:
    """Tests for full model mapping functionality."""

    def test_complete_mapping(self) -> None:
        """Verifies that the complete mapping matches the expected result."""
        complete_mapping = map_models(source_data, TargetModelOrder)
        assert complete_mapping == expected_target


class TestFieldMapping:
    """Tests for individual field mapping scenarios."""

    def test_simple_field_match(self) -> None:
        """Tests mapping of a simple field with direct name match."""
        simple_field = map_models(address, SimpleAddressTarget)
        assert simple_field == expected_simple_target

    def test_nested_field_match(self) -> None:
        """Tests mapping a field from a nested structure."""
        nested_field = map_models(source_data, MetaUserTarget)
        assert nested_field == expected_nested_target


class TestNestedModelCreation:
    """Tests for building new models from scattered fields."""

    def test_build_new_models_from_scattered_fields(self) -> None:
        """Tests creation of a new nested model from scattered fields."""
        new_model = map_models(address, NestedAddressTarget)
        assert new_model == expected_new_model


class TestListHandling:
    """Tests for handling lists of models."""

    def test_list_of_existing_models(self) -> None:
        """Tests mapping a list of models that exist in the source."""
        result = map_models(source_data, PaymentInfo)
        assert result == payment_info

    def test_list_of_models_with_new_models(self) -> None:
        """Tests mapping a list with models that need to be created from fields."""
        result = map_models(source_data, CartInfo)
        assert result == cart_info

    # def test_list_in_root(self):
    #     """Tests mapping a root-level list."""
    #     result = mapper.map_models(ListSource(), RootListTarget)
    #     assert result.root_list == ExpectedRootListTarget.root_list


# TODO: use the errors property
class TestErrorCases:
    """Tests for error handling scenarios."""

    def test_field_in_target_not_found_in_source(self) -> None:
        """Tests handling when a target field doesn't exist in the source."""
        # Should return a dict since it can't fully build the model
        required_field_error = ErrorType.REQUIRED_FIELD
        mapper = DataMapper()
        result = mapper.map_models(address, MissingFieldAddress)
        assert isinstance(result, dict)
        assert required_field_error in mapper.error_manager.errors
        assert len(mapper.error_manager.errors) == 1

    def test_field_found_with_different_type(self) -> None:
        """Tests handling when a field exists but has an incompatible type."""
        # Should return a dict with the fields it could map
        validation_error = ErrorType.VALIDATION
        mapper = DataMapper()
        result = mapper.map_models(address, TypeErrorAddress)
        assert isinstance(result, dict)
        assert validation_error in mapper.error_manager.errors
        assert len(mapper.error_manager.errors) == 1

    # def test_new_model_empty(self):
    #     """Tests handling when a new model is empty."""
    #     mapper = datamapper()

    # def test_no_mappable_data(self):
    #     """Tests handling when no mappable data is found."""
    #     mapper = datamapper()


class TestPartialReturns:
    """Tests for partial return scenarios."""

    @pytest.mark.parametrize(
        "source,target,expected",
        [
            (address, PartialNewModelNestedAddress, expected_new_model_partial),
            (source_data, PartialListNewCartInfo, expected_list_new_partial),
        ],
    )
    def test_partial_returns(
        self, source: BaseModel, target: ModelType, expected: DataMapped
    ) -> None:
        """
        Parametrized test for partial return scenarios.
        Tests different partial return situations with a single test function.
        """
        partial_return = ErrorType.PARTIAL_RETURN
        mapper = DataMapper()
        result = mapper.map_models(source, target)

        # Verify the result is a dict (partial mapping)
        assert isinstance(result, dict)
        assert partial_return in mapper.error_manager.errors
        assert result == expected
