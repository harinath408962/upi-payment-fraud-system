from sqlalchemy import (
    BigInteger,
    CHAR,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    String,
    text
)

from app.db.session import Base


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    transaction_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    merchant_id = Column(
        BigInteger,
        ForeignKey("merchants.merchant_id"),
        nullable=False
    )
    customer_id = Column(
        BigInteger,
        ForeignKey("customers.customer_id"),
        nullable=False
    )
    payment_method_id = Column(
        BigInteger,
        ForeignKey("payment_methods.payment_method_id"),
        nullable=False
    )
    idempotency_key = Column(String(100), nullable=False)
    request_hash = Column(CHAR(64), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(
        CHAR(3),
        nullable=False,
        server_default=text("'INR'")
    )
    transaction_status = Column(
        String(20),
        nullable=False,
        server_default=text("'CREATED'")
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )