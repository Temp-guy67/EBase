import logging
from util import create_hashed_password, generate_salt
from schemas import UserSignUp, OrderCreate, UserSignUpResponse
from models import Account, Orders, Password
from util import create_hashed_password, generate_salt, create_order_id
from sql_constants import CommonConstants
import random
from sqlalchemy.orm import Session


def get_user_by_user_id(db: Session, user_id: str):
    try:
        return db.query(Account).filter(Account.user_id == user_id).first()
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_user_id] {} ".format(ex))


def get_user_by_email(db: Session, email: str):
    try:
        return db.query(Account).filter(Account.email == email).first()
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_email] {} ".format(ex))


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
        password = user.password
        alpha_int = random.randint(1,26)
        if not username :
            rand_int = random.randint(1,999)
            
            username = "auto_" + str(rand_int) + chr(64 + alpha_int) 

        user_id = "user_" + chr(64 + alpha_int) + str(random.randint(1,999))
        db_user = Account(email=user.email, phone=user.phone, user_id=user_id,
                          username=username)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        test_response = {"email":user.email, "phone":user.phone, "user_id":user_id,"username":username, "is_verified" : db_user.is_verified , "role" : db_user.role}
        await create_password(db, user_id, password)

        response = UserSignUpResponse.model_validate(test_response)
        return response

    except Exception as ex :
        logging.exception("[CRUD][Exception in create_new_user] {} ".format(ex))
    return None


async def create_password(db:Session, user_id:str, password : str):
    try:
        salt = await generate_salt()
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
            return db_user
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


async def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    try:
        # Jani na keno ei join krsi 
        # res =  db.query(Account, Orders).join(Orders).filter(Account.id == Orders.owner_id).all()
        # for e in res :
        res = db.query(Account).all()
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
        print(" Order Generated ")
        return order_obj.to_dict()
    except Exception as ex :
        logging.exception("[CRUD][Exception in create_new_order]",ex)


def get_all_orders_by_user(db: Session, user_id: str):
    try:
        single_order_obj = db.query(Orders).filter(Orders.owner_id == user_id).all()
        return single_order_obj
    except Exception as ex:
        logging.exception("[crud][Exception in get_all_orders_by_user] {} ".format(ex))


def get_order_by_order_id(db: Session, order_id: str):
    try:
        return db.query(Orders).filter(Orders.order_id == order_id).first()
    except Exception as ex :
        logging.exception("[crud][Exception in get_order_by_order_id] {} ".format(ex))


def get_orders_status(db: Session, Orders_id: int):
    try:
        order = get_order_by_order_id(db, Orders_id)
        return order
    except Exception as ex :
        logging.exception("[crud][Exception in get_order_by_order_id] {} ".format(ex))
    


async def update_order_status(db: Session, Orders_id: str, Orders_status: dict):
    try :
        logging.info("[CRUD][Landed in update_Orders_status] {} ".format(Orders_status))
        Orders_obj = db.query(Orders).filter(Orders.Orders_id == Orders_id).first()
        if Orders_obj:
            for key, value in Orders_status.items():
                setattr(Orders_obj, key, value)
            db.commit()
            db.refresh(Orders_obj)
            return Orders_obj
        return None
    except Exception as ex :
        logging.exception("[CRUD][Exception in update_Orders_status] {} ".format(ex))


def delete_order(db: Session, order_id: str):
    try:
        order_obj = db.query(Orders).filter(Orders.order_id == order_id).first()
        if order_obj:
            db.delete(order_obj)
            db.commit()
            return True
    except Exception as ex :
        logging.exception("[CRUD][Exception in delete_order] {} ".format(ex))
    return False



def get_all_orderss(db: Session, skip: int = 0, limit: int = 100):
    try:
        return db.query(Orders).offset(skip).limit(limit).all()
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_all_Orderss] {} ".format(ex))

