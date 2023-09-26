import logging
from util import create_hashed_password, generate_salt
from schemas import UserSignUp
from models import Account
from util import create_hashed_password, generate_salt
from sql_constants import CommonConstants
import random

from sqlalchemy.orm import Session
# from database import SessionLocal


# def get_user_by_id(db:Session, user_id: int):
#     try:
#         account_data =  db.query(Account).filter(Account.id == user_id).first()
#         print(" ACCOUNT _DATA : " , account_data)
#         order_details =  db.query(Order).filter(Account.id == user_id)
#     except Exception as ex :
#         logging.exception("[main][Exception in signup] {} ".format(ex))


def get_user_by_email(db: Session, email: str):
    try:
        return db.query(Account).filter(Account.email == email).first()
    except Exception as ex :
        logging.exception("[crud][Exception in get_user_by_email] {} ".format(ex))


def get_user_by_username(db: Session, username: str):
    try:
        return db.query(Account).filter(Account.username == username).first()
    except Exception as ex :
        logging.exception("[crud][Exception in get_user_by_username] {} ".format(ex))


def get_user_by_phone(db: Session, phone: str):
    try:
        return db.query(Account).filter(Account.phone == phone).first()
    except Exception as ex :
        logging.exception("[crud][Exception in get_user_by_phone] {} ".format(ex))

# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     try:
#         return db.query(models.Account).offset(skip).limit(limit).all()
#     except Exception as ex :
#         logging.exception("[main][Exception in signup] {} ".format(ex))


async def create_new_user(db: Session, user: UserSignUp):
    try:
        salt = await generate_salt()
        hashed_password = await create_hashed_password(user.password, salt)
        username = user.username
        if not username :
            id_salt = await generate_salt(CommonConstants.RANDOM_ID_LENGTH)
            rand_int = random.randint(1,999)
            username = "auto_" + id_salt + str(rand_int)

        db_user = Account(salt=salt, hashed_password=hashed_password, username=username, email=user.email, phone=user.phone)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)   
        logging.info("[crud][create_new_user] ADDED SUCCESSFULLY ")                # to know everything is stored
        return db_user
    except Exception as ex :
        logging.exception("[crud][Exception in create_user] {} ".format(ex))


# From ChatGPT : Not tested yet

# def delete_user(db: Session, user_id: int):
#     user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
#     if user_to_delete:
#         db.delete(user_to_delete)
#         db.commit()
#         return True
#     return False

# def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
#     db_user = db.query(models.User).filter(models.User.id == user_id).first()
#     if db_user:
#         for key, value in user_update.dict().items():
#             setattr(db_user, key, value)
#         db.commit()
#         db.refresh(db_user)
#         return db_user
#     return None




# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.User).offset(skip).limit(limit).all()


# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user


# def get_items(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Item).offset(skip).limit(limit).all()


# def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
#     db_item = models.Item(**item.dict(), owner_id=user_id)
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item
