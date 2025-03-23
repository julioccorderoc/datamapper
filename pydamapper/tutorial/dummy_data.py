"""
dummy_data.py
=============

This module provides dummy data for testing and tutorials:
    - Raw source data as pydantic models
    - Expected target data as pydantic models
    - Expected target data as dictionaries for partial returns

If ran as a script, it also prints the expected data as a pretty JSON string.
"""

import pydamapper.tutorial.models as models
from datetime import date
import json

# ----------------------------------------------------------
# Bases for both main source and target Ecommerce order data
# ----------------------------------------------------------

# Mock Customer Details
customer_details = models.CustomerDetails(customer_id=54321, full_name="John Doe")

# Mock Address
address = models.Address(address_name="Home", city="Springfield", state="IL")

# Mock Promotions
promotion1 = models.Promotion(promotion_id=201, discount=10.0)
promotion2 = models.Promotion(promotion_id=202, discount=5.0)

# Mock Customizations
customization1 = models.Customization(customization_id=1, customization_name="Color: Red")
customization2 = models.Customization(customization_id=2, customization_name="Size: Large")

# Mock Products
product1 = models.Product(
    product_id=101, price=25.0, customizations=[customization1, customization2]
)
product2 = models.Product(product_id=102, price=50.0, customizations=[customization2])

# Mock Cart Details
cart_details1 = models.CartDetails(product=product1)
cart_details2 = models.CartDetails(product=product2)
cart_details = [cart_details1, cart_details2]

# Mock taxes
taxes = models.Taxes(tax=7.50)

# Mock payment info
payment_info = models.PaymentInfo(
    payment_method="Credit Card", promotions=[promotion1, promotion2], taxes=taxes
)

# Mock new products
newproduct1 = models.NewProduct(product_id=101, price=25.0)
newproduct2 = models.NewProduct(product_id=102, price=50.0)

# Mock cart info
cart_info = models.CartInfo(
    products=[newproduct1, newproduct2], customizations=[customization1, customization2]
)

# ---------------------
# Ecommerce source data
# ---------------------

# Complete EcommerceOrder instance
source_data = models.EcommerceOrder(
    order_id=12345,
    customer_details=customer_details,
    address=address,
    order_date="2023-10-26",
    payment_method="Credit Card",
    promotions=[promotion1, promotion2],
    tax=7.50,
    cart_details=cart_details,
)

# -----------------------------------------
# Ecommerce data mapped to Accounting order
# -----------------------------------------

expected_target = models.AccountingOrder(
    order_id=12345,
    customer_id=54321,
    order_date=date(2023, 10, 26),
    payment_info=payment_info,
    cart_info=cart_info,
    comments=None,
)

# ------------
# Simple cases
# ------------

# Expected model from simple field mapping
expected_simple_match = models.SimpleTarget(**address.model_dump())

# Expected model for multiple nested fields match
expected_nested_match = models.NestedTarget(
    order_id=12345, full_name="John Doe", city="Springfield"
)

# --------------
# Building cases
# --------------

# Expected model from building new model with scattered fields
expected_building_scattered = models.NewModelTarget(
    address_name="Home", nested_model=expected_simple_match
)

# -----------
# Error cases
# -----------

# Expected dict from missing field error
expected_missing_field = {"address_name": "Home"}

# Expected dict from type mismatch error
expected_type_mismatch = {"state": "IL"}

# Expected dict from empty new model error
expected_empty_new_model = {"product_id": 101, "price": 25.0}

# --------------------
# Partial return cases
# --------------------

# Sub-dict for simple field mapping with partial return
sub_partial_simple = {"city": "Springfield", "state": "IL"}

# Expected new model partial return
expected_partial_simple = {"address_name": "Home", "meta_address": sub_partial_simple}

# Sub-dicts for scattered with partial return
sub_partial_scattered_1 = {"product_id": 101, "price": 25.0}
sub_partial_scattered_2 = {"product_id": 102, "price": 50.0}

# Exptected list of new models with partial return
expected_partial_scattered = {
    "scattered": [sub_partial_scattered_1, sub_partial_scattered_2],
    "customizations": [customization1, customization2],
}


if __name__ == "__main__":
    print("\nDUMMY DATA FOR TESTING AND TUTORIALS:")
    print("\n+++++ Printing expected output as a pretty JSON string: +++++\n")

    print("\n- EXPECTED ECOMMERCE ORDER:\n")
    print(json.dumps(source_data.model_dump(), indent=4, default=str))

    print("\n- EXPECTED ADDRESS FIELD:\n")
    print(json.dumps(address.model_dump(), indent=4, default=str))

    print("\n- EXPECTED ACCOUNTING ORDER:\n")
    print(json.dumps(expected_target.model_dump(), indent=4, default=str))

    print("\n- EXPECTED SIMPLE FIELD MATCH:\n")
    print(json.dumps(expected_simple_match.model_dump(), indent=4, default=str))

    print("\n- EXPECTED NESTED FIELD MATCH:\n")
    print(json.dumps(expected_nested_match.model_dump(), indent=4, default=str))

    print("\n- EXPECTED NEW MODEL FROM SCATTERED FIELDS MATCH:\n")
    print(json.dumps(expected_building_scattered.model_dump(), indent=4, default=str))

    print("\n- EXPECTED FIELD NOT FOUND ERROR:\n")
    print(json.dumps(expected_missing_field, indent=4, default=str))

    print("\n- EXPECTED FIELD FOUND WITH DIFFERENT TYPE ERROR:\n")
    print(json.dumps(expected_type_mismatch, indent=4, default=str))

    # print("\n- EXPECTED NEW MODEL EMPTY ERROR:\n") # TODO
    # print(json.dumps(expected_target.model_dump(), indent=4, default=str))

    print("\n- EXPECTED NEW MODEL PARTIAL RETURN CASE:\n")
    print(json.dumps(expected_partial_simple, indent=4, default=str))

    print("\n- EXPECTED LIST OF NEW MODELS PARTIAL RETURN CASE:\n")
    print(json.dumps(expected_partial_scattered, indent=4, default=str))
