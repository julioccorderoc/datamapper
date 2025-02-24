from tests.models import *

payment_info = PaymentInfo(
    payment_method="Credit Card",
    promotions=[
        Promotion(promotion_id=201, promotion_name="Summer Sale", discount=10.0),
        Promotion(promotion_id=202, promotion_name="New Customer", discount=5.0),
    ],
    taxes=Taxes(tax=7.50),
    total=107.50,
)

scattered_items = [
    Scattered(extra_item_name="Gift Wrap", extra_item_price=5.0),
    Scattered(extra_item_name="Rush Delivery", extra_item_price=10.0),
]

# Mock Customizations
customization1 = Customization(customization_id=1, customization_name="Color: Red")
customization2 = Customization(customization_id=2, customization_name="Size: Large")

cart_info = CartInfo(
    products=[
        Product(product_id=101, product_name="T-Shirt", price=25.0, quantity=2, customizations=[customization1, customization2]),
        Product(product_id=102, product_name="Jeans", price=50.0, quantity=1, customizations=[customization2]),
    ],
    scattered=scattered_items,
)

expected_target = TargetOrderForAccounting(
    customer_id=54321,
    shipped=False,
    city="Springfield",
    webhook_name="OrderCreated",
    payment_info=payment_info,
    cart_info=cart_info,
    comments="Leave at front door.",
)

import json
print(json.dumps(expected_target.model_dump(), indent=4))