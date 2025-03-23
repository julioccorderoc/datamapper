"""
models.py
=========

This module provides pydantic models for testing and tutorials.
It uses as an example an order from an ecommerce that need to be sent to an accounting system.
    - Ecommerce Order: an order coming from an ecommerce platform
    - Accounting Order: an order in the format needed for the accounting system
    - Submodels: models used in the main models
    - Pure testing models: models for specific cases used in testing
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

# ----------------------
# Complete test | Source
# ----------------------


class EcommerceOrder(BaseModel):
    order_id: int
    customer_details: Optional[CustomerDetails] = None  # this won't be None
    address: Address
    order_date: str  # string type to be coerced to date
    payment_method: str
    promotions: List[Promotion]
    tax: float
    cart_details: List[CartDetails]  # list of one model
    comments: Optional[str] = None  # this will be None


class CartDetails(BaseModel):
    product: Product


class Product(BaseModel):
    product_id: int
    price: float
    customizations: List[Customization]


class Customization(BaseModel):
    customization_id: int
    customization_name: str


class Promotion(BaseModel):
    promotion_id: int
    discount: float


class CustomerDetails(BaseModel):
    customer_id: int
    full_name: str


class Address(BaseModel):
    address_name: str
    city: str
    state: str


# ----------------------
# Complete test | Target
# ----------------------


class AccountingOrder(BaseModel):
    order_id: int  # direct match
    customer_id: int  # nested match
    order_date: date  # coerced type from string
    payment_info: PaymentInfo  # build new model
    cart_info: CartInfo  # build new model with list of models
    comments: Optional[str] = None  # None case


class PaymentInfo(BaseModel):
    payment_method: str  # direct match
    promotions: List[Promotion]  # list of models with direct instances
    taxes: Taxes  # new model within a new model


class CartInfo(BaseModel):
    products: List[NewProduct]  # list of models with scattered data
    customizations: List[Customization]  # build list of existing models


class Taxes(BaseModel):
    tax: float  # direct match


class NewProduct(BaseModel):
    product_id: int
    price: float


# ------------
# Simple cases
# ------------


# Target model for simple field mapping
class SimpleTarget(BaseModel):
    city: str
    state: str


# Target model for multiple nested fields match
class NestedTarget(BaseModel):
    order_id: int  # direct match
    full_name: str  # nested match from the customer details model
    city: str  # nested match from the address model


# --------------
# Building cases
# --------------


# Target model for new model creation from scattered fields
class NewModelTarget(BaseModel):
    address_name: str
    nested_model: SimpleTarget  # new non existent model


# -----------
# Error cases
# -----------


# Target model for type error
class TypeErrorCase(BaseModel):
    city: bool  # str cannot be coerced to bool
    state: str


# Target model for field not found error
class MissingFieldCase(BaseModel):
    address_id: int
    address_name: str


# --------------------
# Partial return cases
# --------------------


# Sub-model for simple field mapping with partial return
class PartialSimpleMatch(BaseModel):
    city: str
    state: str
    non_existent_field: str  # field not found


# Target model for new model creation with partial return
class PartialNewModel(BaseModel):
    address_name: str
    meta_address: PartialSimpleMatch  # non existent field here
    another_non_existent_field: str  # field not found


# Sub-model for scattered models with partial return
class PartialScattered(BaseModel):
    product_id: int
    price: float
    non_existent_field: bool  # field not found


# Target model for list of new models with partial return
class PartialListNewModel(BaseModel):
    scattered: List[PartialScattered]  # non existent field here
    customizations: List[Customization]  # direct match
