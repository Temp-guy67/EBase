from typing import Optional
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
from host_app.mail_manager.config import send_email_to_client
from host_app.routes import verification


public_router = APIRouter(
    prefix='/public',
    tags=['public']
)

# Dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
api_key_from_header = APIKeyHeader(name=ServiceParameters.X_API_KEY)

@public_router.post("/signup", summary="To Sign up in the system")
async def sign_up(user: UserSignUp, req: Request, api_key : str = Depends(api_key_from_header), db: Session = Depends(get_db)):
    """
    Sign in the system:
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)

    *Body:*
    - **email**: `required` - As we are providing Admin access too for presentation, we disble the email checks for now. Can use temporary mail services like 10mint mail (recommended)
    - **phone**: `required` - Please maintain 10 digits
    - **username**: Optional - Will be auto generated if not provided
    - **role**: Optional - Can avoid

    *Response:*
    - Response Body :
        **Password will be mailed, Use it for first login**
        **Newly created User Object**
        
    """
    try:
        
        logging.info("Data received for Signup : {}".format(user))
        verification_result = await verification.verify_api_key(db, api_key, req)
        if type(verification_result) != type(dict()) :
            return JSONResponse(status_code=403,  headers=dict(), content=verification_result.__repr__())
        
        if not int(verification_result["is_service_verified"]) :
            return JSONResponse(status_code=401,  headers=dict(), content=verification_result.__repr__())
        
        email=user.email
        phone = user.phone
        username = user.username
        user.role = 1

        # check = await email_validation_check(email)
        # if not check :
        #     return JSONResponse(status_code=401, content=CustomException(detail="INVALID EMAIL PATTERN, only accecpting gmail, outlook and hotmail").__repr__())
        
        check = await phone_validation_check(phone)
        if not check :
            return JSONResponse(status_code=401, content=CustomException(detail="INVALID PHONE NUMBER PATTERN").__repr__())

        if_account_existed = await check_if_account_existed(db=db, email=email, phone=phone, username=username)
        if(if_account_existed):
            return JSONResponse(status_code=401, headers=dict(), content=CustomException(detail="{} ALREADY REGISTERED AS {}".format(if_account_existed[0], if_account_existed[1])).__repr__())

        res = await crud.create_new_user(db=db, user=user, service_org=verification_result["service_org"])
        # Exceptions.ACCOUNT_CREATION_FAILED
        if not res:
            return JSONResponse(status_code=401, headers=dict(),content=CustomException(detail=res).__repr__())
        
        response_obj = ResponseObject()  
        response_obj.set_data(res)

        return JSONResponse(status_code=200,content=response_obj.to_dict())
    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in sign_up] {} ".format(ex))


@public_router.post("/login", summary="To login in the system")
async def user_login(userlogin : UserLogin, req: Request, api_key : str = Depends(api_key_from_header), db: Session = Depends(get_db)):
    """
    Login in the system:
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)

    *Body:*
    - **email**: `required`
    - **password**: `required`

    *Response:*
    - Response Body :
        **User Object** and 
        **Access Token** Will be valid upto 30 mints. `required` Must add in Header (Just put in authorize box on top right) for further use
        
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

        await common_util.delete_access_token_in_redis(user_id)
        
        common_util.update_access_token_in_redis(user_id, access_token, client_ip, "login")
        common_util.update_user_details_in_redis(user_id, user_obj)
        
        
        headers = {"access_token": access_token, "token_type": "bearer"}
        response_obj = ResponseObject()  
        response_obj.set_data(user_obj)
        response_obj.set_daily_request_count_left(verification_result["daily_req_left"])

        return JSONResponse(status_code=200, headers=headers,content=response_obj.to_dict())

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in user_login] {} ".format(ex))


# =========================== SERVICES ==============================

@public_router.post("/createservice", summary="To Create New Service")
async def service_sign_up(service_user: ServiceSignup, req :Request, db: Session = Depends(get_db)):
    """
    To Create New Service in the system:
    *Header:*
    - Nothing in Header (As of now)

    *Body:*
    - **service_org**: `required`
    - **service_name**: `required`
    - **phone**: `required`
    - **registration_mail**: `required`
    - **subscription_mode**: Optional - By Default TEST(20 api call daily limit)
    - **ip_ports**: Optional - List of IPs from where the service API will be valid for admins and Users under this org. By default your current api will be counted. `Though for the presentation, Its non operational now.`

    *Response:*
    - Response Body :
        **Password will be mailed, Use it for first login**
        **Newly created User Object**
    """
    try:
        logging.info("Data received for service_sign_up : {} ".format(service_user.model_dump()))
        responseObject = ResponseObject()
        service_email = service_user.registration_mail
        service_org = service_user.service_org
        
        org_check = await org_validation_check(service_org)
        if not org_check :
            return JSONResponse(status_code=401, content=CustomException(detail="INVALID ORG PATTERN, org must be of two letters only in Capital").__repr__())
        
        
        # check = await email_validation_check(service_email)
        # if not check :
        #     return JSONResponse(status_code=401, content=CustomException(detail="INVALID EMAIL PATTERN, only accecpting gmail, outlook and hotmail").__repr__())
        

        is_service_existed = await check_if_service_existed(db=db, service_email=service_email, service_org=service_org)
        if(is_service_existed):
            return JSONResponse(status_code=401, content=CustomException(detail="{} ALREADY REGISTERED AS {}".format(is_service_existed[0], is_service_existed[1])).__repr__())

        if_account_existed = await check_if_account_existed(db=db, email=service_email, phone=service_user.phone)
        if(if_account_existed):
            return JSONResponse(status_code=401, content=CustomException(detail="{} ALREADY REGISTERED AS {}".format(if_account_existed[0], if_account_existed[1])).__repr__())

        # Service_res is already a dict
        user_signup_model = dict()
        user_signup_model["email"] = service_email
        user_signup_model["phone"] = service_user.phone
        user_signup_model["service_org"] = service_org
        user_signup_model["role"] = str(models.Account.Role.ADMIN)

        user_model = UserSignUp.model_validate(user_signup_model)

        service_res = await service_crud.create_new_service(db, req, service_user=service_user)
        user_res = await crud.create_new_user(db=db, user=user_model, service_org=service_org)

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




# Helper method 


async def check_if_account_existed(db: Session, email : str, phone : str, username : Optional[str] = None):
    reason = []
    try:
        if username :
            db_client = crud.if_account_cred_exist(db=db, email=email, phone=phone, username=username)
        else :
            db_client = crud.if_account_cred_exist(db=db, email=email, phone=phone)

        if db_client:
            if db_client["email"] == email :
                reason.append(email)
                reason.append("ACCOUNT_EMAIL")
            elif db_client["phone"] == phone:
                reason.append(phone)
                reason.append("ACCOUNT_PHONE")
            elif db_client["username"] == username:
                reason.append(username)
                reason.append("ACCOUNT_USERNAME")

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in check_if_account_existed] {} ".format(ex))
    return reason


async def email_validation_check(email:str) -> bool:
    try:
        accepted_domain = ["gmail.com", "hotmail.com", "outlook.com"]
        x = email.split("@")
        if len(x) == 1 or x[1] not in accepted_domain:
            return False
        return True

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in email_validation_check] {} ".format(ex))
    return False

async def phone_validation_check(phone:str) -> bool:
    try:
        if len(phone) == 10 and phone.isdigit():
            return True
        return False

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in phone_validation_check] {} ".format(ex))
    return False

async def org_validation_check(org: str) -> bool:
    try:
        if len(org) == 2 and org.isupper():
            return True
        return False

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in phone_validation_check] {} ".format(ex))
    return False
