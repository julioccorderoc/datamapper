from tests.models import *

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

# Mock Promotions
promotion1 = Promotion(promotion_id=201, promotion_name="Summer Sale", discount=10.0)
promotion2 = Promotion(promotion_id=202, promotion_name="New Customer", discount=5.0)

# Mock Address
address = Address(
    address_name="Home",
    address_line_1="123 Main St",
    address_line_2="Apt 4B",
    city="Springfield",
    state="IL",
    zip_code="62704",
    country="USA",
)

# Mock Checkout Items
checkout1 = Checkout(extra_item_id=301, extra_item_name="Gift Wrap", extra_item_price=5.0)
checkout2 = Checkout(extra_item_id=302, extra_item_name="Rush Delivery", extra_item_price=10.0)

# Mock Webhook
webhook = Webhook(webhook_id=401, webhook_name="OrderCreated")

# Mock Cart Details
cart_details = CartDetails(products=[product1, product2])

# Complete SourceNewOrderFromEcommerce instance
source_order = SourceNewOrderFromEcommerce(
    order_id=12345,
    customer_id=54321,
    address=address,
    order_date=date(2023, 10, 26),
    shipped=False,
    payment_method="Credit Card",
    promotions=[promotion1, promotion2],
    tax=7.50,
    total=107.50,
    cart_details=cart_details,
    checkout=[checkout1, checkout2],
    comments="Leave at front door.",
    webhook=webhook,
)

# import json
# print(json.dumps(source_order.model_dump(), indent=4, default=str))