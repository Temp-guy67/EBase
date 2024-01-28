from fastapi import Depends, HTTPException, status, APIRouter
from host_app.common.exceptions import CustomException, Exceptions
from host_app.common.response_object import ResponseObject
from host_app.database.schemas import UserInDB, UserDelete, UserUpdate
from sqlalchemy.orm import Session
import logging
from fastapi.responses import JSONResponse
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
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=user).to_dict())
    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in read_users_me] {} ".format(ex))


@user_router.post("/update/")
async def update_user(user_data : UserUpdate, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        logging.info("Data received for update_user : {} | action user_id : {}".format(user_data, user["user_id"]))

        if not user_data:
            return 
        user_id, password = user["user_id"], user_data.password

        password_obj = await crud.get_password_data(db, user_id)

        is_password_verified = await verification.verify_password(password, password_obj.hashed_password, password_obj.salt)

        if not is_password_verified :
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.WRONG_PASSWORD).__repr__())  
        
        user_update_map = await common_util.update_map_set(user_data)
        
        if not user_update_map :
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="Nothing to Update").__repr__()) 
            
        res = await common_util.update_account_info(db, user_id, user_id, user_update_map, user["service_org"])
        if type(res) != type(dict()):
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.OPERATION_FAILED).__repr__()) 

        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in update_user] {} | user_id {}".format(ex, user["user_id"]))


@user_router.post("/update/password/")
async def update_user_password(user_data : UserUpdate, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        user_id = user["user_id"]
        logging.info("Data received for update_user_password : {} | action user_id : {}".format(user_data, user_id))
        old_password, new_password = user_data.password, user_data.new_password

        if(not old_password or not new_password):
            return JSONResponse(status_code=401, headers=dict(), content=CustomException(detail="Provide both Old and new password").__repr__()) 
        
        password_obj = await crud.get_password_data(db, user_id)

        is_password_verified = await verification.verify_password(old_password, password_obj.hashed_password, password_obj.salt)

        if not is_password_verified:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.WRONG_PASSWORD).__repr__())  

        res = await common_util.update_password(user, new_password, db)

        if type(res) != type(dict()):
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=res).__repr__())
        
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())
    
    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in update_user_password] {} | user_id {}".format(ex, user["user_id"]))
        

@user_router.get("/delete/")
async def delete_user(user_data : UserDelete, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        logging.info("Data received for delete_user : {}".format(user["user_id"]))

        user_id, user_org, password = user["user_id"], user["service_org"], user_data.password
        password_obj = await crud.get_password_data(db, user_id)
        is_password_verified = await verification.verify_password(password, password_obj.hashed_password, password_obj.salt)
        
        if not is_password_verified:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.WRONG_PASSWORD).__repr__()) 
            
        res = await common_util.delete_user(user_id, user_org, db)
        if type(res) != type(dict()):
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=res).__repr__())
        
        await common_util.delete_access_token_in_redis(user_id)
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())
    
        
    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in delete_user] {} ".format(ex))


@user_router.get("/logout/")
async def logout(user: UserInDB = Depends(verification.get_current_active_user)):
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        user_id = user["user_id"]
        logging.info("Request received for logout | action user_id : {}".format(user_id))
        await common_util.delete_access_token_in_redis(user_id)
        
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data={"details" : "Logout Successful"}).to_dict())

    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in logout] {} ".format(ex))
        
