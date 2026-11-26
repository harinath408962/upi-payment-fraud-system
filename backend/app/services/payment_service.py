
from decimal import Decimal
import hashlib
import json


from sqlalchemy.exc import IntegrityError

from app.schemas.payment import PaymentCreate

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.payment_method import PaymentMethod
from app.models.payment_transaction import PaymentTransaction


class PaymentServiceError(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def validate_payment_entities(
    db: Session,
    merchant_id: int,
    customer_id: int,
    payment_method_id: int
):
    # 1. Validate merchant
    merchant = db.execute(
        select(Merchant).where(
            Merchant.merchant_id == merchant_id
        )
    ).scalar_one_or_none()

    if merchant is None:
        raise PaymentServiceError("Merchant not found", 404)

    if merchant.status != "ACTIVE":
        raise PaymentServiceError("Merchant is not active", 403)

    # 2. Validate customer
    customer = db.execute(
        select(Customer).where(
            Customer.customer_id == customer_id
        )
    ).scalar_one_or_none()

    if customer is None:
        raise PaymentServiceError("Customer not found", 404)

    # 3. Validate payment method ownership and status
    payment_method = db.execute(
        select(PaymentMethod).where(
            PaymentMethod.payment_method_id == payment_method_id
        )
    ).scalar_one_or_none()

    if payment_method is None:
        raise PaymentServiceError("Payment method not found", 404)

    if payment_method.customer_id != customer_id:
        raise PaymentServiceError(
            "Payment method does not belong to this customer",
            403
        )

    if payment_method.status != "ACTIVE":
        raise PaymentServiceError(
            "Payment method is not active",
            403
        )

    return merchant, customer, payment_method



def generate_request_hash(
    merchant_id: int,
    customer_id: int,
    payment_method_id: int,
    amount: Decimal,
    currency: str
) -> str:
    normalized_amount = amount.quantize(Decimal("0.01"))

    request_data = {
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "payment_method_id": payment_method_id,
        "amount": format(normalized_amount, ".2f"),
        "currency": currency
    }

    canonical_data = json.dumps(
        request_data,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()



def create_payment(
    db: Session,
    payment_data: PaymentCreate,
    idempotency_key: str
) -> PaymentTransaction:

    # Validate the idempotency key
    if not idempotency_key or not idempotency_key.strip():
        raise PaymentServiceError(
            "Idempotency key is required",
            400
        )

    if len(idempotency_key) > 100:
        raise PaymentServiceError(
            "Idempotency key cannot exceed 100 characters",
            400
        )

    idempotency_key = idempotency_key.strip()

    # Generate a hash of the payment request
    request_hash = generate_request_hash(
        payment_data.merchant_id,
        payment_data.customer_id,
        payment_data.payment_method_id,
        payment_data.amount,
        payment_data.currency
    )

    # Check whether this request was already processed
    existing_payment = db.execute(
        select(PaymentTransaction).where(
            PaymentTransaction.merchant_id == payment_data.merchant_id,
            PaymentTransaction.idempotency_key == idempotency_key
        )
    ).scalar_one_or_none()

    if existing_payment:
        if existing_payment.request_hash != request_hash:
            raise PaymentServiceError(
                "Idempotency key already used with different payment details",
                409
            )

        return existing_payment

    # Validate entities before creating a new payment
    validate_payment_entities(
        db,
        payment_data.merchant_id,
        payment_data.customer_id,
        payment_data.payment_method_id
    )

    # Prepare the new payment transaction
    new_payment = PaymentTransaction(
        merchant_id=payment_data.merchant_id,
        customer_id=payment_data.customer_id,
        payment_method_id=payment_data.payment_method_id,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        amount=payment_data.amount,
        currency=payment_data.currency,
        transaction_status="CREATED"
    )

    db.add(new_payment)

    try:
        db.commit()
        db.refresh(new_payment)
        return new_payment

    except IntegrityError:
        # Another concurrent request may have inserted the same key.
        db.rollback()

        existing_payment = db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.merchant_id == payment_data.merchant_id,
                PaymentTransaction.idempotency_key == idempotency_key
            )
        ).scalar_one_or_none()

        if existing_payment:
            if existing_payment.request_hash != request_hash:
                raise PaymentServiceError(
                    "Idempotency key already used with different payment details",
                    409
                )

            return existing_payment

        # It was a different database integrity error.
        raise


ALLOWED_PAYMENT_TRANSITIONS = {
    "CREATED": {"PENDING", "CANCELLED"},
    "PENDING": {"SUCCESS", "FAILED", "CANCELLED"},
    "FAILED": {"PENDING"},
    "SUCCESS": set(),
    "CANCELLED": set()
}


def update_payment_status(
    db: Session,
    transaction_id: int,
    new_status: str
) -> PaymentTransaction:

    # Lock the payment row to prevent simultaneous conflicting updates.
    payment = db.execute(
        select(PaymentTransaction)
        .where(PaymentTransaction.transaction_id == transaction_id)
        .with_for_update()
    ).scalar_one_or_none()

    if payment is None:
        raise PaymentServiceError("Payment not found", 404)

    current_status = payment.transaction_status

    allowed_statuses = ALLOWED_PAYMENT_TRANSITIONS.get(
        current_status, set()
    )

    if new_status not in allowed_statuses:
        raise PaymentServiceError(
            f"Invalid payment transition: {current_status} -> {new_status}",
            409
        )

    payment.transaction_status = new_status
    payment.updated_at = func.now()

    db.commit()
    db.refresh(payment)

    return payment
