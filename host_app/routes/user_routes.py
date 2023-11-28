from fastapi import Depends, HTTPException, status, Request, APIRouter
from host_app.database.schemas import UserSignUp, UserInDB, UserLogin, UserDelete, UserUpdate
from sqlalchemy.orm import Session
from host_app.database.sql_constants import ACCESS_TOKEN_EXPIRE_MINUTES, CommonConstants
from fastapi.security import OAuth2PasswordBearer
import jwt, jwt.exceptions
import logging
from datetime import timedelta
from host_app.database import crud
from host_app.database.database import get_db
from host_app.caching import redis_util
from host_app.common import util
from host_app.routes import verification


user_router = APIRouter(
    prefix='/user',
    tags=['user']
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


@user_router.get("/me/")
async def read_users_me(user: UserInDB = Depends(verification.get_current_active_user)):
    try:
        return user
    except Exception as ex:
        logging.exception("[MAIN][Exception in read_users_me] {} ".format(ex))


@user_router.post("/update/")
async def update_user(user_data : UserUpdate,user: UserInDB = Depends(verification.get_current_active_user),  db: Session = Depends(get_db)):
    try:
        user_id = user.id
        password = user_data.password
        # verify password and tell them if fails operation stops here with exception and also segregate update column here, we have restrictions while updating , user cant update user name and email except admin support
        password_obj = await crud.get_password_data(db, user_id)
        
        await verification.verify_password(password, password_obj.hashed_password, password_obj.salt)


        data = {"phone": "999000999"} 
        await crud.update_user(db, user_id, data)

    except Exception as ex:
        logging.exception("[MAIN][Exception in update_user] {} ".format(ex))



@user_router.post("/updatepassword/")
async def update_user_password(user_data : UserUpdate,user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]
        password = user_data.password
        password_obj = await crud.get_password_data(db, user_id)

        if await verification.verify_password(password, password_obj.hashed_password, password_obj.salt):
            new_password = user_data.new_password
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

    except Exception as ex:
        logging.exception("[MAIN][Exception in update_user_password] {} ".format(ex))
        
    

@user_router.post("/delete/")
async def delete_user(user_data : UserDelete, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]
        password = user_data.password
        password_obj = await crud.get_password_data(db, user_id)
        
        if await verification.verify_password(password, password_obj.hashed_password, password_obj.salt):
            res = crud.delete_user(db, user_id)
            if res :
                await redis_util.delete_from_redis(user_id)
                return  {"user_id" : user_id, "messege":"User has been Deleted Sucessfully"} 
            else:
                return {"user_id" : user_id, "messege":"Failed to delete user ; Contact Admin Team"} 
        else:
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password is wrong",
                headers={"WWW-Authenticate": "Bearer"}
            )

    except Exception as ex:
        logging.exception("[MAIN][Exception in delete_user] {} ".format(ex))