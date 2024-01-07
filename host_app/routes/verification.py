import logging, secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordBearer,HTTPBearer,APIKeyHeader
from host_app.common import util
from fastapi import status, Depends, HTTPException, Request
from host_app.database.sql_constants import SECRET_KEY, ALGORITHM
from typing import Annotated
import jwt, jwt.exceptions
from host_app.database.database import get_db
from host_app.common.exceptions import Exceptions, CustomException
from host_app.common import common_util
from host_app.database.sql_constants import APIConstants
from host_app.caching import redis_util
from host_app.database import crud, schemas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
security = HTTPBearer()
api_key_from_header = APIKeyHeader(name="api_key")


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
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate Token Credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        # print(" Token receoved ", token)
        verification_result = await verify_api_key(api_key, req, db)
        if type(verification_result) != type(dict()) :
            return verification_result
        
        if not int(verification_result["is_service_verified"]) :
            return Exceptions.SERVICE_NOT_VERIFIED

        user_id_from_token_map = await redis_util.get_str(token)

        if user_id_from_token_map:
            user_data = await redis_util.get_hm(user_id_from_token_map)
            if user_data :
                return user_data

        # Now will encrypt and get from DB 
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


async def verify_api_key(enc_api_key: str, req: Request, db: Session):
    try:
        client_ip = req.client.host
        api_key = await decrypt_enc_api_key(enc_api_key)
        if not api_key:
            return CustomException(detail="Add api_key in the header")

        daily_req_left = None
        service_obj = await common_util.get_service_details(db, api_key) 
        
        if service_obj :
            ip_ports = service_obj["ip_ports"]

            if "*" in ip_ports:
                logging.info("Sending all ip ok")
            elif client_ip not in ip_ports:
                return Exceptions.WRONG_IP
            
            daily_req_left = service_obj["daily_request_count"]
            is_service_verified = service_obj["is_verified"]

            if daily_req_left :
                await common_util.reduce_daily_req_counts(api_key, service_obj)
                return {"daily_req_left" : int(daily_req_left) - 1 , "is_service_verified" : is_service_verified}
            
            elif daily_req_left == "0" :
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
    


