
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings

from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentStatusUpdate,
    ProviderProcessRequest,
    ProviderConfirmationRequest
)

from app.services.payment_service import (
    PaymentServiceError,
    create_payment,
    update_payment_status
)

from app.services.provider_processing_service import (
    process_provider_payment,
    confirm_provider_payment
)


router = APIRouter(prefix="/payments", tags=["Payments"])


# Create a new payment
@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment_endpoint(
    payment_data: PaymentCreate,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=100
    ),
    db: Session = Depends(get_db)
):
    try:
        return create_payment(
            db=db,
            payment_data=payment_data,
            idempotency_key=idempotency_key
        )

    except PaymentServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.message
        )


# Development-only manual status update
if settings.DEBUG:

    @router.patch(
        "/{transaction_id}/status",
        response_model=PaymentResponse
    )
    def update_payment_status_endpoint(
        transaction_id: int,
        status_data: PaymentStatusUpdate,
        db: Session = Depends(get_db)
    ):
        try:
            return update_payment_status(
                db=db,
                transaction_id=transaction_id,
                new_status=status_data.transaction_status
            )

        except PaymentServiceError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.message
            )


# Process payment through simulated provider
@router.post(
    "/{transaction_id}/process",
    response_model=PaymentResponse
)
def process_provider_payment_endpoint(
    transaction_id: int,
    request: ProviderProcessRequest,
    db: Session = Depends(get_db)
):
    try:
        return process_provider_payment(
            db=db,
            transaction_id=transaction_id,
            outcome=request.outcome
        )

    except PaymentServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.message
        )


# Confirm a pending payment through simulated provider callback
@router.post(
    "/{transaction_id}/confirm",
    response_model=PaymentResponse
)
def confirm_provider_payment_endpoint(
    transaction_id: int,
    request: ProviderConfirmationRequest,
    db: Session = Depends(get_db)
):
    try:
        return confirm_provider_payment(
            db=db,
            transaction_id=transaction_id,
            outcome=request.outcome
        )

    except PaymentServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.message
        )
