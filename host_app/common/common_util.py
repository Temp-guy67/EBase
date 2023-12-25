import logging
from host_app.database.sql_constants import CommonConstants
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from host_app.caching import redis_util
from host_app.caching.redis_constant import RedisConstant
from host_app.database import crud, service_crud
from host_app.database.database import get_db
from host_app.common import util
from host_app.routes import verification
from host_app.common.exceptions import Exceptions, CustomException


def update_access_token_in_redis(user_id:str, access_token: str):
    try :
        redis_util.set_str(access_token, user_id, 1800)
        # For logout cases only
        redis_util.set_str(user_id, access_token, 1800)

    except Exception as ex :
        logging.exception("[common_util][Exception in update_access_token_in_redis] {} ".format(ex))


async def update_user_details_in_redis(user_id:str, user_obj: dict):
    try :
        await redis_util.set_hm(RedisConstant.USER_OBJECT + user_id, user_obj, 1800)

    except Exception as ex :
        logging.exception("[common_util][Exception in update_user_details_in_redis] {} ".format(ex))


async def get_user_details(user_id, db: Session = Depends(get_db)):
    try :
        user_details = await redis_util.get_hm(RedisConstant.USER_OBJECT + user_id)
        if not user_details :
            user_details = crud.get_user_by_user_id(db,user_id)

        return user_details

    except Exception as ex :
        logging.exception("[common_util][Exception in get_user_details] {} ".format(ex))

        

async def update_password(user:dict, password, new_password, db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]
        password_obj = await crud.get_password_data(db, user_id)

        if await verification.verify_password(password, password_obj.hashed_password, password_obj.salt):

            new_salt = await util.generate_salt(CommonConstants.SALT_LENGTH)
            new_hashed_password = await util.create_hashed_password(new_password, new_salt)
            data = {"salt": new_salt, "hashed_password" : new_hashed_password} 
            res = await crud.update_password_data(db, user_id, data)
            if res :
                await redis_util.delete_from_redis(user_id)
                
            return {"user_id" : user_id, "messege":"Password has been Updated Sucessfully"}
        else :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password is wrong",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as ex :
        logging.exception("[common_util][Exception in update_password] {} ".format(ex))
             
        
async def delete_api_cache_from_redis(api_key: str):
    try:
        await redis_util.delete_from_redis(RedisConstant.IP_PORTS_SET + api_key )
        await redis_util.delete_from_redis(RedisConstant.DAILY_REQUEST_LEFT + api_key)
        await redis_util.delete_from_redis( RedisConstant.SERVICE_ORG + api_key )
        await redis_util.delete_from_redis(RedisConstant.IS_SERVICE_VERIFIED + api_key)
    
        
        print(" Deleted all the cache")

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in delete_api_cache_from_redis] {} ".format(ex))


async def add_api_cache_to_redis(api_key: str,service_id: str, daily_req_left: int, is_service_verified: int, ip_ports_list: list):
    try:
        redis_util.set_str(api_key + RedisConstant.IS_SERVICE_VERIFIED, str(is_service_verified), 86400) 

        redis_util.set_str(api_key + RedisConstant.SERVICE_ID, service_id , 86400)

        for ip_port in ip_ports_list:
            await redis_util.add_to_set_str_val(api_key + RedisConstant.IP_PORTS_SET, ip_port, 86400)
            
        if daily_req_left > 0 :
            redis_util.set_str(api_key + RedisConstant.DAILY_REQUEST_LEFT, str(daily_req_left - 1), 86400)
        print(" Data added in Redis [Service Id]" ,service_id )

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in delete_api_cache_from_redis] {} ".format(ex))
        
        

# Common update, it will update anything literally except password and return a boolean 
# But reaching upto here is fuckin impossible without proper authentication.


async def update_account_info(user_id: int, user_update_map_info: dict, db: Session = Depends(get_db)):
    try:
        # username, email and phone
        user_update_map = dict()
        possible_update = ["email", "phone", "username" , "is_verified"]
        
        for k,v in user_update_map_info.items():
            if k == possible_update[0]:
                res = crud.get_user_by_email()
                if res :
                    return Exceptions.EMAIL_HAS_BEEN_REGISTERED
                
            if k == possible_update[1]:
                res = crud.get_user_by_phone()
                if res :
                    return Exceptions.PHONE_NUMBER_HAS_BEEN_REGISTERED
            if k in possible_update :
                user_update_map[k] = v
        
        updated_user_data = await crud.update_account_data(db, user_id, user_update_map)
        
        if updated_user_data :
            update_user_details_in_redis(user_id, updated_user_data)
            return 1
        else :
            return -1
        
        
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in update_account_info] {} ".format(ex))
        

# Only use it for verification
async def get_service_details(db: Session, api_key: str):
    try:
        service_obj = dict()
        # await delete_api_cache_from_redis(api_key)
        
        service_data_obj = await redis_util.get_hm(RedisConstant.SERVICE_API + api_key)
        
        if not service_data_obj :
            service_data_obj = service_crud.get_service_by_api_key(db, api_key)
            
            if not service_data_obj :
                return CustomException(detail="Service Info Not Available", message="Check with you Service/API Provider")
            
        service_obj["service_org"] = service_data_obj["service_org"]
        service_obj["is_verified"] = service_data_obj["is_verified"]
        service_obj["daily_request_count"] = service_data_obj["daily_request_count"]
        service_obj["ip_ports"] = service_data_obj["ip_ports"]

        # redis_util.set_str(RedisConstant.SERVICE_API + api_key, service_obj, 86400)
        
        return service_obj
    
    except Exception as ex :
        logging.exception("[Common_Util][Exception in get_service_details] {} ".format(ex))


async def update_service_object_in_redis(api_key:str, service_obj:dict):
    await redis_util.set_hm(RedisConstant.SERVICE_API + api_key, service_obj, 86400)


async def reduce_daily_req_counts(api_key:str, service_obj:dict):
    service_obj["daily_request_count"] = str(int(service_obj["daily_request_count"]) - 1)
    await update_service_object_in_redis(api_key, service_obj)


async def update_service_verified_api(api_key:str, service_obj:dict):
    service_obj["is_verified"] = "1"
    await update_service_object_in_redis(api_key, service_obj)