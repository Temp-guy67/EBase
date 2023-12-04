from fastapi import Depends, HTTPException, status, Request, APIRouter
from host_app.database.schemas import UserSignUp, UserLogin, ServiceSignup
from sqlalchemy.orm import Session
from host_app.database.sql_constants import ACCESS_TOKEN_EXPIRE_MINUTES
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

@public_router.post("/signup")
async def sign_up(user: UserSignUp, db: Session = Depends(get_db)):
    try:
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
        
        print(" Landed in create Service ", service_user.registration_mail)
        db_client = service_crud.get_service_by_email(db=db, email=service_user.registration_mail)

        if db_client:
            return HTTPException(status_code=400, detail="Email already registered as Service Owner")
        
        db_client = service_crud.get_service_by_service_org(db, service_org=service_user.service_org)
        if db_client:
            return HTTPException(status_code=400, detail="Service ORG already registered")
        

        res = await service_crud.create_new_service(db=db, service_user=service_user)
        print(" RES RECEVED IN PUBLIC ROUTES : " , res)
        return res

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in service_sign_up] {} ".format(ex))


