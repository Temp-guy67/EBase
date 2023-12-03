import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from host_app.common import util
from fastapi import status, Depends, HTTPException
from host_app.database.sql_constants import SECRET_KEY, ALGORITHM
from typing import Annotated
import jwt, jwt.exceptions
from host_app.database.database import get_db
import secrets

from host_app.caching import redis_util
from host_app.database import crud, schemas

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
        


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id_from_token_map = await redis_util.get_str(token)

        logging.info(" GOt user_id from token map : {} ".format(user_id_from_token_map))

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


async def get_api_key():
    try:
        api_key = secrets.token_urlsafe(32)
        return api_key

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_api_key] {} ".format(ex))

async def get_encrypted_api_key(api_key:str, ip_ports: list):
    try:
        encoded_api_key = jwt.encode({'api_key': api_key, 'ip_ports':ip_ports}, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_api_key

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_encrypted_api_key] {} ".format(ex))
    
        
async def decrypt_api_key(ip_ports: str):
    try:
        api_key = secrets.token_urlsafe(32)
        print(" API KEY : ", api_key)
        encoded_jwt = jwt.encode({'api_key': api_key, 'ip_ports':ip_ports}, SECRET_KEY, algorithm=ALGORITHM)
        return {'encrypted_api_key': encoded_jwt}

    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in get_api_key] {} ".format(ex))