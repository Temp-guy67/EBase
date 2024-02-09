from typing import Optional
from host_app.common.exceptions import Exceptions
from host_app.database.schemas import OrderCreate, OrderQuery
from sqlalchemy.orm import Session
import logging, random, string
from host_app.database import order_crud
from host_app.caching import redis_util
from host_app.caching.redis_constant import RedisConstant


async def create_order(db: Session, user_id:str, service_org:str, order_info: OrderCreate):
    try:
        new_order = await order_crud.create_new_order(db, user_id, service_org, order_info)
        
        if new_order :
            redis_util.set_hm(RedisConstant.ORDER_OBJ + new_order["order_id"], new_order, 1800)
            await add_order_ids_in_redis(user_id, new_order["order_id"])
            redis_util.add_to_set(RedisConstant.USER_PRODUCT_SET + new_order["owner_id"], [new_order["product_id"]], 1800)

        return new_order
    
    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in create_order] {} ".format(ex))


async def add_order_ids_in_redis(user_id: str, order_id:str)-> None:
    try:
        user_order_ids = await redis_util.get_set(RedisConstant.USER_ORDERS_SET + user_id)
        if user_order_ids:
            redis_util.add_to_set(RedisConstant.USER_ORDERS_SET + user_id, [order_id])

        # if not in redis , then leave it . On next query it will be set
    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in add_order_ids_in_redis] {} ".format(ex))


async def get_all_order_id_by_user(db: Session, user_id: str, org: Optional[str] = None):
    order_ids = []
    try:
        user_order_ids = await redis_util.get_set(RedisConstant.USER_ORDERS_SET + user_id)
        if not user_order_ids:
            user_order_ids = await order_crud.get_all_order_id_by_user(db, user_id, org)
            redis_util.add_to_set(RedisConstant.USER_ORDERS_SET + user_id, user_order_ids)
            
        return user_order_ids
    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in get_all_orders_by_user] {} ".format(ex))
    
    return order_ids
    
    
    
async def get_all_orders(db: Session, user_id: str, org: Optional[str] = None):
    try :
        all_order_ids = await get_all_order_id_by_user(db, user_id, org)
        all_orders_obj = []
        
        for single_order_id in all_order_ids:
            single_order_obj = await get_single_order(db, single_order_id, user_id, org)
            all_orders_obj.append(single_order_obj)
        return all_orders_obj
        
    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in get_all_orders] {} ".format(ex))


async def get_single_order(db: Session, order_id:str, user_id: Optional[str] = None, org: Optional[str] = None):
    try:
        order_obj = await redis_util.get_hm(RedisConstant.ORDER_OBJ + order_id)
        
        if not order_obj :
            order_obj = await order_crud.get_order_by_order_id(db, user_id, order_id, org)
            redis_util.set_hm(RedisConstant.ORDER_OBJ + order_id, order_obj)
        return order_obj

    except Exception as ex:
        logging.exception("[ORDER_UTIL][Exception in get_single_order] {} ".format(ex))
    
    

async def update_order_object(db:Session, user_id:str, order_id:str, order_data:dict, service_org: Optional[str] = None):
    try:
        order_update_map = dict()
        
        possible_column_updates = ["order_status", "order_quantity", "delivery_address", "receivers_mobile", "payment_status"]
        
        for k,v in order_data.items():
            if k in possible_column_updates:
                order_update_map[k] = v
        
        updated_order_obj = await order_crud.update_order_status(db, user_id, order_id, order_update_map, service_org)
        
        if updated_order_obj :
            redis_util.set_hm(RedisConstant.ORDER_OBJ + order_id, updated_order_obj)
            
        return updated_order_obj
    except Exception as ex :
        logging.exception("[ORDER_UTIL][Exception in update_order_object] {} ".format(ex))
    

async def create_order_id(user_id : str, service_org:str):
    try :
        random_id = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(5)])
        order_id = user_id[5:] + service_org  + "_" + random_id
        return order_id
    
    except Exception as ex :
        logging.exception("[ORDER_UTIL][Exception in create_order_id] {} ".format(ex))
        
async def set_order_update_map(order_query: OrderQuery ):
    try:
        order_data = dict()
        possible_update = ["order_status", "order_quantity", "delivery_address", "receivers_mobile", "payment_status"]

        for k,v in order_query :
            if v and k in possible_update:
                if k == possible_update[0] :
                    if not 1<=v<=6 :
                        return Exceptions.UNAVAILABLE_ORDER_STATUS
                    
                elif k == possible_update[4] :
                    if not 1<=v<=3 :
                        return Exceptions.UNAVAILABLE_ORDER_STATUS
                order_data[k] = v 
        return order_data
    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in check_admin_privileges] {} ".format(ex))


async def get_all_products_bought(user_id: str):
    all_products_bought = await redis_util.get_set(RedisConstant.USER_PRODUCT_SET + user_id)
    return all_products_bought