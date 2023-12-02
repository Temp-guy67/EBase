
import logging
from .schemas import UserSignUp, OrderCreate, UserSignUpResponse, ClientSignup
from .models import Service
from host_app.common.util import create_hashed_password, generate_salt, create_order_id
from .sql_constants import CommonConstants
from host_app.caching.redis_constant import RedisConstant
import random
from sqlalchemy.orm import Session
from host_app.caching import redis_util



def get_client_by_service_id(db: Session, service_id: str):
    try:
        return db.query(Service).filter(Service.service_id == service_id).first()
    except Exception as ex :
        logging.exception("[CLIENT_DBUTILS][Exception in get_client_by_service_id] {} ".format(ex))


def get_client_by_email(db: Session, email: str):
    try:
        return db.query(Service).filter(Service.registration_mail == email).first()
    except Exception as ex :
        logging.exception("[CLIENT_DBUTILS][Exception in get_client_by_email] {} ".format(ex))


def get_client_by_service_initials(db: Session, service_initials: str):
    try:
        return db.query(Service).filter(Service.service_initials == service_initials).first()
    except Exception as ex :
        logging.exception("[CLIENT_DBUTILS][Exception in get_client_by_service_initials] {} ".format(ex))



async def create_new_client(db: Session, user: ClientSignup):
    try:
        username = user.username
        alpha_int = random.randint(1,26)
        if not username :
            rand_int = random.randint(1,999)
            
            username = "auto_" + str(rand_int) + chr(64 + alpha_int) 

        user_id = "user_" + chr(64 + alpha_int) + str(random.randint(1,999))
        db_user = Service(email=user.email, phone=user.phone, user_id=user_id,
                          username=username)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        test_response = {"email":user.email, "phone":user.phone, "user_id":user_id,"username":username, "is_verified" : db_user.is_verified , "role" : db_user.role}

        response = UserSignUpResponse.model_validate(test_response)
        return response

    except Exception as ex :
        logging.exception("[CRUD][Exception in create_new_user] {} ".format(ex))
    return None