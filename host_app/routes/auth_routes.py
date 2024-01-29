from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse
from host_app.common.exceptions import CustomException, Exceptions
from host_app.logs import log_manager
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


auth_router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

'''
Some Extra Method
1. All users under org
2. all orders Under Org
3. Update Service Data
4. Stop Service 

'''

@auth_router.get("/verify/service/{service_id}")
async def verify_service(service_id : str, super_admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin).__repr__())
        
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
        if not isinstance(super_admin, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin).__repr__())
        
        is_sup_admin = await check_sup_admin_privileges(super_admin)
        if not isinstance(is_sup_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_sup_admin}").__repr__())  
            
        res = await service_util.verify_user(db, user_id, super_admin["user_id"], None, True)
        if res :
            return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict()) 
    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in verify_user] {} ".format(ex))


@auth_router.get("/logs")
async def read_logs(super_admin: UserInDB = Depends(verification.get_current_active_user)):
    if not isinstance(super_admin, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin).__repr__())
    
    is_sup_admin = await check_sup_admin_privileges(super_admin)
    if not isinstance(is_sup_admin, bool):
        return JSONResponse(status_code=401, content=CustomException(detail=f"is_SuperAdmin : {is_sup_admin}").__repr__())  
    res = await log_manager.read_logs()
    return res


@auth_router.get("/me/")
async def get_super_admin(super_admin: UserInDB = Depends(verification.get_current_active_user)):
    try:
        if not isinstance(super_admin, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin).__repr__())
        
        user_id = super_admin["user_id"]
        logging.info(f"Data received for get_admin : {user_id}")
        is_super_admin = await check_sup_admin_privileges(super_admin) 

        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is super_admin : {is_super_admin}").__repr__()) 
        
        return JSONResponse(status_code=200, content=ResponseObject(data=super_admin).to_dict())
    except Exception as ex:
        logging.exception("[AUTH_ROUTES][Exception in get_super_admin] {} ".format(ex))


@auth_router.post("/update/{org_user_id}")
async def update_user_data(org_user_id: str, update_data: UserUpdate, super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        super_admin_id = super_admin_data["user_id"]
        logging.info("Data received for update_user_data : {} | action user_id : {}".format(org_user_id, super_admin_id))
    
        is_super_admin =  await check_sup_admin_privileges(super_admin_data) 
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__()) 

        user_update_map = await common_util.update_map_set(update_data)
    
        if not user_update_map :
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="Nothing to Update").__repr__()) 
        
        res = await common_util.update_account_info(db, org_user_id, super_admin_id, user_update_map, super_admin_data["service_org"])
        if not res :
            return JSONResponse(status_code=401, content=CustomException(detail="Operation Failed").__repr__()) 

        return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[AUTH_ROUTES][Exception in update_user_data] {} ".format(ex))


# own data update
@auth_router.post("/update/")
async def update_admin_account_data(update_data: UserUpdate, super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        print("  ")
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        super_admin_id = super_admin_data["user_id"]
        is_super_admin =  await check_sup_admin_privileges(super_admin_data) 

        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__()) 

        user_update_map = await common_util.update_map_set(update_data)
        
        if not user_update_map :
            return JSONResponse(status_code=401, content=CustomException(detail="Nothing to Update").__repr__()) 
        
        res = await common_util.update_account_info(db, super_admin_id, super_admin_id, user_update_map, super_admin_data["service_org"])
        if not res :
            return JSONResponse(status_code=401, content=CustomException(detail="Operation Failed").__repr__()) 

        return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[AUTH_ROUTES][Exception in update_admin_account_data] {} ".format(ex))


@auth_router.get("/verify/user/{org_user_id}")
async def verify_user(org_user_id: str, super_admin_data: UserInDB = Depends(verification.get_current_active_user),  db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        res = await service_util.verify_user(db, org_user_id, super_admin_data["user_id"], super_admin_data["service_org"])
        if res :
            return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict()) 

    except Exception as ex:
        logging.exception("[AUTH_ROUTES][Exception in verify_user] {} ".format(ex))


# not done - His own password of account  - will start from here
@auth_router.post("/updatepassword/")
async def update_super_admin_password(update_data : UserUpdate, super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        super_admin_id = super_admin_data["user_id"]
        logging.info("Data received for update_super_admin_password :  super_admin_id : {}".format(super_admin_id))
        old_password, new_password = update_data.password, update_data.new_password

        if(not old_password or not new_password):
            return JSONResponse(status_code=401, headers=dict(), content=CustomException(detail="Provide both Old and new password").__repr__()) 
        
        password_obj = await crud.get_password_data(db, super_admin_id)

        is_password_verified = await verification.verify_password(old_password, password_obj.hashed_password, password_obj.salt)

        if not is_password_verified:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.WRONG_PASSWORD).__repr__())  

        res = await common_util.update_password(super_admin_data, new_password, db)
        if type(res) != type(dict()):
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=res).__repr__())
        
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[AUTH_ROUTES][Exception in update_super_admin_password] {} ".format(ex))


# Super  admin can Update - ip_ports - his own
@auth_router.post("/update/ipports/{ipports}")
async def update_ip_ports(user_data : UserUpdate, super_admin_data: UserInDB = Depends(verification.get_current_active_user)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        # will work
        return {"message" : "under construction"}
    except Exception as ex:
        logging.exception("[AUTH_ROUTES][Exception in update_user_password] {} ".format(ex))

    
@auth_router.post("/delete/{org_user_id}", summary="To delete any user")
async def delete_user(org_user_id : str, extra_data : UserDelete, super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        logging.info("Data received for delete_user : user_id {} action user_id : {}".format(org_user_id, super_admin_data["user_id"]))

        super_admin_id, admin_org, admin_password = super_admin_data["user_id"], super_admin_data["service_org"], extra_data.password
        
        password_obj = await crud.get_password_data(db, super_admin_id)
        is_password_verified = await verification.verify_password(admin_password, password_obj.hashed_password, password_obj.salt)
        
        if not is_password_verified:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=Exceptions.WRONG_PASSWORD).__repr__()) 
            
        res = await common_util.delete_user(org_user_id, admin_org, db)
        if type(res) != type(dict()):
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail=res).__repr__())
        
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex:
        logging.exception("[AUTH_ROUTES][Exception in delete_user] {} ".format(ex))


# ------------- 
@auth_router.get("/getalluser/")
async def get_all_user_under_org(super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        logging.info("Data received for get_all_user_under_org | admin user_id : {}".format(super_admin_data["user_id"]))
        res = await service_util.get_all_users(db, super_admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="No User found").__repr__())
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in get_all_user_under_org] {} ".format(ex))

    
@auth_router.get("/getalluser/unverified")
async def get_all_unverified_users_under_org(super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        logging.info("Data received for get_all_unverified_users_under_org : admin user_id : {}".format(super_admin_data["user_id"]))
        res = await service_util.get_all_unverified_users(db, super_admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="No User found").__repr__())
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in get_all_unverified_users_under_org] {} ".format(ex))


@auth_router.get("/getuser/{user_id}")
async def get_user_under_org(user_id:str, super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        logging.info("Data received for user_id : {} | admin user_id : {}".format(user_id, super_admin_data["user_id"]))
        res = await service_util.get_user(db, user_id, super_admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="No User Found").__repr__())
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())

    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in get_user_under_org] {} ".format(ex))


@auth_router.get("/getorder/{order_id}")
async def get_order_under_org(order_id: str, super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        super_admin_id = super_admin_data["user_id"]
        logging.info("Data received for get_order_under_org | order_id : {} | admin user_id : {}".format(order_id, super_admin_id))
        res = await order_util.get_single_order(db, order_id, super_admin_id, super_admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="No Order Found").__repr__())
        return JSONResponse(status_code=200, headers=dict(),content=ResponseObject(data=res).to_dict())
    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in get_order_under_org] {} ".format(ex))


@auth_router.get("/getallorder/")
async def get_all_orders_under_org(super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        print(" adin")
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        super_admin_id = super_admin_data["user_id"]
        logging.info("[AUTH_ROUTES][get_all_orders_under_org]Data received for get_all_orders_under_org | admin user_id : {}".format( super_admin_id))
        res = await order_util.get_all_orders(db, super_admin_id, super_admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401, content=CustomException(detail="No Order Found").__repr__())
        
        return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict())
    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in get_all_orders_under_org] {} ".format(ex))


@auth_router.get("/getorder/user/{user_id}")
async def get_orders_by_user_under_org(user_id:str, super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        super_admin_id = super_admin_data["user_id"]
        logging.info("Data received for get_orders_by_user_under_org | admin user_id : {} | user_id {}".format(super_admin_id, user_id))
        res = await service_util.get_all_orders_by_user(db, user_id, super_admin_data["service_org"])
        if not res:
            return JSONResponse(status_code=401, content=CustomException(detail="No Order Found").__repr__())
        return JSONResponse(status_code=200, content=ResponseObject(data=res).to_dict())
    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in get_orders_by_user_under_org] {} ".format(ex))


@auth_router.post("/order/update/{order_id}")
async def update_orders_by_user_under_org(order_id: str, order_query: OrderQuery, super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        super_admin_id = super_admin_data["user_id"]
        logging.info("Data received for update_orders_by_user_under_org | admin user_id : {} | order_id : {}".format(super_admin_id, order_id))
        
        order_data = await order_util.set_order_update_map(order_query)
        if not isinstance(order_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=order_data).__repr__())
        
        order_obj = await order_util.update_order_object(db, super_admin_id, order_id, order_data, super_admin_data["service_org"])
        if not order_obj:
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.OPERATION_FAILED).__repr__())
        
        return JSONResponse(status_code=200, content=ResponseObject(data={"message" : "Order Data Updated successfully"}).to_dict())
    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in update_orders_by_user_under_org] {} ".format(ex))


@auth_router.get("/order/cancel/{order_id}")
async def cancel_orders_by_user_under_org(order_id: str, super_admin_data: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        if not isinstance(super_admin_data, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=super_admin_data).__repr__())
        
        is_super_admin = await check_sup_admin_privileges(super_admin_data)
        if not isinstance(is_super_admin, bool):
            return JSONResponse(status_code=401, content=CustomException(detail=f"Is Super Admin : {is_super_admin}").__repr__())  
        
        super_admin_id = super_admin_data["user_id"]
        logging.info("Data received for cancel_orders_by_user_under_org | admin user_id : {} | order_id : {}".format(super_admin_id, order_id))
        
        order_data = dict()
        order_data["order_status"] = models.Orders.OrderStatus.CANCELED
        order_obj = await order_util.update_order_object(db, super_admin_id, order_id, order_data, super_admin_data["service_org"])
        if not order_obj:
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.OPERATION_FAILED).__repr__())
        
        return JSONResponse(status_code=200, content=ResponseObject(data={"message" : "Order canceled successfully"}).to_dict())
    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in cancel_orders_by_user_under_org] {} ".format(ex))



async def check_sup_admin_privileges(super_admin : dict):
    try:
        if super_admin["role"] != models.Account.Role.SUPER_ADMIN :
            return Exceptions.NOT_AUTHORIZED
        
        return True

    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in check_sup_admin_privileges] {} ".format(ex))