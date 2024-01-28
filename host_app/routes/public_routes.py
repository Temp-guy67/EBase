from fastapi import Depends, HTTPException, status, Request, APIRouter
from host_app.common.exceptions import Exceptions, CustomException
from host_app.database.schemas import UserSignUp, UserLogin, ServiceSignup
from host_app.database import models
from sqlalchemy.orm import Session
from host_app.common.constants import ACCESS_TOKEN_EXPIRE_MINUTES, ServiceParameters
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
import logging
from fastapi.responses import JSONResponse
from datetime import timedelta
from host_app.database import crud, service_crud
from host_app.database.database import get_db
from host_app.common import common_util
from host_app.common.response_object import ResponseObject
from host_app.routes import verification


public_router = APIRouter(
    prefix='/public',
    tags=['public']
)

# Dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
api_key_from_header = APIKeyHeader(name=ServiceParameters.X_API_KEY)

@public_router.post("/signup")
async def sign_up(user: UserSignUp, req: Request, api_key : str = Depends(api_key_from_header), db: Session = Depends(get_db)):
    try:
        
        logging.info("Data received for Signup : {}".format(user))
    
        verification_result = await verification.verify_api_key(db, api_key, req)
        if type(verification_result) != type(dict()) :
            return JSONResponse(status_code=403,  headers=dict(), content=verification_result.__repr__())
        
        if not int(verification_result["is_service_verified"]) :
            return JSONResponse(status_code=401,  headers=dict(), content=verification_result.__repr__())

        if_account_existed = await check_if_account_existed(db=db, email=user.email, phone=user.phone)
        if(if_account_existed):
            return JSONResponse(status_code=401,  headers=dict(), content=CustomException(detail="{} ALREADY REGISTERED AS {}".format(if_account_existed[0], if_account_existed[1])).__repr__())

        res = await crud.create_new_user(db=db, user=user)
        if not res:
            return JSONResponse(status_code=401, headers=dict(),content=CustomException(detail=Exceptions.ACCOUNT_CREATION_FAILED).__repr__())
        
        response_obj = ResponseObject()  
        response_obj.set_data(res)
        return JSONResponse(status_code=200, headers=dict(),content=response_obj.to_dict())
    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in sign_up] {} ".format(ex))


@public_router.post("/login")
async def user_login(userlogin : UserLogin, req: Request, api_key : str = Depends(api_key_from_header), db: Session = Depends(get_db)):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: `required`
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    try:
        logging.info("Data received for Login : {}".format(userlogin.model_dump()))
        
        verification_result = await verification.verify_api_key(db, api_key, req, userlogin.email)
        if not isinstance(verification_result, dict) :
            return JSONResponse(status_code=403, headers=dict(), content=verification_result.__repr__())
        
        if not int(verification_result["is_service_verified"]) :
            return JSONResponse(status_code=401, headers=dict(), content=CustomException(detail=Exceptions.SERVICE_NOT_VERIFIED).__repr__())


        client_ip = req.client.host
        user_agent = req.headers.get("user-agent")
        
        db_user = crud.get_user_by_email_login(db, email=userlogin.email)
        if not db_user :
            return JSONResponse(status_code=401, headers=dict(), content=CustomException(detail="Account Does not exist").__repr__())
        
        account_obj = db_user[0][0]
        password_obj = db_user[0][1]
        
        user_obj = account_obj.to_dict()
        user_obj["client_ip"] = client_ip
        user_obj["user_agent"] = user_agent
        
        if user_obj["account_state"] != 1 :
            return JSONResponse(status_code=401, headers=dict(), content=CustomException(detail="Account Does not exist").__repr__())

        if not account_obj:
            return JSONResponse(status_code=401, headers=dict(),content=CustomException(detail=Exceptions.USER_NOT_FOUND).__repr__())
        
        res = await verification.verify_password(userlogin.password, password_obj.hashed_password, password_obj.salt)

        if not res:
            return JSONResponse(status_code=401, headers=dict(),content=CustomException(detail=Exceptions.INCORRECT_EMAIL_PASSWORD).__repr__())
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = verification.create_access_token(
            data={"sub": userlogin.email}, expires_delta=access_token_expires
        )
        user_id = user_obj["user_id"]

        common_util.update_access_token_in_redis(user_id, access_token, client_ip)
        common_util.update_user_details_in_redis(user_id, user_obj)
        await common_util.delete_access_token_in_redis(user_id)
        
        headers = {"access_token": access_token, "token_type": "bearer"}
        response_obj = ResponseObject()  
        response_obj.set_data(user_obj)
        response_obj.set_daily_request_count_left(verification_result["daily_req_left"])

        return JSONResponse(status_code=200, headers=headers,content=response_obj.to_dict())

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in user_login] {} ".format(ex))


# =========================== SERVICES ==============================

@public_router.post("/createservice")
async def service_sign_up(service_user: ServiceSignup,  req :Request, db: Session = Depends(get_db)):
    try:
        logging.info("Data received for service_sign_up : {} ".format(service_user.model_dump()))
        responseObject = ResponseObject()
        service_email = service_user.registration_mail
        service_org = service_user.service_org

        is_service_existed = await check_if_service_existed(db=db, service_email=service_email, service_org=service_org)
        if(is_service_existed):
            return JSONResponse(status_code=401, content=CustomException(detail="{} ALREADY REGISTERED AS {}".format(is_service_existed[0], is_service_existed[1])).__repr__())

        if_account_existed = await check_if_account_existed(db=db, email=service_email, phone=service_user.phone)
        if(if_account_existed):
            return JSONResponse(status_code=401, content=CustomException(detail="{} ALREADY REGISTERED AS {}".format(if_account_existed[0], if_account_existed[1])).__repr__())

        # Service_res is already a dict
        user_signup_model = dict()
        user_signup_model["email"] = service_email
        user_signup_model["password"] = service_user.password
        user_signup_model["phone"] = service_user.phone
        user_signup_model["service_org"] = service_org
        user_signup_model["role"] = str(models.Account.Role.ADMIN)

        user_model = UserSignUp.model_validate(user_signup_model)

        service_res = await service_crud.create_new_service(db, req, service_user=service_user)
        user_res = await crud.create_new_user(db=db, user=user_model)

        data = {"Service_Account_Details" : service_res, "Admin_Account_Details" : user_res}
        responseObject.set_data(data)
    
        return JSONResponse(status_code=200, content=responseObject.to_dict())

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in service_sign_up] {} ".format(ex))



async def check_if_service_existed(db: Session, service_email : str, service_org : str):
    reason = []
    try:
        db_client = service_crud.if_service_cred_exist(db=db, email=service_email, service_org=service_org)

        if db_client:
            if db_client["service_org"] == service_org :
                reason.append(service_org)
                reason.append("SERVICE_ORG")
            elif db_client["registration_mail"] == service_email:
                reason.append(service_email)
                reason.append("SERVICE_EMAIL")

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in check_if_service_existed] {} ".format(ex))
    return reason


async def check_if_account_existed(db: Session, email : str, phone : str):
    reason = []
    try:
        db_client = crud.if_account_cred_exist(db=db, email=email, phone=phone)

        if db_client:
            if db_client["email"] == email :
                reason.append(email)
                reason.append("ACCOUNT_EMAIL")
            elif db_client["phone"] == phone:
                reason.append(phone)
                reason.append("ACCOUNT_PHONE")

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in check_if_account_existed] {} ".format(ex))
    return reason

