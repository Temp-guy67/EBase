from fastapi import Depends, HTTPException, status, APIRouter
from host_app.common.exceptions import CustomException
from host_app.common.response_object import ResponseObject
from host_app.database.schemas import UserInDB, UserDelete, UserUpdate
from sqlalchemy.orm import Session
import logging
from host_app.database import crud
from host_app.database.database import get_db
from host_app.common import common_util
from host_app.routes import verification


user_router = APIRouter(
    prefix='/user',
    tags=['user']
)


@user_router.get("/me/")
async def read_users_me(user: UserInDB = Depends(verification.get_current_active_user)):
    try:
        responseObject = ResponseObject()
        responseObject.set_status(status.HTTP_200_OK)
        responseObject.set_data(user)
        
        return responseObject
    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in read_users_me] {} ".format(ex))


@user_router.post("/update/")
async def update_user(user_data : UserUpdate, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        responseObject = ResponseObject()
        user_id = user.id
        password = user_data.password
        password_obj = await crud.get_password_data(db, user_id)
        
        res = await verification.verify_password(password, password_obj.hashed_password, password_obj.salt)

        if not res :
            exp = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password is wrong",
                headers={"WWW-Authenticate": "Bearer"},
            )
            responseObject.set_exception(exp)
            return responseObject
        
        possible_update = ["email", "phone", "username"]

        for k,v in user_data :
            if v not in possible_update:
                del user_data[k]

        if not user_data:
            exp = CustomException(detail="Invalid parameters provided")

            responseObject.set_exception(exp)
            return responseObject
        

        res = await common_util.update_account_info(user_id, user_data)
        
        if res :
            if type(res) != type(dict()):
                responseObject.set_exception(res)
                return responseObject

            responseObject.set_status(status.HTTP_200_OK)
            responseObject.set_data(res)
            return responseObject

    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in update_user] {} ".format(ex))


@user_router.post("/updatepassword/")
async def update_user_password(user_data : UserUpdate, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        responseObject = ResponseObject()
        res = await common_util.update_password(user, user_data.password, user_data.new_password)

        if type(res) != type(dict()):
            responseObject.set_exception(res)
            return responseObject
        responseObject.set_status(status.HTTP_200_OK)
        responseObject.set_data(res)
        return responseObject
    
    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in update_user_password] {} ".format(ex))
        


@user_router.post("/delete/")
async def delete_user(user_data : UserDelete, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        responseObject = ResponseObject()
        user_id = user["user_id"]
        user_org = user["service_org"]
        password = user_data.password
        password_obj = await crud.get_password_data(db, user_id)
        
        is_password_verified = await verification.verify_password(password, password_obj.hashed_password, password_obj.salt)
        
        if not is_password_verified:
            exp = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password is wrong",
                headers={"WWW-Authenticate": "Bearer"},
            )
            responseObject.set_exception(exp)
            return responseObject
            
        res = await common_util.delete_user(user_id, user_org, db)
        if type(res) != type(dict()):
            responseObject.set_exception(res)
            return responseObject
        responseObject.set_status(status.HTTP_200_OK)
        responseObject.set_data(res)
        return responseObject

    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in delete_user] {} ".format(ex))


@user_router.post("/logout/")
async def delete_user(user: UserInDB = Depends(verification.get_current_active_user)):
    try:
        user_id = user["user_id"]
        await common_util.delete_access_token_in_redis(user_id)

    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in delete_user] {} ".format(ex))
        
