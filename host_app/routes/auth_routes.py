from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.responses import JSONResponse
from host_app.common.exceptions import CustomException, Exceptions
from host_app.common.response_object import ResponseObject
from host_app.database.schemas import UserInDB, UserUpdate
from sqlalchemy.orm import Session
import logging
from host_app.database import crud, models
from host_app.database.database import get_db
from host_app.routes import verification
from host_app.common import util, service_util
from host_app.logs import log_manager

auth_router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


@auth_router.get("/verify/service/{service_id}")
async def verify_service(service_id : str, super_admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        is_sup_admin = await check_sup_admin_privileges(super_admin)
        
        if not isinstance(is_sup_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=is_sup_admin).__repr__())  
            
        res = await service_util.verify_service(service_id, db)
        if res :
            return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict())
    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in verify_service] {} ".format(ex))



@auth_router.get("/verify/user/{user_id}")
async def verify_user(user_id : str, super_admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        print( " super admin ",super_admin)
        is_sup_admin = await check_sup_admin_privileges(super_admin)
        if not isinstance(is_sup_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_sup_admin}").__repr__())  
            
        res = await service_util.verify_user(db, user_id, super_admin["user_id"], None, True)
        if res :
            return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict()) 
    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in verify_user] {} ".format(ex))


@auth_router.get("/logs")
async def read_logs(super_admin: UserInDB = Depends(verification.get_current_active_user)):
    is_sup_admin = await check_sup_admin_privileges(super_admin)
    if not isinstance(is_sup_admin, bool):
        return JSONResponse(status_code=401, content=CustomException(detail=f"is_SuperAdmin : {is_sup_admin}").__repr__())  
    res = await log_manager.read_logs()
    return res


# Untested ----------------------

@auth_router.get("/allorders")
async def get_all_orders(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] == models.Account.Role.SUPER_ADMIN :
            return await crud.get_all_orders(db)
        else :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to this Action",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except Exception as ex :
        logging.exception("[MAIN][Exception in get_all_order] {} ".format(ex))


@auth_router.get("/allusers")
async def get_all_user(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] == models.Account.Role.SUPER_ADMIN or user["role"] == models.Account.Role.ADMIN:
            return await crud.get_all_users(db)
        else :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to this Action",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except Exception as ex :
        logging.exception("[MAIN][Exception in get_all_userA] {} ".format(ex))


@auth_router.post("/updateuser/")
async def update_user_role(info: UserUpdate, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not (int(user["role"]) == models.Account.Role.SUPER_ADMIN or int(user["role"]) == models.Account.Role.ADMIN) :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to this Action",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        opr = info.opr 
        if not opr :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Opr param missing",
                headers={"WWW-Authenticate": "Bearer"}
            )

        admin_id = user["user_id"]
        password_obj = await crud.get_password_data(db, admin_id)

        if not (await util.verify_password(info.password, password_obj.hashed_password, password_obj.salt)) :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                messege="You are not authorized to this Action | Password is Wrong",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user_id = info.user_id 
        role = info.new_role
        success_msg = None
        response = {}

        if opr == "role_update":
            new_role = None
            if models.Account.Role.USER == role :
                new_role = models.Account.Role.USER
            if models.Account.Role.ADMIN == role :
                new_role = models.Account.Role.ADMIN
            if models.Account.Role.SUPER_ADMIN == role :
                new_role = models.Account.Role.SUPER_ADMIN

            if new_role:
                update_info_map = {"role" : new_role}
                success_msg = "Role updated successfully"

        elif opr == "verify_user":
            update_info_map = {"is_verified" : models.Account.Verification.VERIFIED}
            success_msg = "User has been verified successfully"

        if update_info_map :
            res = await crud.update_account_data(db, user_id, update_info_map)
            if res :
                content = {"status":"200OK", "user_id" : user_id, "messege" : success_msg}
                return content

    except Exception as ex :
        logging.exception("[MAIN][Exception in verify_user] {} ".format(ex))
        
        

async def check_sup_admin_privileges(super_admin : dict):
    try:
        if super_admin["role"] != models.Account.Role.SUPER_ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        return True

    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in check_sup_admin_privileges] {} ".format(ex))
        
        
        
        
from typing import Optional
from fastapi import Depends, APIRouter
from host_app.common.response_object import ResponseObject
from host_app.database.schemas import OrderQuery, UserInDB, UserDelete, UserUpdate
from sqlalchemy.orm import Session
import logging
from host_app.database import crud, models
from host_app.database.database import get_db
from host_app.routes import verification
from host_app.common.exceptions import CustomException, Exceptions
from host_app.common import common_util, service_util, order_util
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
async def get_admin(admin_data: UserInDB = Depends(verification.get_current_active_user)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        user_id = admin_data["user_id"]
        logging.info(f"Data received for get_admin : {user_id}")
        is_admin = await check_admin_privileges(admin_data) 

        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__()) 
        
        return JSONResponse(status_code=200, content=ResponseObject(data=admin_data).to_dict())
    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in get_admin] {} ".format(ex))


@service_router.post("/update/{org_user_id}")
async def update_user_data(org_user_id: str, update_data: UserUpdate, admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        admin_id = admin_data["user_id"]
        logging.info("Data received for update_user_data : {} | action user_id : {}".format(org_user_id, admin_id))
    
        is_admin =  await check_admin_privileges(admin_data) 
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__()) 

        user_update_map = await common_util.update_map_set(update_data)
    
        if not user_update_map :
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="Nothing to Update").__repr__()) 
        
        res = await common_util.update_account_info(db, org_user_id, admin_id, user_update_map, admin_data["service_org"])
        if not res :
            return JSONResponse(status_code=401, content=CustomException(detail="Operation Failed").__repr__()) 

        return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in update_user_data] {} ".format(ex))

# own data update
@service_router.post("/update/")
async def update_admin_account_data(update_data: UserUpdate, admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        print("  ")
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        admin_id = admin_data["user_id"]
        is_admin =  await check_admin_privileges(admin_data) 

        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__()) 

        user_update_map = await common_util.update_map_set(update_data)
        
        if not user_update_map :
            return JSONResponse(status_code=401, content=CustomException(detail="Nothing to Update").__repr__()) 
        
        res = await common_util.update_account_info(db, admin_id, admin_id, user_update_map, admin_data["service_org"])
        if not res :
            return JSONResponse(status_code=401, content=CustomException(detail="Operation Failed").__repr__()) 

        return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in update_admin_account_data] {} ".format(ex))


@service_router.get("/verify/user/{org_user_id}")
async def verify_user_under_org(org_user_id: str, admin_data: UserInDB = Depends(verification.get_current_active_user),  db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        res = await service_util.verify_user(db, org_user_id, admin_data["user_id"], admin_data["service_org"])
        if res :
            return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict()) 

    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in verify_user_under_org] {} ".format(ex))


# not done - His own password of account 
@service_router.post("/updatepassword/")
async def update_admin_password(update_data : UserUpdate, admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        admin_id = admin_data["user_id"]
        logging.info("Data received for update_admin_password :  admin_id : {}".format(admin_id))
        old_password, new_password = update_data.password, update_data.new_password

        if(not old_password or not new_password):
            return JSONResponse(status_code=401, headers=dict(), content=CustomException(detail="Provide both Old and new password").__repr__()) 
        
        password_obj = await crud.get_password_data(db, admin_id)

        is_password_verified = await verification.verify_password(old_password, password_obj.hashed_password, password_obj.salt)

        if not is_password_verified:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.WRONG_PASSWORD).__repr__())  

        res = await common_util.update_password(admin_data, new_password, db)
        if type(res) != type(dict()):
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=res).__repr__())
        
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in update_user_password] {} ".format(ex))


# Service admin can Update - ip_ports - his own
@service_router.post("/update/ipports/{ipports}")
async def update_ip_ports(user_data : UserUpdate, admin_data: UserInDB = Depends(verification.get_current_active_user)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        # will work
        return {"message" : "under construction"}
    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in update_user_password] {} ".format(ex))

    
@service_router.post("/delete/{org_user_id}", summary="To delete any user")
async def delete_user(org_user_id : str, extra_data : UserDelete, admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        logging.info("Data received for delete_user : user_id {} action user_id : {}".format(org_user_id, admin_data["user_id"]))

        admin_id, admin_org, admin_password = admin_data["user_id"], admin_data["service_org"], extra_data.password
        
        password_obj = await crud.get_password_data(db, admin_id)
        is_password_verified = await verification.verify_password(admin_password, password_obj.hashed_password, password_obj.salt)
        
        if not is_password_verified:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.WRONG_PASSWORD).__repr__()) 
            
        res = await common_util.delete_user(org_user_id, admin_org, db)
        if type(res) != type(dict()):
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=res).__repr__())
        
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[SERVICE_ROUTES][Exception in delete_user] {} ".format(ex))


# ------------- 
@service_router.get("/getalluser/")
async def get_all_user_under_org(admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        logging.info("Data received for get_all_user_under_org | admin user_id : {}".format(admin_data["user_id"]))
        res = await service_util.get_all_users(db, admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="No User found").__repr__())
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_all_user_under_org] {} ".format(ex))

    
@service_router.get("/getalluser/unverified")
async def get_all_unverified_users_under_org(admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        logging.info("Data received for get_all_unverified_users_under_org : admin user_id : {}".format(admin_data["user_id"]))
        res = await service_util.get_all_unverified_users(db, admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="No User found").__repr__())
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_all_unverified_users_under_org] {} ".format(ex))


@service_router.get("/getuser/{user_id}")
async def get_user_under_org(user_id:str, admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        logging.info("Data received for user_id : {} | admin user_id : {}".format(user_id, admin_data["user_id"]))
        res = await service_util.get_user(db, user_id, admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="No User Found").__repr__())
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_user_under_org] {} ".format(ex))


@service_router.get("/getorder/{order_id}")
async def get_order_under_org(order_id: str, admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        admin_id = admin_data["user_id"]
        logging.info("Data received for get_order_under_org | order_id : {} | admin user_id : {}".format(order_id, admin_id))
        res = await order_util.get_single_order(db, order_id, admin_id, admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="No Order Found").__repr__())
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())
    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_order_under_org] {} ".format(ex))


@service_router.get("/getallorder/")
async def get_all_orders_under_org(admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        print(" adin")
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        admin_id = admin_data["user_id"]
        logging.info("[service_routes][get_all_orders_under_org]Data received for get_all_orders_under_org | admin user_id : {}".format( admin_id))
        res = await order_util.get_all_orders(db, admin_id, admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401, content=CustomException(detail="No Order Found").__repr__())
        
        return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict())
    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_all_orders_under_org] {} ".format(ex))


@service_router.get("/getorder/user/{user_id}")
async def get_orders_by_user_under_org(user_id:str, admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        admin_id = admin_data["user_id"]
        logging.info("Data received for get_orders_by_user_under_org | admin user_id : {} | user_id {}".format(admin_id, user_id))
        res = await service_util.get_all_orders_by_user(db, user_id, admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401, content=CustomException(detail="No Order Found").__repr__())
        return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict())
    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in get_orders_by_user_under_org] {} ".format(ex))


@service_router.post("/order/update/{order_id}")
async def update_orders_by_user_under_org(order_id: str, order_query: OrderQuery, admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        admin_id = admin_data["user_id"]
        logging.info("Data received for update_orders_by_user_under_org | admin user_id : {} | order_id : {}".format(admin_id, order_id))
        
        order_data = await order_util.set_order_update_map(order_query)
        if not isinstance(order_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=order_data).__repr__())
        
        order_obj = await order_util.update_order_object(db, admin_id, order_id, order_data, admin_data["service_org"])
        if not order_obj:
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.OPERATION_FAILED).__repr__())
        
        return JSONResponse(status_code=200, content=ResponseObject(data={"message" : "Order Data Updated successfully"}).to_dict())
    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in update_orders_by_user_under_org] {} ".format(ex))


@service_router.get("/order/cancel/{order_id}")
async def cancel_orders_by_user_under_org(order_id: str, admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=admin_data).__repr__())
        
        is_admin = await check_admin_privileges(admin_data)
        if not isinstance(is_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Admin : {is_admin}").__repr__())  
        
        admin_id = admin_data["user_id"]
        logging.info("Data received for cancel_orders_by_user_under_org | admin user_id : {} | order_id : {}".format(admin_id, order_id))
        
        order_data = dict()
        order_data["order_status"] = models.Orders.OrderStatus.CANCELED
        order_obj = await order_util.update_order_object(db, admin_id, order_id, order_data, admin_data["service_org"])
        if not order_obj:
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.OPERATION_FAILED).__repr__())
        
        return JSONResponse(status_code=200, content=ResponseObject(data={"message" : "Order canceled successfully"}).to_dict())
    except Exception as ex :
        logging.exception("[SERVICE_ROUTES][Exception in cancel_orders_by_user_under_org] {} ".format(ex))



