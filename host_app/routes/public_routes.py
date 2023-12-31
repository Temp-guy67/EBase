from fastapi import Depends, HTTPException, status, Request, APIRouter
from host_app.common.exceptions import Exceptions
from host_app.database.schemas import UserSignUp, UserLogin, ServiceSignup
from sqlalchemy.orm import Session
from host_app.database.sql_constants import ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordBearer
import logging
from datetime import timedelta
from host_app.database import crud, service_crud
from host_app.database.database import get_db
from host_app.common import common_util
from host_app.common.response_object import ResponseObject
from host_app.routes import verification
from host_app.database import models


public_router = APIRouter(
    prefix='/public',
    tags=['public']
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
# Dependency


@public_router.post("/signup")
async def sign_up(user: UserSignUp, req: Request, db: Session = Depends(get_db)):
    try:
        response_obj = ResponseObject()
        verification_result = await verification.verify_api_key(req, db)
        if type(verification_result) != type(dict()) :
            response_obj.set_status_and_exception(status.HTTP_403_FORBIDDEN, verification_result)
            return verification_result
        
        if not int(verification_result["is_service_verified"]) :
            response_obj.set_status_and_exception(status.HTTP_401_UNAUTHORIZED, Exceptions.SERVICE_NOT_VERIFIED)
            return Exceptions.SERVICE_NOT_VERIFIED

        db_user = crud.get_user_by_email(db=db, email=user.email)

        if db_user:
            response_obj.set_status_and_exception(status.HTTP_401_UNAUTHORIZED, HTTPException(status_code=400, detail="Email already registered"))
            return response_obj
        
        db_user = crud.get_user_by_phone(db, phone=user.phone)
        if db_user:
            response_obj.set_status_and_exception(status.HTTP_401_UNAUTHORIZED, HTTPException(status_code=400, detail="Mobile Number already registered"))
            return response_obj

        res = await crud.create_new_user(db=db, user=user)
        if res:
            response_obj.set_status(status.HTTP_200_OK)
            response_obj.set_data(res)
        
        return response_obj

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in sign_up] {} ".format(ex))


@public_router.post("/login")
async def user_login(userlogin : UserLogin, req: Request, db: Session = Depends(get_db)):
    try:
        response_obj = ResponseObject()
        verification_result = await verification.verify_api_key(req, db)
        
        if type(verification_result) != type(dict()) :
            response_obj.set_status_and_exception(status.HTTP_403_FORBIDDEN, verification_result)
            return response_obj
        
        if not int(verification_result["is_service_verified"]) :
            response_obj.set_status_and_exception(status.HTTP_401_UNAUTHORIZED, Exceptions.SERVICE_NOT_VERIFIED)
            return response_obj

        client_ip = req.client.host
        user_agent = req.headers.get("user-agent")
        db_user = crud.get_user_by_email_login(db, email=userlogin.email)
        
        account_obj = db_user[0][0]
        password_obj = db_user[0][1]
        
        user_obj = await account_obj.to_dict()
        user_obj["client_ip"] = client_ip
        user_obj["user_agent"] = user_agent

        if not account_obj:
            response_obj.set_status_and_exception(status.HTTP_401_UNAUTHORIZED, HTTPException(status_code=401, detail="User Not Available"))
            return response_obj
        
        res = await verification.verify_password(userlogin.password, password_obj.hashed_password, password_obj.salt)

        if not res:
            exp = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password",headers={"WWW-Authenticate": "Bearer"})
            response_obj.set_exception(exp)
            return response_obj
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = verification.create_access_token(
            data={"sub": userlogin.email}, expires_delta=access_token_expires
        )
        user_id = user_obj["user_id"]

        common_util.update_access_token_in_redis(user_id, access_token)
        await common_util.update_user_details_in_redis(user_id, user_obj)
        
        data = {"access_token": access_token, "token_type": "bearer", "role" : user_obj["role"]}
        
        response_obj.set_status(status.HTTP_200_OK)
        response_obj.set_data(data)
        response_obj.set_daily_request_count_left(verification_result["daily_req_left"])

        return response_obj    

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in user_login] {} ".format(ex))


# =========================== SERVICES ==============================

@public_router.post("/createservice")
async def service_sign_up(service_user: ServiceSignup, db: Session = Depends(get_db)):
    try:
        responseObject = ResponseObject()

        service_email = service_user.registration_mail
        service_org = service_user.service_org
        db_client = service_crud.get_service_by_email(db=db, email=service_email)

        if db_client:
            responseObject.set_exception(HTTPException(status_code=400, detail="Email already registered as Service Owner"))
            return responseObject
        
        db_client = service_crud.get_service_by_service_org(db, service_org=service_org)
        if db_client:
            responseObject.set_exception(HTTPException(status_code=400, detail="Service ORG already registered"))
            return responseObject
        
        service_res = await service_crud.create_new_service(db=db, service_user=service_user)
        db_user = crud.get_user_by_email(db=db, email=service_email)

        if db_user:
            responseObject.set_exception(HTTPException(status_code=400, detail="Email already registered as User"))
            return responseObject

        user_signup_model = dict()
        user_signup_model["email"] = service_email
        user_signup_model["password"] = service_user.password
        user_signup_model["phone"] = service_user.phone
        user_signup_model["service_org"] = service_org
        user_signup_model["role"] = str(models.Account.Role.ADMIN)

        user_model = UserSignUp.model_validate(user_signup_model)
        user_res = await crud.create_new_user(db=db, user=user_model)
        
        data = {"Service Details" : service_res, "Admin Account" : user_res}
        responseObject.set_status(status.HTTP_200_OK)
        responseObject.set_data(data)
        return responseObject

    except Exception as ex :
        logging.exception("[PUBLIC_ROUTES][Exception in service_sign_up] {} ".format(ex))


