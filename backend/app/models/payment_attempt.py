
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    text
)

from app.db.session import Base


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    payment_attempt_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    transaction_id = Column(
        BigInteger,
        ForeignKey("payment_transactions.transaction_id"),
        nullable=False
    )

    attempt_number = Column(
        Integer,
        nullable=False
    )

    provider_reference = Column(
        String(100),
        unique=True,
        nullable=True
    )

    provider_response = Column(
        JSON,
        nullable=True
    )

    attempted_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )

    response_at = Column(
        DateTime,
        nullable=True
    )
