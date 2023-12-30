import logging
from .schemas import OrderCreate
from .models import Account, Orders
from host_app.common.util import create_hashed_password, generate_salt
from host_app.caching.redis_constant import RedisConstant
from sqlalchemy.orm import Session
from host_app.caching import redis_util
from typing import Optional
from host_app.common import order_util


# ==================== Orders CRUD METHODS =================================

async def create_new_order(db: Session, user_id:str, service_org:str, orders_info: OrderCreate):
    try :
        order_id = await order_util.create_order_id(user_id)
        order_obj = Orders(order_id=order_id, product_id=orders_info.product_id, owner_id=orders_info.owner_id,receivers_mobile= orders_info.receivers_mobile, delivery_address=orders_info.delivery_address, service_org=service_org)
        db.add(order_obj)
        db.commit()
        db.refresh(order_obj)
        return order_obj.to_dict()
    except Exception as ex :
        logging.exception("[order_crud][Exception in create_new_order]",ex)
    


def get_all_orders_by_user(db: Session, user_id: str, org: Optional[str] = None):
    try:
        if not org : 
            single_order_obj = db.query(Orders).filter(Orders.owner_id == user_id).all()
        else :
            single_order_obj = db.query(Orders).filter(Orders.owner_id == user_id, Orders.service_org == org).all()

        return single_order_obj
    except Exception as ex:
        logging.exception("[order_crud][Exception in get_all_orders_by_user] {} ".format(ex))


def get_all_order_id_by_user(db:Session, user_id: str, org: Optional[str] = None ):
    try:
        order_ids = []
        if not org : 
            order_ids = db.query(Orders.id).filter(Orders.owner_id == user_id).all()
        else:
            order_ids = db.query(Orders.id).filter(Orders.owner_id == user_id, Orders.service_org == org).all()
            
        return order_ids

    except Exception as ex:
        logging.exception("[order_crud][Exception in get_all_orders_by_user] {} ".format(ex))

def get_order_by_order_id(db: Session, user_id : str, order_id: str, org: Optional[str] = None):
    try:
        order_obj =  db.query(Orders).filter(Orders.order_id == order_id, Orders.owner_id== user_id).first()
        
    except Exception as ex :
        logging.exception("[crud][Exception in get_order_by_order_id] {} ".format(ex))


def get_orders_status(db: Session, user_id : str, Orders_id: int, org: Optional[str] = None):
    try:
        order = get_order_by_order_id(db, Orders_id)
        return order
    except Exception as ex :
        logging.exception("[crud][Exception in get_order_by_order_id] {} ".format(ex))
    


async def update_order_status(db: Session, user_id : str, order_id: str, orders_status: dict, org: Optional[str] = None):
    try :
        logging.info("[CRUD][Landed in update_Orders_status] {} ".format(orders_status))
        order_obj = db.query(Orders).filter(Orders.order_id == order_id).first()
  
        if order_obj:
            for key, value in orders_status.items():
                if key and value :
                    setattr(order_obj, key, value)
            db.commit()
            db.refresh(order_obj)
            
            updated_order_obj = db.query(Orders).filter(Orders.order_id == order_id).first()
            print(" UPDATED updated_order_obj : ",updated_order_obj)
            return updated_order_obj.to_dict()
        return None
    except Exception as ex :
        logging.exception("[CRUD][Exception in update_Orders_status] {} ".format(ex))


def delete_order(db: Session, order_id: str, user_id : str, org: Optional[str] = None):
    try:
        order_obj = db.query(Orders).filter(Orders.order_id == order_id).first()
        if order_obj.owner_id != user_id :
            logging.info("[CRUD][Not authorizede to delete this order][Order_Id] {} [User_id] {}".format(order_id, user_id))
            return False
        if order_obj:
            db.delete(order_obj)
            db.commit()
            return True
    except Exception as ex :
        logging.exception("[CRUD][Exception in delete_order] {} ".format(ex))
    return False



def get_all_orderss(db: Session, skip: int = 0, limit: int = 100, org: Optional[str] = None):
    try:
        if not org :
            return db.query(Orders).offset(skip).limit(limit).all()
        return db.query(Account).filter(Orders.service_org == org).all()
        
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_all_Orderss] {} ".format(ex))


async def get_single_order(db: Session, user_id: str, order_id: str, org: Optional[str] = None):
    try:
        if(await redis_util.is_exists(RedisConstant.ORDER_OBJ + order_id)):
            single_order = await redis_util.get_hm(RedisConstant.ORDER_OBJ + order_id)
            if single_order["user_id"] == user_id :
                return single_order
        else :
            single_order = get_order_by_order_id(db, order_id)

            if single_order.user_id == user_id :
                data = single_order.to_dict()
                creted_time = data["created_time"]
                data["created_time"] = str(creted_time)
                await redis_util.set_hm(RedisConstant.ORDER_OBJ + order_id, data, 1800)
    
                return single_order

    except Exception as ex :
        logging.exception("[MAIN][Exception in get_single_order] {} ".format(ex))
    return single_order