import logging
from typing import Optional
from host_app.common.constants import CommonConstants
from fastapi import Depends
from sqlalchemy.orm import Session
from host_app.caching import redis_util
from host_app.database.schemas import UserUpdate
from host_app.caching.redis_constant import RedisConstant
from host_app.database import crud, service_crud
from host_app.database.database import get_db
from host_app.common import util
from host_app.common.exceptions import Exceptions, CustomException
from host_app.mail_manager.config import send_email_to_client


def update_access_token_in_redis(user_id:str, access_token: str, ip: str):
    try :
        data_map = {"user_id" : user_id, "ip" : ip}
        redis_util.set_hm(access_token, data_map, 1800)
        redis_util.set_str(RedisConstant.USER_ACCESS_TOKEN + user_id, access_token, 1800)

    except Exception as ex :
        logging.exception("[common_util][Exception in update_access_token_in_redis] {} ".format(ex))


async def delete_access_token_in_redis(user_id : str):
    try:
        access_token = await redis_util.get_str(RedisConstant.USER_ACCESS_TOKEN + user_id)
        if access_token :
            redis_util.delete_from_redis(access_token)
            redis_util.delete_from_redis(RedisConstant.USER_ACCESS_TOKEN + user_id)

    except Exception as ex :
        logging.exception("[common_util][Exception in delete_access_token_in_redis] {} ".format(ex))


def update_user_details_in_redis(user_id:str, user_obj: dict):
    try :
        redis_util.set_hm(RedisConstant.USER_OBJECT + user_id, user_obj, 1800)

    except Exception as ex :
        logging.exception("[common_util][Exception in update_user_details_in_redis] {} ".format(ex))


async def get_user_details(user_id, db: Session = Depends(get_db)):
    try :
        user_details = await redis_util.get_hm(RedisConstant.USER_OBJECT + user_id)
        if not user_details :
            user_details = crud.get_user_by_user_id(db,user_id)
        return user_details if user_details else Exceptions.USER_NOT_FOUND

    except Exception as ex :
        logging.exception("[common_util][Exception in get_user_details] {} ".format(ex))

async def delete_user_details_from_redis(user_id:str):
    redis_util.delete_from_redis(RedisConstant.USER_OBJECT + user_id)
    
        
async def update_password(user:dict, new_password, db: Session):
    try:
        logging.info(f"[update_password][Data received][user] {user}")
        user_id = user["user_id"]

        new_salt = await util.generate_salt(CommonConstants.SALT_LENGTH)
        new_hashed_password = await util.create_hashed_password(new_password, new_salt)
        data = {"salt": new_salt, "hashed_password" : new_hashed_password} 
        res = await crud.update_password_data(db, user_id, data)

        if res :
            await delete_user_details_from_redis(user_id)
            await  delete_access_token_in_redis(user_id)
            
            # user_map = {"username" : user["username"], "email" : user["email"]}
            # send_email_to_client(2, user_map)
            
            return {"user_id" : user_id, "messege":"Password has been Updated Sucessfully"}

    except Exception as ex :
        logging.exception("[common_util][Exception in update_password] {} ".format(ex))
             

# Common update, it will update anything literally except password and return a boolean 
# But reaching upto here is fuckin impossible without proper authentication.


async def update_account_info(db: Session, user_id: str, updater:str, user_update_map_info: dict, service_org: Optional[str] = None, is_sup : Optional[bool] = None):
    data = {}
    try:
        logging.info(f"[update_account_info][Data received][targetUser] {user_id} [updater] {updater} [Update details] {user_update_map_info}")
        user_update_map = dict()
        
        possible_update = ["email", "phone", "username", "is_verified"]
        
        for k,v in user_update_map_info.items():
            if k == possible_update[0]:
                res = crud.get_user_by_email(db, v)
                if res :
                    return Exceptions.EMAIL_HAS_BEEN_REGISTERED
                
            if k == possible_update[1]:
                res = crud.get_user_by_phone(db, v)
                if res :
                    return Exceptions.PHONE_NUMBER_HAS_BEEN_REGISTERED
                
            if k == possible_update[2]:
                res = crud.get_user_by_username(db, v)
                if res :
                    return Exceptions.USERNAME_HAS_BEEN_TAKEN

            if k in possible_update :
                user_update_map[k] = v
        
        updated_user_data = await crud.update_account_data(db, user_id, updater, user_update_map, service_org, is_sup)
        data = {"user_id" : user_id, "details" : "User Data updated successfully", "updated_by" : updater, "updated_data" : updated_user_data}
        if updated_user_data :
            update_user_details_in_redis(user_id, updated_user_data)

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in update_account_info] {} ".format(ex))
    return data
        

async def delete_user(user_id:str, user_org:str, db: Session):
    try:
        res = await crud.delete_user(db, user_id, user_org)
        # now delete from redis
        if not res :
            return Exceptions.OPERATION_FAILED
        data = {"user_id" : user_id, "details" : "User Data updated successfully"}
        await delete_user_details_from_redis(user_id)
        return data
        
    except Exception as ex :
        logging.exception("[Common_Util][Exception in delete_user] {} ".format(ex))


# Only use it for verification
async def get_service_details(db: Session, api_key: str):
    try:
        service_obj = dict()
        # await delete_api_cache_from_redis(api_key)
        
        service_data_obj = await redis_util.get_hm(RedisConstant.SERVICE_API + api_key)

        if not service_data_obj :
            service_data_obj = service_crud.get_service_by_api_key(db, api_key)
            
            if not service_data_obj :
                return CustomException(detail="Service Info Not Available")
            
        service_obj["service_org"] = service_data_obj["service_org"]
        service_obj["is_verified"] = service_data_obj["is_verified"]
        service_obj["daily_request_count"] = service_data_obj["daily_request_count"]
        service_obj["ip_ports"] = service_data_obj["ip_ports"]
        service_obj["registration_mail"] = service_data_obj["registration_mail"]

        redis_util.set_hm(RedisConstant.SERVICE_API + api_key, service_obj, 86400)
        
        return service_obj
    
    except Exception as ex :
        logging.exception("[Common_Util][Exception in get_service_details] {} ".format(ex))


async def update_service_object_in_redis(api_key:str, service_obj:dict):
    redis_util.set_hm(RedisConstant.SERVICE_API + api_key, service_obj, 86400)

async def delete_api_cache_from_redis(api_key:str):
    redis_util.delete_from_redis(RedisConstant.SERVICE_API + api_key)
    

async def reduce_daily_req_counts(api_key:str, service_obj:dict):
    service_obj["daily_request_count"] = str(int(service_obj["daily_request_count"]) - 1)
    await update_service_object_in_redis(api_key, service_obj)


async def update_service_verified_api(api_key:str, service_obj:dict):
    service_obj["is_verified"] = "1"
    await update_service_object_in_redis(api_key, service_obj)


async def update_map_set(user_data: UserUpdate):
    try:
        possible_update = ["email", "phone", "username"]
        user_data = (user_data.model_dump())
        user_update_map = dict()
        
        for k,v in user_data.items():
            if k in possible_update and v :
                user_update_map[k] = v
                
        return user_update_map
    except Exception as ex :
        logging.exception("[Common_Util][Exception in update_map_set] {} ".format(ex))

