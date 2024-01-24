from typing import Optional
from fastapi import Depends, HTTPException, status, APIRouter
from host_app.common.response_object import ResponseObject
from host_app.database.schemas import UserInDB, UserDelete, UserUpdate
from sqlalchemy.orm import Session
import logging
from host_app.database import crud, models
from host_app.database.database import get_db
from host_app.caching import redis_util
from host_app.routes import verification
from host_app.common.exceptions import CustomException, Exceptions
from host_app.common import common_util, service_util
from fastapi.responses import JSONResponse


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
4. verify any user under his org by its user_id - [Done]
5. Update any user details under his org - [done]
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

while updating anything, will add org_user_id + admin org that will ensure damn

'''


@service_router.get("/me/")
async def get_admin(admin: UserInDB = Depends(verification.get_current_active_user)):
    try:
        is_admin = await check_admin_privileges(admin, admin["user_id"]) 

        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__()) 
        
        return JSONResponse(status_code=200, content=ResponseObject(data=admin).to_dict())
    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in get_admin] {} ".format(ex))


# Not done
# possible_update users ["email", "phone", "username", "is_verified"]  
@service_router.post("/update/{org_user_id}")
async def update_user_data(org_user_id:str, user_data: UserUpdate, admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        admin_id = user_data.user_id
        is_admin =  await check_admin_privileges(admin) 

        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__()) 

        user_update_map_info = dict()
        res = await common_util.update_account_info(org_user_id, user_update_map_info)
        respObj.set_status(status.HTTP_200_OK)
        respObj.set_data(res)

        return respObj

    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in update_user] {} ".format(ex))

# own data update
@service_router.post("/update/")
async def update_user_data(admin_data: UserUpdate, admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        admin_id = admin_data.user_id
        is_admin =  await check_admin_privileges(admin, admin_id) 

        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__()) 

        user_update_map_info = dict()
        res = await common_util.update_account_info(admin_id, user_update_map_info)
        respObj.set_status(status.HTTP_200_OK)
        respObj.set_data(res)

        return respObj

    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in update_user] {} ".format(ex))


# -- 
@service_router.get("/verify/{user_id}")
async def verify_user_under_org(user_id: str, admin: UserInDB = Depends(verification.get_current_active_user),  db: Session = Depends(get_db)):
    try:
        is_admin = await check_admin_privileges(admin)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        if user_id[:2] != admin["service_org"]:
            return JSONResponse(status_code=401, content=CustomException(detail=f" User - {user_id} Not from your Org").__repr__()) 

        res = await service_util.verify_user(user_id, db)
        if res :
            return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict()) 

    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in verify_user_under_org] {} ".format(ex))


# not done - His own password of account 
@service_router.post("/updatepassword/")
async def update_admin_password(user_data : UserUpdate, admin: UserInDB = Depends(verification.get_current_active_user)):
    try:
        if admin["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        return  await common_util.update_password(admin, user_data.password, user_data.new_password)

    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in update_user_password] {} ".format(ex))


# Service admin can Update - ip_ports - his own
@service_router.post("/updateipports/")
async def update_ip_ports(user_data : UserUpdate, admin: UserInDB = Depends(verification.get_current_active_user)):
    try:
        # will work
        return {"message" : "under construction"}
    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in update_user_password] {} ".format(ex))

    
@service_router.post("/delete/", summary="To delete any user", description=" To delete any user from the org")
async def delete_user(user_data : UserDelete, admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = admin["user_id"]
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
        logging.exception("[SERVICE_ROUTES][Exception in delete_user] {} ".format(ex))


# ------------- 
@service_router.get("/getalluser/")
async def get_all_user_under_org(admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if admin["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        org = admin["service_org"] 
        res = await crud.get_all_users(db, org)
        return res

    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_all_user_under_org] {} ".format(ex))

    
@service_router.get("/getunverifiedusers/")
async def get_all_un_verified_users_under_org(admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if admin["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        org = admin["service_org"] 
        res = await crud.get_all_unverified_users(db, org)
        return res

    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_all_user_under_org] {} ".format(ex))


@service_router.get("/getallorders/")
async def get_all_orders_under_org(admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if admin["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        org = admin["service_org"] 
        res = await crud.get_all_orderss(db, org)
        return res

    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_all_orders_under_org] {} ".format(ex))



@service_router.get("/getordersbyuser/")
async def get_orders_by_user_under_org(admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if admin["role"] != models.Account.Role.ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        org = admin["service_org"] 
        res = await crud.get_all_orders_by_user(db, org)
        return res

    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_orders_by_user_under_org] {} ".format(ex))


# get any order
# get any user 
# update any order


async def check_admin_privileges(admin: dict, org_user: Optional[dict] = None):
    try:
        exp = Exceptions.NOT_AUTHORIZED
        if admin["role"] != models.Account.Role.ADMIN or admin["user_id"][:2] != admin["service_org"]:
            return exp
        
        return True

    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in check_admin_privileges] {} ".format(ex))


