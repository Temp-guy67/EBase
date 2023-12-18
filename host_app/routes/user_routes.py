from fastapi import Depends, HTTPException, status, APIRouter
from host_app.database.schemas import UserInDB, UserDelete, UserUpdate
from sqlalchemy.orm import Session
from host_app.database.sql_constants import CommonConstants
import jwt, jwt.exceptions
import logging
from host_app.database import crud
from host_app.database.database import get_db
from host_app.caching import redis_util
from host_app.common import common_util
from host_app.routes import verification


user_router = APIRouter(
    prefix='/user',
    tags=['user']
)


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
        return  await common_util.update_password(user, user_data.password, user_data.new_password)
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