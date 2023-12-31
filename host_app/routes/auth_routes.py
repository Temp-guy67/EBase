from fastapi import Depends, HTTPException, status, APIRouter
from host_app.database.schemas import UserInDB, UserUpdate
from sqlalchemy.orm import Session
import logging
from host_app.database import crud, models
from host_app.database.database import get_db
from host_app.routes import verification
from host_app.common import util, service_util

auth_router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


@auth_router.get("/verifyservice")
async def verify_service(super_admin: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        service_id = "BT_O766"
        await service_util.verify_service(service_id, db)

    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in verify_service] {} ".format(ex))



@auth_router.get("/verifyuser")
async def verify_user(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        pass
    except Exception as ex :
        logging.exception("[AUTH_ROUTES][Exception in verify_user] {} ".format(ex))




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