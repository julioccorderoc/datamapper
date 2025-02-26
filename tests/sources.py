from .models import *

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

cart_details1 = CartDetails(product=product1)
cart_details2 = CartDetails(product=product2)

# Mock Promotions
promotion1 = Promotion(promotion_id=201, promotion_name="Summer Sale", discount=10.0)
promotion2 = Promotion(promotion_id=202, promotion_name="New Customer", discount=5.0)

# Mock Customer Details
customer_details = CustomerDetails(
    full_name="John Doe",
    email="john.doe@example.com",
    phone="555-123-4567",
    education="Bachelor of Science",
    username="johndoe",
)

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
cart_details = [cart_details1, cart_details2]

# Complete SourceModelOrder instance
source_data = SourceModelOrder(
    order_id=12345,
    customer_id=54321,
    customer_details=customer_details,
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
# print(json.dumps(source_data.model_dump(), indent=4, default=str))


# ---------------------------------------------------
# All other cases
# ---------------------------------------------------

# Source model for simple field mapping
class SimpleSource(BaseModel):
    simple_field: str
    nested: dict = {"nested_field": "nested_value"}

simple_source = Address(
    address_name = "Address_name",
    address_line_1 = "Address_line_1",
    address_line_2 = "Address_line_2",
    city = "City",
    state = "State",
    zip_code = "Zip_code",
    country = "Country",
)

# Source model for nested model creation
class ScatteredSource(BaseModel):
    field1: str = "value1"
    field2: int = 42
    unrelated: str = "ignore"

# Source models for list handling
class Item(BaseModel):
    name: str
    value: int

class ListSource(BaseModel):
    items: List[Item] = [
        Item(name="item1", value=1),
        Item(name="item2", value=2)
    ]
    root_list: List[str] = ["a", "b", "c"]

# Source model for error cases
class ErrorSource(BaseModel):
    existing_field: str = "value"
    wrong_type: str = "not_an_int"

# Source models for partial return tests
class PartialSimpleSource(BaseModel):
    found_field: str = "value"

class PartialNestedSource(BaseModel):
    data: dict = {"field": "value"}

class PartialListItem(BaseModel):
    name: str = "item1"

class PartialListSource(BaseModel):
    items: List[PartialListItem] = [PartialListItem()]

class PartialSourceItem(BaseModel):
    old_name: str = "item1"

class PartialNewListSource(BaseModel):
    items: List[PartialSourceItem] = [PartialSourceItem()]

class PartialRootListSource(BaseModel):
    root_list: List[str] = ["a", "b"]