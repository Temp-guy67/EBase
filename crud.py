import logging
from util import create_hashed_password, generate_salt
from schemas import UserCreate 
from models import Account
from util import create_hashed_password, generate_salt

# from sqlalchemy.orm import Session
from database import SessionLocal


# def get_user_by_id(db:Session, user_id: int):
#     try:
#         account_data =  db.query(Account).filter(Account.id == user_id).first()
#         print(" ACCOUNT _DATA : " , account_data)
#         order_details =  db.query(Order).filter(Account.id == user_id)
#     except Exception as ex :
#         logging.exception("[main][Exception in signup] {} ".format(ex))


def get_user_by_email(db: SessionLocal, email: str):
    try:
        # db = next(db_test)
        print(" IN get_user_by_email ")
        return db.query(Account).filter(Account.email == email).first()
    except Exception as ex :
        logging.exception("[main][Exception in get_user_by_email] {} ".format(ex))

# def get_user_by_phone(phone:str, db: Session):
#     try:
#         # db = next(db_test)
#         return db.query(models.Account).filter(models.Account.phone == phone).first()
#     except Exception as ex :
#         logging.exception("[main][Exception in signup] {} ".format(ex))

# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     try:
#         return db.query(models.Account).offset(skip).limit(limit).all()
#     except Exception as ex :
#         logging.exception("[main][Exception in signup] {} ".format(ex))


async def create_user(db: SessionLocal, user: UserCreate):
    try:
        print(" create user data ",**user.model_dump())

        salt = await generate_salt()
        hashed_password = await create_hashed_password(user.password, salt)
        db_user = Account(salt=salt, hashed_password=hashed_password, user=user)
        await db.add(db_user)
        db.commit()
        db.refresh(db_user)                               # to know everything is stored
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



async def validatePassword(userId, password):
    try :
        pass
    except Exception as ex :
        logging.error("[PasswordDB][validatePassword][Exception caught] {} ".format(ex))





# def get_user(db: Session, user_id: int):
#     return db.query(User).filter(models.User.id == user_id).first()


# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()


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
