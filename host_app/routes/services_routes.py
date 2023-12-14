from fastapi import Depends, HTTPException, status, APIRouter
from host_app.database.schemas import UserInDB, UserDelete, UserUpdate
from sqlalchemy.orm import Session
from host_app.database.sql_constants import CommonConstants
import jwt, jwt.exceptions
import logging
from host_app.database import crud, models
from host_app.database.database import get_db
from host_app.caching import redis_util
from host_app.common import util
from host_app.routes import verification
from host_app.common.exceptions import Exceptions


service_router = APIRouter(
    prefix='/service',
    tags=['service']
)


'''
What an Admin can do is : 

1. Update his details, update password, update his ip (max three)

2. get all users under his org - [Done]
    2.1. get any user by user id - [Done]
3. get all unverified user under his org - [Done]
4. verify any user under his org by its user_id
5. Update any user details under his org
6. delete any user from his org

7. register for new api key - [ apply only]
    7.1 : request for new plan - [ apply only]
8. register for account deletion - [apply only]
    All his data will be provided to him

    
9. check all the order made from his org - [Done]
10. check all the orders made by any user from his org - [Done]
11. check any order by order id under his org
12. delete any order by order id under his org
13. Update any order details of user under his org
14. Create order only for his own

[cant create order from any other user POV]
'''


@service_router.get("/me/")
async def get_admin(user: UserInDB = Depends(verification.get_current_active_user)):
    try:
        if user["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        return user
    except Exception as ex:
        logging.exception("[MAIN][Exception in read_users_me] {} ".format(ex))


@service_router.post("/update/")
async def update_user_data(user_data : UserUpdate, user: UserInDB = Depends(verification.get_current_active_user),  db: Session = Depends(get_db)):
    try:
        if user["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        user_id = user.id
        password = user_data.password
        # verify password and tell them if fails operation stops here with exception and also segregate update column here, we have restrictions while updating , user cant update user name and email except admin support
        password_obj = await crud.get_password_data(db, user_id)
        
        await verification.verify_password(password, password_obj.hashed_password, password_obj.salt)

        data = {"phone": "999000999"} 
        await crud.update_user(db, user_id, data)

    except Exception as ex:
        logging.exception("[MAIN][Exception in update_user] {} ".format(ex))



@service_router.post("/updatepassword/")
async def update_admin_password(user_data : UserUpdate,user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
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
        
    

@service_router.post("/delete/")
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


# ------------- 

@service_router.get("/getalluser/")
async def get_all_user_under_org(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        org = user["service_org"] 
        res = await crud.get_all_users(db, org)
        return res

    except Exception as ex :
        logging.exception("[MAIN][Exception in get_all_user_under_org] {} ".format(ex))

    
@service_router.get("/getunverifiedusers/")
async def get_all_unverified_user_under_org(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        org = user["service_org"] 
        res = await crud.get_all_unverified_users(db, org)
        return res

    except Exception as ex :
        logging.exception("[MAIN][Exception in get_all_user_under_org] {} ".format(ex))


@service_router.get("/getallorders/")
async def get_all_orders_under_org(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        org = user["service_org"] 
        res = await crud.get_all_orderss(db, org)
        return res

    except Exception as ex :
        logging.exception("[MAIN][Exception in get_all_orders_under_org] {} ".format(ex))



@service_router.get("/getordersbyuser/")
async def get_orders_by_user_under_org(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        org = user["service_org"] 
        res = await crud.get_all_orders_by_user(db, org)
        return res

    except Exception as ex :
        logging.exception("[MAIN][Exception in get_orders_by_user_under_org] {} ".format(ex))




# ----------- write from here


@service_router.get("/getunverifiedusers/")
async def get_all_unverified_user_under_org(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        org = user["service_org"] 
        res = await crud.get_all_unverified_users(db, org)
        return res

    except Exception as ex :
        logging.exception("[MAIN][Exception in get_all_user_under_org] {} ".format(ex))