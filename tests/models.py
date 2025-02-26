from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

# ---------------------------------------------------
# Complete test | It has all the cases | Source model
# ---------------------------------------------------

class SourceModelOrder(BaseModel):
    order_id: int
    customer_id: int
    customer_details: CustomerDetails
    address: Address
    order_date: date
    shipped: bool
    payment_method: str
    promotions: List[Promotion]
    tax: float
    total: float
    cart_details: List[CartDetails]
    checkout: Optional[List[Checkout]] = None # this won't be None
    comments: Optional[str] = None # this will be None
    webhook: Webhook


class CartDetails(BaseModel):
    product: Product

class Product(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int
    customizations: List[Customization]

class Customization(BaseModel):
    customization_id: int
    customization_name: str

class Promotion(BaseModel):
    promotion_id: int
    promotion_name: str
    discount: float

class CustomerDetails(BaseModel):
    full_name: str
    email: str
    phone: str
    education: str
    username: str

class Address(BaseModel):
    address_name: str
    address_line_1: str
    address_line_2: str
    city: str
    state: str
    zip_code: str
    country: str

class Checkout(BaseModel):
    extra_item_id: int
    extra_item_name: str
    extra_item_price: float

class Webhook(BaseModel):
    webhook_id: int
    webhook_name: str

# ---------------------------------------------------
# Complete test | It has all the cases | Target model
# ---------------------------------------------------

class TargetModelOrder(BaseModel):
    customer_id: int # direct match
    shipped: bool # direct match
    city: str # nested match
    webhook_name: str # nested match
    payment_info: PaymentInfo # build new model
    cart_info: CartInfo # build new model with list of models
    comments: Optional[str] # direct match

class PaymentInfo(BaseModel):
    payment_method: str # direct match
    promotions: List[Promotion] # list of models with direct instances
    taxes: Taxes # new model within a new model
    total: float # direct match

class CartInfo(BaseModel):
    products: List[Product] # direct match
    scattered: Optional[List[Scattered]] # list of models with scattered data

class Taxes(BaseModel):
    tax: float # direct match

class Scattered(BaseModel):
    extra_item_name: str # direct match
    extra_item_price: float # direct match


# ---------------------------------------------------
# All other cases
# ---------------------------------------------------

# Target model for simple field mapping
class SimpleAddressTarget(BaseModel):
    city: str
    state: str
    zip_code: str
    country: str

# Target model for nested field match
class MetaUserTarget(BaseModel):
    username: str
    email: str
    education: str
    city: str
    state: str

# Target model for new model creation
class NestedAddressTarget(BaseModel):
    address_line_1: str
    address_line_2: str
    meta_address: Optional[SimpleAddressTarget]

# Target model for nested model creation
class Nested(BaseModel):
    field1: str
    field2: int

class NestedTarget(BaseModel):
    nested: Nested

# Target models for list handling
class Item(BaseModel):
    name: str
    value: int

class ListTarget(BaseModel):
    items: List[Item]

class NewItem(BaseModel):
    item_name: str
    item_value: int

class NewListTarget(BaseModel):
    new_items: List[NewItem]

class RootListTarget(BaseModel):
    root_list: List[str]

# Target model for error cases
class ErrorTarget(BaseModel):
    missing_field: str
    wrong_type: int

# Target models for partial return tests
class PartialSimpleTarget(BaseModel):
    found_field: str
    missing_field: str

class PartialNested(BaseModel):
    field: str

class PartialNestedTarget(BaseModel):
    nested: PartialNested
    missing: str

class PartialListTarget(BaseModel):
    items: List[Item]
    missing: str

class PartialNewListTarget(BaseModel):
    new_items: List[NewItem]
    missing: str

class PartialRootListTarget(BaseModel):
    root_list: List[str]
    missing: str