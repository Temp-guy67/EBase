from fastapi import Depends, HTTPException, status, Request, APIRouter
from host_app.database.schemas import UserSignUp, UserLogin, ClientSignup
from sqlalchemy.orm import Session
from host_app.database.sql_constants import ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordBearer
import jwt, jwt.exceptions
import logging
from datetime import timedelta
from host_app.database import crud, client_dbutils
from host_app.database.database import get_db
from host_app.caching import redis_util
from host_app.common import util
from host_app.routes import verification


user_router = APIRouter(
    prefix='/public',
    tags=['public']
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
# Dependency

#====================================== USER ============================

@user_router.post("/signup")
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


@user_router.post("/login")
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


@user_router.post("/createclient")
async def sign_up(client: ClientSignup, db: Session = Depends(get_db)):
    try:
        db_client = client_dbutils.get_client_by_email(db=db, email=client.registration_mail)

        if db_client:
            return HTTPException(status_code=400, detail="Email already registered as Client")
        
        db_client = client_dbutils.get_client_by_service_initials(db, phone=client.service_initials)
        if db_client:
            return HTTPException(status_code=400, detail="Service Initials already registered")
        

        res = await client_dbutils.create_new_client(db=db, client=client)
        return res

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in sign_up] {} ".format(ex))


