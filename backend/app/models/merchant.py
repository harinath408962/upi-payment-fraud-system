from sqlalchemy import BigInteger, Column, DateTime, String, text

from app.db.session import Base


class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(BigInteger, primary_key=True, autoincrement=True)
    merchant_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    phone = Column(String(15), nullable=False)
    business_type = Column(String(100), nullable=True)
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