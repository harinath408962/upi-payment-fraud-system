from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, text

from app.db.session import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    payment_method_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    customer_id = Column(
        BigInteger,
        ForeignKey("customers.customer_id"),
        nullable=False
    )
    method_type = Column(String(30), nullable=False)
    payment_token = Column(String(255), nullable=False, unique=True)
    display_identifier = Column(String(50), nullable=True)
    status = Column(
        String(20),
        nullable=False,
        server_default=text("'ACTIVE'")
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )   