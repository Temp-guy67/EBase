from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String)
    salt = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    created_time = Column(DateTime, default=func.now())
    last_login_time = Column(DateTime, onupdate=func.now())

    # items = relationship("Order", back_populates="owner")


# class Order(Base):
#     __tablename__ = "order"

#     id = Column(Integer, primary_key=True, index=True)
#     order_id = Column(String,primary_key=True, unique=True, nullable=False)
#     order_status = Column(String)
#     payment_status = Column(Boolean)
#     delivery_address = Column(String)
#     owner_id = Column(Integer, ForeignKey("account.id"))

#     owner = relationship("Account", back_populates="order")
