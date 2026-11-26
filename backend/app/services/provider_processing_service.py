
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.payment_transaction import PaymentTransaction
from app.models.payment_attempt import PaymentAttempt
from app.models.retry_attempt import RetryAttempt

from app.services.payment_service import PaymentServiceError
from app.services.provider_simulator import simulate_provider_response


def process_provider_payment(
    db: Session,
    transaction_id: int,
    outcome: str
) -> PaymentTransaction:

    allowed_outcomes = {"SUCCESS", "FAILED", "TIMEOUT", "PENDING"}

    if outcome not in allowed_outcomes:
        raise PaymentServiceError("Invalid provider outcome", 400)

    try:
        # Lock the transaction to prevent concurrent processing.
        payment = db.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.transaction_id == transaction_id)
            .with_for_update()
        ).scalar_one_or_none()

        if payment is None:
            raise PaymentServiceError("Payment not found", 404)

        previous_status = payment.transaction_status

        # Only new or failed payments can start a provider attempt.
        if previous_status not in {"CREATED", "FAILED"}:
            raise PaymentServiceError(
                f"Cannot process provider payment from status: {previous_status}",
                409
            )

        # Calculate the next provider attempt number.
        previous_attempt_count = db.execute(
            select(func.max(PaymentAttempt.attempt_number))
            .where(PaymentAttempt.transaction_id == transaction_id)
        ).scalar_one_or_none()

        attempt_number = (previous_attempt_count or 0) + 1

        # A retry record is created when processing a previously failed payment.
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

        # Start the provider attempt.
        payment.transaction_status = "PENDING"

        provider_response = simulate_provider_response(outcome)

        attempt = PaymentAttempt(
            transaction_id=transaction_id,
            attempt_number=attempt_number,
            provider_reference=provider_response["provider_reference"],
            provider_response=provider_response,
            response_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        db.add(attempt)

        # Map provider outcome to payment status.
        if outcome == "SUCCESS":
            payment.transaction_status = "SUCCESS"

        elif outcome == "FAILED":
            payment.transaction_status = "FAILED"

        else:
            # TIMEOUT and PENDING await further provider confirmation.
            payment.transaction_status = "PENDING"

        payment.updated_at = func.now()

        # Update retry record after the provider attempt.
        if retry_record is not None:
            if outcome == "FAILED" or outcome == "TIMEOUT":
                retry_record.retry_status = "FAILED"
            else:
                retry_record.retry_status = "COMPLETED"

        db.commit()
        db.refresh(payment)

        return payment

    except PaymentServiceError:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
