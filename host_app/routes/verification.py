import logging, secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from host_app.common import util
from fastapi import Header, status, Depends, HTTPException, Request
from host_app.database.sql_constants import SECRET_KEY, ALGORITHM
from typing import Annotated
import jwt, jwt.exceptions
from host_app.database.database import get_db
from host_app.common.exceptions import Exceptions

from host_app.caching import redis_util
from host_app.caching.redis_constant import RedisConstant
from host_app.database import crud, schemas,service_crud

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

async def verify_password(user_password: str, hashed_password : str, salt : str):
    try:
        if hashed_password and salt and user_password :
            temp_hashed_password = await util.create_hashed_password(user_password, salt)
            return temp_hashed_password == hashed_password
        else :
            return False

    except Exception as ex:
        logging.exception("[VERIFICATION][Exception in verify_password] {} ".format(ex))


def create_access_token(data: dict, expires_delta: timedelta):
    try :
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in create_access_token] {} ".format(ex))
        


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], req: Request, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:

        verification_result = await verify_api_key(req, db)
        if type(verification_result) != type(dict()) :
            return verification_result
        
        if not int(verification_result["is_service_verified"]) :
            return Exceptions.SERVICE_NOT_VERIFIED

        user_id_from_token_map = await redis_util.get_str(token)
        print(" REQUEST thing ", req.client.host)

        if user_id_from_token_map:
            user_data = await redis_util.get_hm(user_id_from_token_map)
            logging.info(" GOt user_data MAP from token map : {} ".format(user_data))
            if user_data :
                return user_data
            else :
                print(" ELSE CASE Huser_routerENING ")


        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)

        db_user = crud.get_user_by_email(db=db, email=token_data.email)
        if db_user is None:
            raise credentials_exception
        
        db_data = await db_user.to_dict()
        await redis_util.set_hm(db_user.user_id, db_data, 1800)
        return db_data
        
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_current_user] {} ".format(ex))
        raise credentials_exception


async def get_current_active_user(current_user: Annotated[schemas.UserInDB, Depends(get_current_user)]):
    return current_user


async def verify_api_key(req: Request, db: Session):
    try:

        client_ip = req.client.host
        user_agent = req.headers.get("user-agent")
        enc_api_key = req.headers.get("api_key")

        api_key = await decrypt_enc_api_key(enc_api_key)

        ip_ports_set = None
        daily_req_left = None
        # await delete_api_cache_from_redis()
        need_to_update_redis = False

        if await redis_util.is_exists(api_key + RedisConstant.SERVICE_ID):
            print(" checking in redis")
            ip_ports_set = await redis_util.get_str(api_key + RedisConstant.IP_PORTS_SET)

            daily_req_left = await redis_util.get_str(api_key + RedisConstant.DAILY_REQUEST_LEFT)
            daily_req_left = int(daily_req_left)

            is_service_verified = await redis_util.get_str(api_key + RedisConstant.IS_SERVICE_VERIFIED)

        else :
            service_obj = service_crud.get_service_by_api_key(db=db, api_key=api_key)
            need_to_update_redis = True
           

            if service_obj:
                ip_ports_str = service_obj.ip_ports
                ip_ports_list = await util.unzipper(ip_ports_str)

                service_id = service_obj.service_id
                if not client_ip in ip_ports_list :
                    return Exceptions.WRONG_IP

                daily_req_left = service_obj.daily_request_counts
                is_service_verified = service_obj.is_verified

                redis_util.set_str(api_key + RedisConstant.IS_SERVICE_VERIFIED, str(is_service_verified), 86400) 

                redis_util.set_str(api_key + RedisConstant.SERVICE_ID, service_id , 86400)

                for ip_port in ip_ports_list:
                    await redis_util.add_to_set_str_val(api_key + RedisConstant.IP_PORTS_SET, ip_port, 86400)


        if daily_req_left :
            redis_util.set_str(api_key + RedisConstant.DAILY_REQUEST_LEFT, str(daily_req_left - 1), 86400)  # for one day
            return {"ip_ports_set": ip_ports_set, "daily_req_left" : daily_req_left- 1 , "is_service_verified" : is_service_verified }
        elif daily_req_left == 0 :
            return Exceptions.REQUEST_LIMIT_EXHAUST 

        
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in verify_api_key] {} ".format(ex))
    return Exceptions.CREDENTIAL_ERROR_EXCEPTION
    


async def decrypt_enc_api_key(enc_api_key: str) -> str:
    try:
        payload = jwt.decode(enc_api_key, SECRET_KEY, algorithms=[ALGORITHM])

        api_key: str = payload.get("api_key")
        return api_key

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in decrypt_enc_api_key] {} ".format(ex))




async def get_api_key() -> str:
    try:
        api_key = secrets.token_urlsafe(32)
        return api_key

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_api_key] {} ".format(ex))


#Boat : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGlfa2V5IjoiTjRPUWdzMGNnWlRYMTBwRTdNdEpveGxLYWY1eEhLdnhfQWtVZHhJcm50VSJ9.wGxmrPHsSD4w_JDKcfN0fBjl9HjWQn6vkZf6qxhSpqo


async def get_encrypted_api_key(api_key:str, ip_ports: list):
    try:
        encoded_api_key = jwt.encode({'api_key': api_key}, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_api_key

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_encrypted_api_key] {} ".format(ex))
    


async def delete_api_cache_from_redis():
    try:
        api_key = "N4OQgs0cgZTX10pE7MtJoxlKaf5xHKvx_AkUdxIrntU"
        await redis_util.delete_from_redis(api_key + RedisConstant.IP_PORTS_SET)
        await redis_util.delete_from_redis(api_key + RedisConstant.DAILY_REQUEST_LEFT)
        await redis_util.delete_from_redis(api_key + RedisConstant.SERVICE_ID)
        await redis_util.delete_from_redis(api_key + RedisConstant.IS_SERVICE_VERIFIED)
        print(" Deleted all the cache")

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in delete_api_cache_from_redis] {} ".format(ex))