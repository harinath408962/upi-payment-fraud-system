
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    text
)

from app.db.session import Base


class RetryAttempt(Base):
    __tablename__ = "retry_attempts"

    retry_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    transaction_id = Column(
        BigInteger,
        ForeignKey("payment_transactions.transaction_id"),
        nullable=False
    )

    retry_number = Column(
        Integer,
        nullable=False
    )

    retry_source = Column(
        String(30),
        nullable=False
    )

    retry_reason = Column(
        String(255),
        nullable=True
    )

    retry_status = Column(
        String(20),
        nullable=False
    )

    requested_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
