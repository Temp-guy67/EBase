from typing import Annotated
from fastapi import Depends, HTTPException, Header, status, Request, APIRouter
from host_app.caching.redis_constant import RedisConstant
from host_app.common.exceptions import Exceptions
from host_app.database.schemas import UserSignUp, UserLogin, ServiceSignup
from sqlalchemy.orm import Session
from host_app.database.sql_constants import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from fastapi.security import OAuth2PasswordBearer
import jwt, jwt.exceptions
import logging
from datetime import timedelta
from host_app.database import crud, service_crud
from host_app.database.database import get_db
from host_app.caching import redis_util
from host_app.common import util
from host_app.routes import verification


public_router = APIRouter(
    prefix='/public',
    tags=['public']
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
# Dependency

#====================================== USER ============================
# = Depends(verification.verify_api_key)
@public_router.post("/signup")
async def sign_up(user: UserSignUp, req: Request, db: Session = Depends(get_db)):
    try:

        verification_result = await verify_api_key(req)
        print(" TYPE OF VER RESULT ", type(verification_result))
        if verification_result != 1 :
            return verification_result

        print(" Lnaded in sign up ", user)
        db_user = crud.get_user_by_email(db=db, email=user.email)

        if db_user:
            return HTTPException(status_code=400, detail="Email already registered")
        
        db_user = crud.get_user_by_phone(db, phone=user.phone)
        if db_user:
            return HTTPException(status_code=400, detail="Mobile Number already registered")
        res = await crud.create_new_user(db=db, user=user)
        return res

    except Exception as ex :
        logging.exception("[MAIN][Exception in sign_up] {} ".format(ex))


@public_router.post("/login")
async def user_login(userlogin : UserLogin, req: Request, db: Session = Depends(get_db)):
    try:
        verification_result = await verification.verify_api_key(req)

        if verification_result != 1 :
            return verification_result

        client_ip = req.client.host
        user_agent = req.headers.get("user-agent")
        db_user = crud.get_user_by_email_login(db, email=userlogin.email)
        
        account_obj = db_user[0][0]
        password_obj = db_user[0][1]
        
        user_obj = await account_obj.to_dict()
        user_obj["client_ip"] = client_ip
        user_obj["user_agent"] = user_agent

        if not account_obj:
            return HTTPException(status_code=400, detail="User Not Available")
        
        res = await verification.verify_password( userlogin.password, password_obj.hashed_password, password_obj.salt)

        if not res:
            return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password",headers={"WWW-Authenticate": "Bearer"})
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = verification.create_access_token(
            data={"sub": userlogin.email}, expires_delta=access_token_expires
        )
        user_id = user_obj["user_id"]

        await redis_util.set_hm(user_id, user_obj)
        await redis_util.set_str(access_token, user_id)
        
        return {"access_token": access_token, "token_type": "bearer", "messege" : "Login Successful"}

    except Exception as ex :
        logging.exception("[MAIN][Exception in user_login] {} ".format(ex))


@public_router.post("/createservice")
async def service_sign_up(service_user: ServiceSignup, db: Session = Depends(get_db)):
    try:
        db_client = service_crud.get_service_by_email(db=db, email=service_user.registration_mail)

        if db_client:
            return HTTPException(status_code=400, detail="Email already registered as Service Owner")
        
        db_client = service_crud.get_service_by_service_org(db, service_org=service_user.service_org)
        if db_client:
            return HTTPException(status_code=400, detail="Service ORG already registered")
        

        res = await service_crud.create_new_service(db=db, service_user=service_user)
        return res

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in service_sign_up] {} ".format(ex))


async def verify_api_key(req: Request, db: Session = Depends(get_db)):
    try:
        client_ip = req.client.host
        user_agent = req.headers.get("user-agent")
        enc_api_key = req.headers.get("api_key")
        print("HEADER : ", client_ip , user_agent, enc_api_key)
        
        payload = jwt.decode(enc_api_key, SECRET_KEY, algorithms=[ALGORITHM])

        api_key: str = payload.get("api_key")
        
        print(" API Key : ", api_key)

        ip_ports_set = None
        daily_req_left = None

        need_to_update_redis = False

        if await redis_util.is_exists(api_key + RedisConstant.SERVICE_ID):
            ip_ports_set = await redis_util.get_str(api_key + RedisConstant.IP_PORTS_SET)

            daily_req_left = await redis_util.get_str(api_key + RedisConstant.DAILY_REQUEST_LEFT)

            is_service_verified = await redis_util.get_str(api_key + RedisConstant.IS_SERVICE_VERIFIED)


        else :

            service_obj = await service_crud.get_service_by_api_key(db=db, api_key=api_key)
            need_to_update_redis = True

            if service_obj:
                ip_ports_str = service_obj.ip_ports
                ip_ports_list = util.unzipper(ip_ports_str)
                
                if not client_ip in ip_ports_list :
                    return Exceptions.WRONG_API

                daily_req_left = service_obj.daily_request_counts
                is_service_verified = service_obj.is_verified

                redis_util.set_str(api_key + RedisConstant.DAILY_REQUEST_LEFT, daily_req_left - 1, 86400) 
                redis_util.set_str(api_key + RedisConstant.IS_SERVICE_VERIFIED, is_service_verified, 86400) 

                for ip_port in ip_ports_list:
                    await redis_util.add_to_set_str_val(api_key + RedisConstant.IP_PORTS_SET, ip_port, 86400)


        if daily_req_left :
            redis_util.set_str(api_key + RedisConstant.DAILY_REQUEST_LEFT, daily_req_left - 1, 86400)  # for one day
            return {"ip_ports_set": ip_ports_set, "daily_req_left" : daily_req_left- 1 , "is_service_verified" : is_service_verified }
        elif daily_req_left == 0 :
            return Exceptions.REQUEST_LIMIT_EXHAUST 

        
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in verify_api_key] {} ".format(ex))
    return Exceptions.CREDENTIAL_ERROR_EXCEPTION