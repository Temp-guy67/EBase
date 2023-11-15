from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Account(Base):
    class Verification:
        NOT_VERIFIED=0
        VERIFIED=1

    class Role:
        USER=1
        ADMIN=2
        SUPER_ADMIN=3

    __tablename__ = "account"

    id = Column(Integer, primary_key=True,index=True, autoincrement=True)
    user_id = Column(String,  index=True, unique=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    is_verified = Column(Integer, default=Verification.NOT_VERIFIED)
    created_time = Column(DateTime, default=func.now())
    role = Column(Integer, default=Role.USER)
    last_login_time = Column(DateTime, onupdate=func.now())

    # items = relationship("Order", back_populates="owner")
    async def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'is_verified': self.is_verified,
            'role': self.role
        }


class Password(Base):
    __tablename__ = "password"
    id = Column(Integer,  primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("account.user_id"))
    hashed_password = Column(String)
    salt = Column(String, unique=True, nullable=False)
    last_updated_time = Column(DateTime, onupdate=func.now())


class Orders(Base):
    class PaymentStatus:
        DUE=1
        PAID=2
        FAILED=3

    class OrderStatus:
        IN_CART=1
        ORDERED=2
        IN_TRANSIT=3
        DELIVERED=4
        FAILED=5
        CANCELLED=6


    __tablename__ = "orders"
    order_id = Column(String, primary_key=True, unique=True)
    product_id = Column(String, nullable=False)
    order_quantity = Column(Integer, default=1)
    order_status = Column(Integer, default=OrderStatus.ORDERED)
    payment_status = Column(Integer, default= PaymentStatus.DUE)
    receivers_mobile = Column(String, nullable=False)
    delivery_address = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("account.user_id"))
    created_time = Column(DateTime, default=func.now())
    last_update_time = Column(DateTime, onupdate=func.now(), nullable=True)

    # owner = relationship("Account", back_populates="order")



    def to_dict(self):
        return {
            'order_id': self.order_id,
            'product_id': self.product_id,
            'order_status': self.order_status,
            'payment_status': self.payment_status,
            'delivery_address': self.delivery_address,
            'created_time' : self.created_time,
            'owner_id' : self.owner_id,
            'receivers_mobile' : self.receivers_mobile,
            'order_quantity' : self.order_quantity
        }




