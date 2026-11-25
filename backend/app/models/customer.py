from sqlalchemy import BigInteger, Column, DateTime, String, text

from app.db.session import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=True, unique=True)
    phone = Column(String(15), nullable=False, unique=True)
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )