from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    merchant_id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    payment_method_id: int = Field(gt=0)

    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2
    )

    currency: Literal["INR"] = "INR"


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    merchant_id: int
    customer_id: int
    payment_method_id: int
    amount: Decimal
    currency: str
    transaction_status: str