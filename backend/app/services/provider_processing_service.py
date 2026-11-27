
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.payment_transaction import PaymentTransaction
from app.models.payment_attempt import PaymentAttempt
from app.models.retry_attempt import RetryAttempt

from app.services.provider_simulator import simulate_provider_response
from app.services.payment_service import PaymentServiceError


ALLOWED_PAYMENT_TRANSITIONS = {
    "CREATED": {"PENDING", "CANCELLED"},
    "PENDING": {"SUCCESS", "FAILED", "CANCELLED"},
    "FAILED": {"PENDING"},
    "SUCCESS": set(),
    "CANCELLED": set()
}


def transition_payment(payment, new_status):
    current_status = payment.transaction_status

    if new_status not in ALLOWED_PAYMENT_TRANSITIONS.get(
        current_status, set()
    ):
        raise PaymentServiceError(
            f"Invalid payment transition: {current_status} -> {new_status}",
            409
        )

    payment.transaction_status = new_status
    payment.updated_at = func.now()


def process_provider_payment(
    db: Session,
    transaction_id: int,
    outcome: str
) -> PaymentTransaction:

    allowed_outcomes = {"SUCCESS", "FAILED", "TIMEOUT", "PENDING"}

    if outcome not in allowed_outcomes:
        raise PaymentServiceError("Invalid provider outcome", 400)

    try:
        payment = db.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.transaction_id == transaction_id)
            .with_for_update()
        ).scalar_one_or_none()

        if payment is None:
            raise PaymentServiceError("Payment not found", 404)

        previous_status = payment.transaction_status

        if previous_status not in {"CREATED", "FAILED"}:
            raise PaymentServiceError(
                f"Cannot process provider payment from status: {previous_status}",
                409
            )

        # Move the payment into PENDING before processing the outcome.
        transition_payment(payment, "PENDING")

        previous_attempt_count = db.execute(
            select(func.max(PaymentAttempt.attempt_number))
            .where(PaymentAttempt.transaction_id == transaction_id)
        ).scalar_one_or_none()

        attempt_number = (previous_attempt_count or 0) + 1

        retry_record = None

        if previous_status == "FAILED":
            previous_retry_count = db.execute(
                select(func.max(RetryAttempt.retry_number))
                .where(RetryAttempt.transaction_id == transaction_id)
            ).scalar_one_or_none()

            retry_record = RetryAttempt(
                transaction_id=transaction_id,
                retry_number=(previous_retry_count or 0) + 1,
                retry_source="SYSTEM",
                retry_reason="Retry after previous provider failure",
                retry_status="REQUESTED"
            )

            db.add(retry_record)

        provider_result = simulate_provider_response(outcome)

        # TIMEOUT means no provider acknowledgement was received.
        provider_response = (
            None if outcome == "TIMEOUT"
            else provider_result
        )

        response_at = (
            None if outcome == "TIMEOUT"
            else datetime.now(timezone.utc).replace(tzinfo=None)
        )

        attempt = PaymentAttempt(
            transaction_id=transaction_id,
            attempt_number=attempt_number,
            provider_reference=provider_result["provider_reference"],
            provider_response=provider_response,
            response_at=response_at
        )

        db.add(attempt)

        # Apply the final state transition when the provider responds.
        if outcome in {"SUCCESS", "FAILED"}:
            transition_payment(payment, outcome)

        # TIMEOUT and PENDING remain in the PENDING state.
        if retry_record is not None:
            if outcome == "SUCCESS":
                retry_record.retry_status = "COMPLETED"

            elif outcome == "FAILED":
                retry_record.retry_status = "FAILED"

            # TIMEOUT and PENDING remain REQUESTED.

        db.commit()
        db.refresh(payment)

        return payment

    except PaymentServiceError:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


def confirm_provider_payment(
    db: Session,
    transaction_id: int,
    outcome: str
) -> PaymentTransaction:

    if outcome not in {"SUCCESS", "FAILED"}:
        raise PaymentServiceError("Invalid confirmation outcome", 400)

    try:
        payment = db.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.transaction_id == transaction_id)
            .with_for_update()
        ).scalar_one_or_none()

        if payment is None:
            raise PaymentServiceError("Payment not found", 404)

        if payment.transaction_status != "PENDING":
            raise PaymentServiceError(
                f"Cannot confirm payment from status: {payment.transaction_status}",
                409
            )

        # Retrieve the latest provider attempt.
        attempt = db.execute(
            select(PaymentAttempt)
            .where(PaymentAttempt.transaction_id == transaction_id)
            .order_by(PaymentAttempt.attempt_number.desc())
            .with_for_update()
        ).scalars().first()

        if attempt is None:
            raise PaymentServiceError(
                "No provider attempt found for this payment",
                409
            )

        confirmation = simulate_provider_response(outcome)

        # Preserve the original provider reference when available.
        if attempt.provider_reference is None:
            attempt.provider_reference = confirmation["provider_reference"]

        confirmation["provider_reference"] = attempt.provider_reference

        attempt.provider_response = confirmation
        attempt.response_at = datetime.now(timezone.utc).replace(tzinfo=None)

        transition_payment(payment, outcome)

        # Complete the outstanding retry, if this was a retry.
        retry_record = db.execute(
            select(RetryAttempt)
            .where(
                RetryAttempt.transaction_id == transaction_id,
                RetryAttempt.retry_status == "REQUESTED"
            )
            .order_by(RetryAttempt.retry_number.desc())
            .with_for_update()
        ).scalars().first()

        if retry_record is not None:
            retry_record.retry_status = (
                "COMPLETED" if outcome == "SUCCESS" else "FAILED"
            )

        db.commit()
        db.refresh(payment)

        return payment

    except PaymentServiceError:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
