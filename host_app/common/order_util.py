from typing import Optional
from fastapi import Depends
from host_app.database.schemas import OrderCreate
from sqlalchemy.orm import Session
import jwt, jwt.exceptions
import logging, random, string
from host_app.database import order_crud
from host_app.database.database import get_db
from host_app.caching import redis_util
from host_app.caching.redis_constant import RedisConstant


async def create_order(user_id:str, service_org:str, order_info: OrderCreate, db: Session = Depends(get_db)):
    try:
        new_order = await order_crud.create_new_order(db, user_id, service_org, order_info)
        
        if new_order :
            await redis_util.set_hm(RedisConstant.ORDER_OBJ + new_order["order_id"], new_order, 1800)
            
            order_ids = await add_order_ids_in_redis(db, user_id, new_order["order_id"], service_org)
        return new_order
    
    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in create_order] {} ".format(ex))



async def add_order_ids_in_redis(db: Session, user_id: str, order_id:str, org: Optional[str] = None):
    try:
        user_order_ids = await redis_util.get_set(RedisConstant.USER_ORDERS_SET + user_id)
        
        if user_order_ids:
            user_order_ids.add(order_id)
            await redis_util.add_to_set(RedisConstant.USER_ORDERS_SET + user_id, [order_id])
        
        user_order_ids = order_crud.get_all_order_id_by_user(db, user_id, org)
        
        return user_order_ids
    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in add_order_ids_in_redis] {} ".format(ex))


async def get_all_order_id_by_user(db: Session, user_id: str, org: Optional[str] = None):
    order_ids = []
    try:
        user_order_ids = await redis_util.get_set(RedisConstant.USER_ORDERS_SET + user_id)
        if not user_order_ids:
            user_order_ids = order_crud.get_all_order_id_by_user(db, user_id, org)
            await redis_util.add_to_set(RedisConstant.USER_ORDERS_SET + user_id)
        return user_order_ids
    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in get_all_orders_by_user] {} ".format(ex))
    
    return order_ids
    
    
    
async def get_all_orders(db: Session, user_id: str, org: Optional[str] = None):
    try :
        all_order_ids = await get_all_order_id_by_user(db, user_id, org)
        all_orders_obj = []
        
        for single_order_id in all_order_ids:
            single_order_obj = await get_single_order(db, user_id, single_order_id,  org)
            all_orders_obj.append(single_order_obj)
        return all_orders_obj
        
    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in get_all_orders] {} ".format(ex))


async def get_single_order(db: Session, user_id: str, order_id:str, org: Optional[str] = None):
    try:
        order_obj = await redis_util.get_hm(RedisConstant.ORDER_OBJ + order_id)
        
        if not order_obj :
            order_obj = order_crud.get_order_by_order_id(db, user_id, order_id, org)
            await redis_util.set_hm(RedisConstant.ORDER_OBJ + order_id, order_obj)
            
        return order_obj

    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in get_single_order] {} ".format(ex))
    
    

async def update_order_object(db:Session, user_id:str, order_data:dict, service_org: Optional[str] = None):
    try:
        
        order_id = order_data["order_id"]
        order_update_map = dict()
        
        possible_column_updates = ["order_status", "payment_status"]
        
        for k,v in order_data.items():
            if k in possible_column_updates:
                order_update_map[k] = v
        
        updated_order_obj = await order_crud.update_order_status(db, user_id, order_id, order_update_map, service_org)
        
        if updated_order_obj :
            await redis_util.set_hm(RedisConstant.ORDER_OBJ + order_id, updated_order_obj)
            
        return updated_order_obj
    except Exception as ex :
        logging.exception("[ORDER_UTIL][Exception in update_order_object] {} ".format(ex))
    

async def create_order_id(user_id : str, service_org:str):
    try :
        random_id = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(5)])
        order_id = user_id[:2] + user_id[5:] + "_" + random_id
        return order_id
    
    except Exception as ex :
        logging.exception("[ORDER_UTIL][Exception in create_order_id] {} ".format(ex))