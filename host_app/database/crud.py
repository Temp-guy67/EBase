import logging, random
from host_app.common.exceptions import Exceptions
from host_app.database.schemas import UserSignUp
from host_app.database.models import Account, Password
from host_app.common.util import create_hashed_password, generate_salt
from host_app.common.constants import CommonConstants
from sqlalchemy.orm import Session
from host_app.common import util
from typing import Optional
from sqlalchemy import or_

from host_app.mail_manager.config import send_email_to_client


def get_user_by_user_id(db: Session, user_id: str, is_sup : Optional[bool] = None, org: Optional[str] = None):
    try:
        res = None
        if is_sup :
            res = db.query(Account).filter(Account.user_id == user_id).first()
            
        elif org :
            res = db.query(Account).filter(Account.user_id == user_id, Account.service_org == org, Account.account_state == Account.AccountState.ACTIVE).first()
        else :
            res = db.query(Account).filter(Account.user_id == user_id).first()
            
        return res.to_dict() if res else None
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_user_id] {} ".format(ex))


def get_user_by_email(db: Session, email: str):
    try:
        db_user = db.query(Account).filter(Account.email == email, Account.account_state == Account.AccountState.ACTIVE).first()
        return db_user.to_dict() if db_user else None
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_email] {} ".format(ex))


# only used for login cases
def get_user_by_email_login(db: Session, email: str):
    try:
        joined_data = (
            db.query(Account, Password)
            .join(Password, Account.user_id == Password.user_id)
            .filter(Account.email == email, Account.account_state == Account.AccountState.ACTIVE)
            .all()
        )
        return joined_data 
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_email_login] {} ".format(ex))


def get_user_by_username(db: Session, username: str):
    try:
        user = db.query(Account).filter(Account.username == username, Account.account_state == Account.AccountState.ACTIVE).first()
        return user.to_dict() if user else None

    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_username] {} ".format(ex))


def get_user_by_phone(db: Session, phone: str):
    try:
        return db.query(Account).filter(Account.phone == phone).first()
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_user_by_phone] {} ".format(ex))


def if_account_cred_exist(db:Session, email : str, phone : str, username : Optional[str] = None):
    try:
        if username:
            user_obj = db.query(Account).filter(or_(Account.email == email, Account.phone == phone, Account.username == username)).first()
        else :
            user_obj = db.query(Account).filter(or_(Account.email == email, Account.phone == phone)).first()
        return user_obj.to_dict() if user_obj else None
    except Exception as ex :
        logging.exception("[CRUD][Exception in if_account_cred_exist] {} ".format(ex))


async def create_new_user(db: Session, user: UserSignUp, service_org : str):
    try:
        username = user.username
        role = user.role
        if not role :
            role = Account.Role.USER
        role = int(role)
            
        alpha_int = random.randint(1,26)
        if not username :
            username = "User_" + service_org + str(role) + await util.generate_secure_random_string()

        user_id = service_org + str(role) + "_" +chr(64 + alpha_int)+ str(random.randint(1000,9999))
        
        db_user = Account(email=user.email, phone=user.phone, user_id=user_id, username=username, service_org=service_org, role=role)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        first_time_pass = await create_new_password(db, user_id)
        
        # mailing
        user_map = {"username" : username, "email" : user.email, "password" : first_time_pass}
        send_email_to_client(1, user_map)
        
        return db_user.to_dict()

    except Exception as ex :
        logging.exception("[CRUD][Exception in create_new_user] {} ".format(ex))
    return None


async def create_new_password(db:Session, user_id:str):
    try:
        # salt is being used as first password
        salt = await generate_salt(CommonConstants.SALT_LENGTH)
        hashed_password = await create_hashed_password(salt, salt)
        db_user = Password(user_id=user_id, hashed_password=hashed_password, salt=salt )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return salt


    except Exception as ex :
        logging.exception("[CRUD][Exception in create_new_password] {} ".format(ex))


async def get_password_data(db: Session, user_id: str):
    try :
        password_data = db.query(Password).filter(Password.user_id == user_id).first()
        return password_data

    except Exception as ex :
        logging.exception("[CRUD][Exception in get_password_data] {} ".format(ex))


async def update_password_data(db: Session, user_id: int, user_update_map: dict):
    try :
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


async def update_account_data(db: Session, user_id: str, updater:str, user_update_map: dict, service_org: Optional[str] = None, is_sup : Optional[bool] = None):
    try :
        logging.info(f"Data received in Update Account Info : user_id {user_id} | updater : {updater} | user_update_map : {user_update_map} | service_org : {service_org}")
        if is_sup :
            db_user = db.query(Account).filter(Account.user_id == user_id).first()
        elif service_org :
            db_user = db.query(Account).filter(Account.user_id == user_id, Account.account_state == Account.AccountState.ACTIVE, Account.service_org == service_org).first()
        else :
            db_user = db.query(Account).filter(Account.user_id == user_id, Account.account_state == Account.AccountState.ACTIVE).first()
            
        if db_user:
            for key, value in user_update_map.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
            return db_user.to_dict()
        return None
    except Exception as ex :
        logging.exception("[CRUD][Exception in update_account_data] {} ".format(ex))



async def delete_user(db: Session, user_id: str, service_org: Optional[str] = None):
    try:
        if service_org :
            db_user = db.query(Account).filter(Account.user_id == user_id, Account.account_state == Account.AccountState.ACTIVE, Account.service_org == service_org).first()
        else : 
            db_user = db.query(Account).filter(Account.user_id == user_id, Account.account_state == Account.AccountState.ACTIVE).first()

        if db_user:
            setattr(db_user, "account_state" , Account.AccountState.DELETED )
            # db.delete(db_user) - Not deleting
            db.commit()
            db.refresh(db_user)
            obj = db.query(Password).filter(Password.user_id == user_id).first()
            if obj:
                db.delete(obj)
                db.commit()
    
                return True
        return False
    except Exception as ex :
        logging.exception("[CRUD][Exception in delete_user] {} ".format(ex))


async def get_all_users(db: Session, is_sup: Optional[bool] = None, service_org: Optional[str] = None, skip: int = 0, limit: int = 100):
    try:
        if is_sup:
            res = res = db.query(Account).all()
        elif service_org :
            res = db.query(Account).filter(Account.service_org == service_org, Account.account_state == Account.AccountState.ACTIVE).all()
        else :
            res = db.query(Account).filter(Account.account_state == Account.AccountState.ACTIVE).all()

        res_arr = {}
        for e in res :
            dicu = e.to_dict()
            res_arr[dicu["user_id"]] = dicu

        return res_arr
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_all_users] {} ".format(ex))


async def get_all_unverified_users(db: Session, is_sup: Optional[bool] = None, org: Optional[str] = None, skip: int = 0, limit: int = 100):
    try:
        if is_sup:
            res = db.query(Account).filter(Account.is_verified == Account.Verification.NOT_VERIFIED).all()
        elif org :
            res = db.query(Account).filter(Account.is_verified == Account.Verification.NOT_VERIFIED, Account.service_org == org, Account.account_state == Account.AccountState.ACTIVE).all()
        else :
            res = db.query(Account).filter(Account.is_verified == Account.Verification.NOT_VERIFIED, Account.account_state == Account.AccountState.ACTIVE).all()

        res_arr = {}
        for e in res :
            dicu = e.to_dict()
            res_arr[dicu["user_id"]] = dicu

        return res_arr
    except Exception as ex :
        logging.exception("[CRUD][Exception in get_all_users] {} ".format(ex))


