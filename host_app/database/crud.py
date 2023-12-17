import logging
from .schemas import UserSignUp, OrderCreate, UserSignUpResponse
from .models import Account, Orders, Password
from host_app.common.util import create_hashed_password, generate_salt, create_order_id
from .sql_constants import CommonConstants
from host_app.caching.redis_constant import RedisConstant
import random
from sqlalchemy.orm import Session
from host_app.caching import redis_util
from host_app.common import util
from typing import Optional


def get_user_by_user_id(db: Session, user_id: str, org: Optional[str] = None):
    try:
        if org :
            return db.query(Account).filter(Account.user_id == user_id, Account.service_org == org).first()

        return db.query(Account).filter(Account.user_id == user_id).first()
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_user_id] {} ".format(ex))


def get_user_by_email(db: Session, email: str):
    try:
        return db.query(Account).filter(Account.email == email).first()
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_email] {} ".format(ex))


# only used for login cases
def get_user_by_email_login(db: Session, email: str):
    try:
        joined_data = (
            db.query(Account, Password)
            .join(Password, Account.user_id == Password.user_id)
            .filter(Account.email == email)
            .all()
        )
        return joined_data
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_email_login] {} ".format(ex))


async def get_user_by_username(db: Session, username: str):
    try:
        user = db.query(Account).filter(Account.username == username).first()
        return user

    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_username] {} ".format(ex))


def get_user_by_phone(db: Session, phone: str):
    try:
        return db.query(Account).filter(Account.phone == phone).first()
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_phone] {} ".format(ex))


async def create_new_user(db: Session, user: UserSignUp):
    try:
        username = user.username
        service_org = user.service_org
        password = user.password
        role = user.role
        if not role :
            role = Account.Role.USER
        role = int(role)
            
        alpha_int = random.randint(1,26)
        if not username :
            username = "User_" + service_org + "_" + str(role) + await util.generate_secure_random_string()

        user_id = service_org + "_" + str(role) + "_" +chr(64 + alpha_int)+ str(random.randint(1000,9999))
        
        db_user = Account(email=user.email, phone=user.phone, user_id=user_id, username=username, service_org=service_org, role=role)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        test_response = {"email":user.email, "phone":user.phone, "user_id":user_id,"username":username, "is_verified" : db_user.is_verified , "role" : db_user.role, "service_org" : db_user.service_org}
        await create_password(db, user_id, password)

        response = UserSignUpResponse.model_validate(test_response)
        return response

    except Exception as ex :
        logging.exception("[CRUD][Exception in create_new_user] {} ".format(ex))
    return None


async def create_password(db:Session, user_id:str, password : str):
    try:
        salt = await generate_salt(CommonConstants.SALT_LENGTH)
        hashed_password = await create_hashed_password(password, salt)
        db_user = Password(user_id=user_id, hashed_password=hashed_password, salt=salt )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user


    except Exception as ex :
        logging.exception("[CRUD][Exception in create_password] {} ".format(ex))


async def get_password_data(db: Session, user_id: str):
    try :
        password_data = db.query(Password).filter(Password.user_id == user_id).first()
        return password_data

    except Exception as ex :
        logging.exception("[CRUD][Exception in get_password_data] {} ".format(ex))


async def update_password_data(db: Session, user_id: int, user_update_map: dict):
    try :
        print(" DATA RECEIVED FOR update_user ",user_update_map)
        db_user = db.query(Password).filter(Password.user_id == user_id).first()
        if db_user:
            for key, value in user_update_map.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
            return db_user
        return None
    except Exception as ex :
        logging.exception("[CRUD][Exception in update_user] {} ".format(ex))


async def update_account_data(db: Session, user_id: int, user_update_map: dict):
    try :
        print(" DATA RECEIVED FOR update_user ",user_update_map)
        db_user = db.query(Account).filter(Account.user_id == user_id).first()
        if db_user:
            for key, value in user_update_map.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
            return db_user.to_dict()
        return None
    except Exception as ex :
        logging.exception("[CRUD][Exception in update_user] {} ".format(ex))



def delete_user(db: Session, user_id: str):
    try:
        db_user = db.query(Account).filter(Account.user_id == user_id).first()
        print("Landed on password delete")
        if db_user:
            db.delete(db_user)
            db.commit()
            obj = db.query(Password).filter(Password.user_id == user_id).first()
            print(" Deleted from Account | password obj  ", obj)
            if obj:
                db.delete(obj)
                db.commit()
                print(" Deleted from Password Table")
                return True
        return False
    except Exception as ex :
        logging.exception("[CRUD][Exception in delete_user] {} ".format(ex))


async def get_all_users(db: Session, org: Optional[str] = None, skip: int = 0, limit: int = 100):
    try:
        # Jani na keno ei join krsi 
        # res =  db.query(Account, Orders).join(Orders).filter(Account.id == Orders.owner_id).all()
        # for e in res :
        if org :
            res = db.query(Account).filter(Account.service_org == org).all()
        else :
            res = db.query(Account).all()

        res_arr = {}
        for e in res :
            dicu = await e.to_dict()
            res_arr[dicu["user_id"]] = dicu

        return res_arr
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_all_users] {} ".format(ex))


async def get_all_unverified_users(db: Session, org: Optional[str] = None, skip: int = 0, limit: int = 100):
    try:
        # Jani na keno ei join krsi 
        # res =  db.query(Account, Orders).join(Orders).filter(Account.id == Orders.owner_id).all()
        # for e in res :
        if org :
            res = db.query(Account).filter(Account.is_verified == Account.Verification.NOT_VERIFIED, Account.service_org == org).all()
        else :
            res = db.query(Account).filter(Account.is_verified == Account.Verification.NOT_VERIFIED).all()

        res_arr = {}
        for e in res :
            dicu = await e.to_dict()
            res_arr[dicu["user_id"]] = dicu

        return res_arr
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_all_users] {} ".format(ex))


# ==================== Orders CRUD METHODS =================================

async def create_new_order(db: Session, orders_info: OrderCreate):
    try :
        ord_id = await create_order_id(orders_info.owner_id)
        order_obj = Orders(order_id=ord_id, product_id=orders_info.product_id, owner_id=orders_info.owner_id,receivers_mobile= orders_info.receivers_mobile, delivery_address=orders_info.delivery_address)
        db.add(order_obj)
        db.commit()
        db.refresh(order_obj)
        return order_obj.to_dict()
    except Exception as ex :
        logging.exception("[CRUD][Exception in create_new_order]",ex)


def get_all_orders_by_user(db: Session, user_id: str, org: Optional[str] = None):
    try:
        if not org : 
            single_order_obj = db.query(Orders).filter(Orders.owner_id == user_id).all()
        else :
            single_order_obj = db.query(Orders).filter(Orders.owner_id == user_id,Orders.service_org == org ).all()

        return single_order_obj
    except Exception as ex:
        logging.exception("[crud][Exception in get_all_orders_by_user] {} ".format(ex))


def get_order_by_order_id(db: Session, user_id : str, order_id: str, org: Optional[str] = None):
    try:
        order_obj =  db.query(Orders).filter(Orders.order_id == order_id, Orders.owner_id== user_id).first()
        
    except Exception as ex :
        logging.exception("[crud][Exception in get_order_by_order_id] {} ".format(ex))


def get_orders_status(db: Session, user_id : str, Orders_id: int, org: Optional[str] = None):
    try:
        order = get_order_by_order_id(db, Orders_id)
        return order
    except Exception as ex :
        logging.exception("[crud][Exception in get_order_by_order_id] {} ".format(ex))
    


async def update_order_status(db: Session, user_id : str, order_id: str, orders_status: dict, org: Optional[str] = None):
    try :
        logging.info("[CRUD][Landed in update_Orders_status] {} ".format(orders_status))
        order_obj = db.query(Orders).filter(Orders.order_id == order_id).first()
  
        if order_obj:
            if order_obj.owner_id == user_id:
                for key, value in orders_status.items():
                    if key and value :
                        setattr(order_obj, key, value)
                db.commit()
                db.refresh(order_obj)
                updated_order_obj =  db.query(Orders).filter(Orders.order_id == order_id).first()
                print(" UPDATED updated_order_obj : ",updated_order_obj)
                return updated_order_obj.to_dict()
        return None
    except Exception as ex :
        logging.exception("[CRUD][Exception in update_Orders_status] {} ".format(ex))


def delete_order(db: Session, order_id: str, user_id : str, org: Optional[str] = None):
    try:
        order_obj = db.query(Orders).filter(Orders.order_id == order_id).first()
        if order_obj.owner_id != user_id :
            logging.info("[CRUD][Not authorizede to delete this order][Order_Id] {} [User_id] {}".format(order_id, user_id))
            return False
        if order_obj:
            db.delete(order_obj)
            db.commit()
            return True
    except Exception as ex :
        logging.exception("[CRUD][Exception in delete_order] {} ".format(ex))
    return False



def get_all_orderss(db: Session, skip: int = 0, limit: int = 100, org: Optional[str] = None):
    try:
        if not org :
            return db.query(Orders).offset(skip).limit(limit).all()
        return db.query(Account).filter(Orders.service_org == org).all()
        
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_all_Orderss] {} ".format(ex))


async def get_single_order(db: Session, user_id: str, order_id: str, org: Optional[str] = None):
    try:
        if(await redis_util.is_exists(RedisConstant.ORDER_OBJ + order_id)):
            single_order = await redis_util.get_hm(RedisConstant.ORDER_OBJ + order_id)
            if single_order["user_id"] == user_id :
                return single_order
        else :
            single_order = get_order_by_order_id(db, order_id)

            if single_order.user_id == user_id :
                data = single_order.to_dict()
                creted_time = data["created_time"]
                data["created_time"] = str(creted_time)
                await redis_util.set_hm(RedisConstant.ORDER_OBJ + order_id, data, 1800)
    
                return single_order

    except Exception as ex :
        logging.exception("[MAIN][Exception in get_single_order] {} ".format(ex))
    return single_order