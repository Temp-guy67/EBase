import logging, secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer,APIKeyHeader
from host_app.common import util
from fastapi import Depends, Request
from host_app.common.constants import SECRET_KEY, ALGORITHM
from typing import Annotated, Optional
import jwt, jwt.exceptions
from host_app.database.database import get_db
from host_app.common.exceptions import Exceptions, CustomException
from host_app.common import common_util
from host_app.common.constants import APIConstants, ServiceParameters
from host_app.caching import redis_util
from host_app.database import crud, schemas
from host_app.common.constants import ServiceParameters

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
security = HTTPBearer()
api_key_from_header = APIKeyHeader(name=ServiceParameters.X_API_KEY)


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
        

# async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], req: Request, db: Session = Depends(get_db)):
async def get_current_user(req: Request, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)], api_key : str = Depends(api_key_from_header), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        user_id_ip_details = await redis_util.get_hm(token)
        logging.info("[VERIFICATION][received request for URI : {} | request_data : {} ]".format(req.url.path, user_id_ip_details) )

        if user_id_ip_details:
            # If from different ip or device check
            if user_id_ip_details["ip"] != req.client.host:
                return Exceptions.TRYING_FROM_DIFFERENT_DEVICE
            
            user_data = await common_util.get_user_details(user_id_ip_details["user_id"], db)
            if not user_data :
                return Exceptions.USER_NOT_FOUND
            elif user_data["active_state"] != 1 :
                return Exceptions.USER_HAS_BEEN_DELETED
            else:
                return user_data
                

        verification_result = await verify_api_key(db, api_key, req)
        if type(verification_result) != type(dict()) :
            return verification_result
        
        if not int(verification_result["is_service_verified"]) :
            return Exceptions.SERVICE_NOT_VERIFIED
        # Now will encrypt and get from DB 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            return Exceptions.FAILED_TO_VALIDATE_CREDENTIALS
        token_data = schemas.TokenData(email=email)

        db_user = crud.get_user_by_email(db=db, email=token_data.email)
        
        if not db_user :
            return Exceptions.USER_NOT_FOUND
            
        common_util.update_user_details_in_redis(db_user["user_id"], db_user)
        
        if int(db_user["is_verified"]) != 1 :
            return Exceptions.USER_NOT_VERIFIED
        return db_user
        
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_current_user] {} ".format(ex))
        return Exceptions.FAILED_TO_VALIDATE_CREDENTIALS


async def get_current_active_user(current_user: Annotated[schemas.UserInDB, Depends(get_current_user)]):
    return current_user


async def verify_api_key(db: Session, enc_api_key: str, req: Request, email: Optional[str] = None):
    try:
        client_ip = req.client.host
        api_key = await decrypt_enc_api_key(enc_api_key)
        if not api_key:
            return CustomException(detail=Exceptions.API_KEY_UNAVAILABLE)

        daily_req_left = None
        service_obj = await common_util.get_service_details(db, api_key) 
        
        # Only test method will be allowed 
        # basic one will have limited
        
        if service_obj :
            service_org = service_obj["service_org"]
            # if email and service_obj["registration_mail"] != email :
            #     return CustomException(detail=Exceptions.WRONG_API)
            
            ip_ports = service_obj["ip_ports"]

            # if "*" in ip_ports:
            #     logging.info("Sending all ip ok")
            # elif client_ip not in ip_ports:
            #     return CustomException(detail=Exceptions.WRONG_IP)
            
            daily_req_left = service_obj["daily_request_count"]
            is_service_verified = service_obj["is_verified"]

            if daily_req_left :
                await common_util.reduce_daily_req_counts(api_key, service_obj)

                return {"daily_req_left" : int(daily_req_left) - 1 , "is_service_verified" : is_service_verified, "service_org" : service_org}
            
            elif daily_req_left == "0" :
                return CustomException(detail=Exceptions.REQUEST_LIMIT_EXHAUSTED)
            
        return CustomException(detail=Exceptions.WRONG_API)
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in verify_api_key] {} ".format(ex))
    return CustomException(detail=Exceptions.CREDENTIAL_ERROR_EXCEPTION)
    

async def decrypt_enc_api_key(enc_api_key: str) -> str:
    try:
        enc_api_key = enc_api_key[APIConstants.ENC_API_PREFIX_LEN:]
        payload = jwt.decode(enc_api_key, SECRET_KEY, algorithms=[ALGORITHM])

        api_key: str = payload.get(ServiceParameters.X_API_KEY)
        return api_key

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in decrypt_enc_api_key] {} ".format(ex))


async def generate_api_key() -> str:
    try:
        api_key = secrets.token_urlsafe(32)
        return api_key

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_api_key] {} ".format(ex))


async def get_encrypted_api_key(api_key:str):
    try:
        encoded_api_key = jwt.encode({ServiceParameters.X_API_KEY: api_key}, SECRET_KEY, algorithm=ALGORITHM)
        return APIConstants.ENC_API_PREFIX + encoded_api_key

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_encrypted_api_key] {} ".format(ex))
    


