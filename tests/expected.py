from .models import *

promotion1 = Promotion(promotion_id=201, promotion_name="Summer Sale", discount=10.0)
promotion2 = Promotion(promotion_id=202, promotion_name="New Customer", discount=5.0)

payment_info = PaymentInfo(
    payment_method="Credit Card",
    promotions=[promotion1, promotion2],
    taxes=Taxes(tax=7.50),
    total=107.50,
)

scattered1 = Scattered(extra_item_name="Gift Wrap", extra_item_price=5.0)
scattered2 = Scattered(extra_item_name="Rush Delivery", extra_item_price=10.0)

scattered_items = [scattered1, scattered2]

# Mock Customizations
customization1 = Customization(customization_id=1, customization_name="Color: Red")
customization2 = Customization(customization_id=2, customization_name="Size: Large")

# Mock Products
product1 = Product(
    product_id=101,
    product_name="T-Shirt",
    price=25.0,
    quantity=2,
    customizations=[customization1, customization2],
)
product2 = Product(
    product_id=102,
    product_name="Jeans",
    price=50.0,
    quantity=1,
    customizations=[customization2],
)

cart_info = CartInfo(
    products=[product1, product2],
    scattered=scattered_items,
)

expected_target = TargetModelOrder(
    customer_id=54321,
    shipped=False,
    city="Springfield",
    webhook_name="OrderCreated",
    payment_info=payment_info,
    cart_info=cart_info,
    comments="Leave at front door.",
)

# import json
# print(json.dumps(expected_target.model_dump(), indent=4))


# ---------------------------------------------------
# All other cases
# ---------------------------------------------------

# Expected model from simple field mapping
expected_simple_target = SimpleAddressTarget(
    city="Springfield",
    state="IL",
    zip_code="62704",
    country="USA",
)

expected_simple_target_partial = {
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62704",
    "country": "USA",
}

# Expected model from nested filed match
expected_nested_target = MetaUserTarget(
    username="johndoe",
    email="john.doe@example.com",
    education="Bachelor of Science",
    city="Springfield",
    state="IL",
)

expected_partial_nested_target = {
    "username": "johndoe",
    "email": "john.doe@example.com",
    "education": "Bachelor of Science",
    "city": "Springfield",
    "state": "IL",
}

# Expected model from new model building
expected_new_model = NestedAddressTarget(
    address_line_1="123 Main St",
    address_line_2="Apt 4B",
    meta_address=expected_simple_target,
)

expected_new_model_partial = {
    "address_line_1": "123 Main St",
    "address_line_2": "Apt 4B",
    "meta_address": expected_simple_target_partial,
}

scattered_partial = [
    {"extra_item_name": "Gift Wrap", "extra_item_price": 5.0},
    {"extra_item_name": "Rush Delivery", "extra_item_price": 10.0},
]

expected_list_new_partial = {
    "products": [product1, product2],
    "scattered": scattered_partial,
}
