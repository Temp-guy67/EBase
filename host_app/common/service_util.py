import logging
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from host_app.common.exceptions import CustomException
from host_app.database import service_crud
from host_app.database.database import get_db
from host_app.common import common_util, order_util
from host_app.caching import redis_util
from host_app.caching.redis_constant import RedisConstant
from host_app.database import crud



# under supervision
async def update_service_info(service_id: int, service_update_data: dict, db: Session = Depends(get_db)):
    try:
        # service name and IP ports
        possible_update = ["service_name", "ip_ports"]
        service_update_map = dict()
        
        for k,v in service_update_data.items():
            if k in possible_update :
                if type(v) != str :
                    v = str(v)
                service_update_map[k] = v
        await service_crud.update_service_data(db, service_id, service_update_map)
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in update_service_info] {} ".format(ex))
        

async def verify_service(service_id: int, db: Session ):
    try:
        service_update_map = dict()
        service_update_map["is_verified"] = 1
        res = await service_crud.update_service_data(db, service_id, service_update_map)
        if res :
            await common_util.delete_api_cache_from_redis(res.api_key)
            return {"message" : "Service Updated"}
            
    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in update_service_info] {} ".format(ex))
        

async def verify_user(db: Session , user_id: int, updater: str, service_org : Optional[str] = None, is_sup : Optional[bool] = None ):
    try:
        account_update_map = dict()
        account_update_map["is_verified"] = 1
        res = await common_util.update_account_info(db, user_id, updater, account_update_map, service_org, is_sup) 
        return res   
            
    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in verify_user] {} ".format(ex))


# Only use it for verification
async def get_service_object(db: Session, email: str):
    try:
        service_obj = dict()
        # await delete_api_cache_from_redis(api_key)
        
        service_data_obj = await redis_util.get_hm(RedisConstant.SERVICE_API + email)
        
        if not service_data_obj :
            service_data_obj = service_crud.get_service_by_api_key(db, email)
            
            if not service_data_obj :
                return CustomException(detail="Service Info Not Available")

        # redis_util.set_str(RedisConstant.SERVICE_API + api_key, service_obj, 86400)
        
        return service_obj
    
    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in get_service_object] {} ".format(ex))



# admin and super admin magic 

async def get_all_users(db:Session, is_sup : Optional[bool] = None, service_org: Optional[str] = None):
    try:
        res = await crud.get_all_users(db, is_sup, service_org)
        return res

    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in get_all_users] {} ".format(ex))



async def get_all_unverified_users(db:Session, is_sup : Optional[bool] = None, service_org: Optional[str] = None):
    try:
        res = await crud.get_all_unverified_users(db, is_sup, service_org)
        return res

    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in get_all_users] {} ".format(ex))
    

async def get_user(db:Session, user_id : str, service_org: Optional[str] = None):
    try:
        res =  crud.get_user_by_user_id(db, user_id, service_org)
        return res

    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in get_all_users] {} ".format(ex))




async def get_single_order(db: Session, order_id: str, user_id: Optional[str] = None, service_org: Optional[str] = None):
    try:
        res = order_util.get_single_order(db, order_id, user_id, service_org)
        return res

    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in get_single_order] {} ".format(ex))
        

async def get_all_orders_by_user(db: Session, user_id: Optional[str] = None, service_org: Optional[str] = None):
    try:
        res = order_util.get_all_orders(db, user_id, service_org)
        return res

    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in get_single_order] {} ".format(ex))