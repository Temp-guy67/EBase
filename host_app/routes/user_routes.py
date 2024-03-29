from fastapi import Depends, APIRouter, Request
from host_app.common.exceptions import CustomException, Exceptions
from host_app.common.response_object import ResponseObject
from host_app.database.schemas import UserInDB, UserDelete, UserPasswordChange, UserUpdate
from sqlalchemy.orm import Session
import logging
from fastapi.responses import JSONResponse
from host_app.database import crud
from host_app.database.database import get_db
from host_app.common import common_util
from host_app.routes import verification
from host_app.caching import redis_constant, redis_util


user_router = APIRouter(
    prefix='/user',
    tags=['user']
)


@user_router.get("/me/", summary="To get profile details")
async def read_users_me(user: UserInDB = Depends(verification.get_current_active_user)):
    """
    Profile Details:
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)
    - **X-Access-Token**: `required` in Header (Just put your token you got by Login response header. that in authorize box on top right)

    *Body:*
    - Nothing

    *Response:*
    - Response Body :
        **User Object or any issue detected**
    """
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=user).to_dict())
    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in read_users_me] {} ".format(ex))


@user_router.post("/update/", summary="To Update user details : email, phone_no and username")
async def update_user(user_data : UserUpdate, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    """
    To Update Profile Details:
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)
    - **X-Access-Token**: `required` in Header (Just put your token you got by Login response header. that in authorize box on top right)

    *Body:*
    - **password**: `required`
    - **email**: Optional - if you want to update mail, then only
    - **username**: Optional - if you want to update username, then only
    - **phone**: Optional - if you want to update phone, then only


    *Response:*
    - Response Body :
        **Success Response or any issue**
    """
    
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        logging.info("Data received for update_user : {} | action user_id : {}".format(user_data, user["user_id"]))

        if user["service_org"] == "TT":
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.NO_UPDATE_FOR_TEST_ORG_RULE).__repr__()) 

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
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.OPERATION_FAILED + " | " +res).__repr__()) 

        return JSONResponse(status_code=200,content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in update_user] {} | user_id {}".format(ex, user["user_id"]))


@user_router.post("/updatepassword/", summary="To Update user Password")
async def update_user_password(user_data : UserPasswordChange, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    """
    To Update Password :
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)
    - **X-Access-Token**: `required` in Header (Just put your token you got by Login response header. that in authorize box on top right)

    *Body:*
    - **password**: `required`
    - **new_password**: Optional - if you want to update password then only

    *Response:*
    - Response Body :
        **Success Response or any issue and a mail for updating password {check spam folder}**
    """
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        user_id = user["user_id"]
        logging.info("Data received for update_user_password : {} | action user_id : {}".format(user_data, user_id))
        old_password, new_password = user_data.password, user_data.new_password

        if user["service_org"] == "TT":
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.NO_UPDATE_FOR_TEST_ORG_RULE).__repr__()) 

        if(not old_password or not new_password):
            return JSONResponse(status_code=401, headers=dict(), content=CustomException(detail="Provide both Old and new password").__repr__()) 
        
        password_obj = await crud.get_password_data(db, user_id)

        is_password_verified = await verification.verify_password(old_password, password_obj.hashed_password, password_obj.salt)

        if not is_password_verified:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.WRONG_PASSWORD).__repr__())  

        res = await common_util.update_password(user, new_password, db)

        if type(res) != type(dict()):
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail= Exceptions.OPERATION_FAILED + " | " + res).__repr__())
        
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())
    
    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in update_user_password] {} | user_id {}".format(ex, user["user_id"]))
        

@user_router.post("/delete/", summary="To Delete user Account")
async def delete_user(user_data : UserDelete, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    """
    To Delete User Account :
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)
    - **X-Access-Token**: `required` in Header (Just put your token you got by Login response header. that in authorize box on top right)

    *Body:*
    - **password**: `required`

    *Response:*
    - Response Body :
        **Success Response or any issue**
    """
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        logging.info("Data received for delete_user : {}".format(user["user_id"]))

        # Extra Check
        if user["service_org"] == "TT":
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.NO_UPDATE_FOR_TEST_ORG_RULE).__repr__()) 

        user_id, user_org, password = user["user_id"], user["service_org"], user_data.password
        password_obj = await crud.get_password_data(db, user_id)
        is_password_verified = await verification.verify_password(password, password_obj.hashed_password, password_obj.salt)
        
        if not is_password_verified:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.WRONG_PASSWORD).__repr__()) 
            
        res = await common_util.delete_user(user_id, user_org, db)
        if type(res) != type(dict()):
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.OPERATION_FAILED + " | " + res).__repr__())
        
        # await common_util.delete_access_token_in_redis(user_id)
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())
    
        
    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in delete_user] {} ".format(ex))


@user_router.get("/logout/", summary="To Logout current Session")
async def logout(req: Request, user: UserInDB = Depends(verification.get_current_active_user)):
    """
    To Logout current Session:
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)
    - **X-Access-Token**: `required` in Header (Just put your token you got by Login response header. that in authorize box on top right)

    *Body:*
    - Nothing

    *Response:*
    - Response Body :
        **Success Response or any issue**
    """
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        user_id = user["user_id"]
        logging.info("Request received for logout | action user_id : {}".format(user_id))

        access_token = await redis_util.get_str(redis_constant.RedisConstant.USER_ACCESS_TOKEN + user_id)

        common_util.update_access_token_map_in_redis(user_id, access_token, req.client.host, "logout")

        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data={"details" : "Logout Successful"}).to_dict())

    except Exception as ex:
        logging.exception("[USER_ROUTES][Exception in logout] {} ".format(ex))
        
