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
from host_app.common.exceptions import Exceptions, CustomException
from host_app.common import common_util
from host_app.database.sql_constants import APIConstants
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
        detail="Could not validate Token Credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:

        verification_result = await verify_api_key(req, db)
        if type(verification_result) != type(dict()) :
            return verification_result
        
        if not int(verification_result["is_service_verified"]) :
            return Exceptions.SERVICE_NOT_VERIFIED

        user_id_from_token_map = await redis_util.get_str(token)

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
        await common_util.update_user_details_in_redis(db_user.user_id, db_data)
        return db_data
        
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_current_user] {} ".format(ex))
        raise credentials_exception


async def get_current_active_user(current_user: Annotated[schemas.UserInDB, Depends(get_current_user)]):
    return current_user


async def verify_api_key(req: Request, db: Session):
    try:
        client_ip = req.client.host
        enc_api_key = req.headers.get("api_key")

        api_key = await decrypt_enc_api_key(enc_api_key)
        
        if not api_key:
            return CustomException(detail="Add api key in the header")

        ip_ports_set = None
        daily_req_left = None
        # await common_util.delete_api_cache_from_redis(api_key)

        service_obj = await common_util.get_service_details(db, api_key) 
        
        if service_obj :
            ip_ports = list(service_obj["ip_ports"])
            print("IP PORTS RECEIVED ", ip_ports)
            
            if client_ip not in ip_ports:
                return Exceptions.WRONG_IP
            
            daily_req_left = int(service_obj["daily_request_count"]) - 1
            is_service_verified = service_obj["is_verified"]

            if daily_req_left :
                common_util.update_daily_req_counts(api_key, daily_req_left)

                return {"daily_req_left" : daily_req_left , "is_service_verified" : is_service_verified}
            
            elif daily_req_left == 0 :
                return Exceptions.REQUEST_LIMIT_EXHAUSTED 
            
        return Exceptions.WRONG_API
        
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in verify_api_key] {} ".format(ex))
    return Exceptions.CREDENTIAL_ERROR_EXCEPTION
    


async def decrypt_enc_api_key(enc_api_key: str) -> str:
    try:
        enc_api_key = enc_api_key[APIConstants.ENC_API_PREFIX_LEN:]
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


async def get_encrypted_api_key(api_key:str):
    try:
        encoded_api_key = jwt.encode({'api_key': api_key}, SECRET_KEY, algorithm=ALGORITHM)
        return APIConstants.ENC_API_PREFIX + encoded_api_key

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_encrypted_api_key] {} ".format(ex))
    


