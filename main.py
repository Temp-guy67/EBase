from fastapi import Depends, FastAPI, HTTPException, status, Request
from schemas import UserSignUp, TokenData, UserInDB, OrderCreate, UserLogin, OrderQuery, UserDelete, UserUpdate
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from services import onStartService
from database import engine, Base, SessionLocal
from sql_constants import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordBearer
import jwt, jwt.exceptions
import logging
from datetime import datetime, timedelta
from typing import Annotated
import crud,util,redis_util

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your allowed origins (e.g., ["https://example.com"])
    allow_methods=["*"],  # Allow all HTTP methods or specify specific methods (e.g., ["GET", "POST"])
    allow_headers=["*"],  # Allow all headers or specify specific headers (e.g., ["Authorization"])
)

Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        
@app.on_event("startup")
async def startService():
    await onStartService()

#====================================== USER ============================

@app.post("/user/signup")
async def sign_up(user: UserSignUp, db: Session = Depends(get_db)):
    try:
        db_user = crud.get_user_by_email(db=db, email=user.email)

        if db_user:
            return HTTPException(status_code=400, detail="Email already registered")
        
        db_user = crud.get_user_by_phone(db, phone=user.phone)
        if db_user:
            return HTTPException(status_code=400, detail="Phone Number already registered")
        res = await crud.create_new_user(db=db, user=user)
        return res

    except Exception as ex :
        logging.exception("[MAIN][Exception in sign_up] {} ".format(ex))


@app.post("/user/login")
async def user_login(userlogin : UserLogin, req: Request, db: Session = Depends(get_db)):
    try:
        client_ip = req.client.host
        user_agent = req.headers.get("user-agent")
        db_user = crud.get_user_by_email_login(db, email=userlogin.email)
        print(" DB -SUER ",db_user)

        account_obj = db_user[0][0]
        password_obj = db_user[0][1]

        session_map = await account_obj.to_dict()
        session_map["client_ip"] = client_ip
        session_map["user_agent"] = user_agent

        if not account_obj:
            return HTTPException(status_code=400, detail="User Not Available")
        
        res = await verify_password(password_obj.user_id, userlogin.password, password_obj.hashed_password, password_obj.salt)

        if not res:
            return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password",headers={"WWW-Authenticate": "Bearer"})
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": userlogin.email}, expires_delta=access_token_expires
        )

        await redis_util.set_hm(access_token, session_map)
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as ex :
        logging.exception("[MAIN][Exception in user_login] {} ".format(ex))


async def verify_password(user_id : str, user_password: str, hashed_password : str, salt : str,  db: Session = Depends(get_db)):
    try:
        if hashed_password and salt and user_password :
            temp_hashed_password = await util.create_hashed_password(user_password, salt)
            return temp_hashed_password == hashed_password
        else :
            return False

    except Exception as ex:
        logging.exception("[MAIN][Exception in verify_password] {} ".format(ex))



def create_access_token(data: dict, expires_delta: timedelta | None = None):
    try :
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    except Exception as ex :
        logging.exception("[MAIN][Exception in create_access_token] {} ".format(ex))
        


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        redis_data = await redis_util.get_hm(token)

        if redis_data:
            return redis_data

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)

        db_user = crud.get_user_by_email(db=db, email=token_data.username)
        if db_user is None:
            raise credentials_exception
        return db_user
        
    except Exception as ex :
        logging.exception("[MAIN][Exception in get_current_user] {} ".format(ex))
        raise credentials_exception


async def get_current_active_user(current_user: Annotated[UserInDB, Depends(get_current_user)]):
    return current_user


@app.get("/user/me/")
async def read_users_me(user: UserInDB = Depends(get_current_active_user)):
    try:
        return user
    except Exception as ex:
        logging.exception("[MAIN][Exception in read_users_me] {} ".format(ex))


@app.post("/user/update/")
async def update_user(user_data : UserUpdate,user: UserInDB = Depends(get_current_active_user),  db: Session = Depends(get_db)):
    try:
        user_id = user.id
        password = user.password
        # verify password and tell them if fails operation stops here with exception and also segregate update column here, we have restrictions while updating , user cant update user name and email except admin support
        data = {"phone": "999000999"} 
        await crud.update_user(db, user_id, data)

    except Exception as ex:
        logging.exception("[MAIN][Exception in update_user] {} ".format(ex))



@app.post("/user/updatepassword/")
async def update_user_password(user_data : UserUpdate,user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = user.id
        password = user_data.password
        if await verify_password(user.hashed_password, user.salt, password):
            new_password = user_data.new_password
            new_salt = await util.generate_salt()
            new_hashed_password = await util.create_hashed_password(new_password, new_salt)
            data = {"salt": new_salt, "hashed_password" : new_hashed_password} 
            await crud.update_user(db, user_id, data)
        else :
            pass 
            #raise exception

    except Exception as ex:
        logging.exception("[MAIN][Exception in update_user_password] {} ".format(ex))


@app.post("/user/delete/")
async def delete_user(user_data : UserDelete, user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = user.id
        password = user_data.password
        if await verify_password(user.hashed_password, user.salt, password):
            print(" password verified | in delete user")
            if crud.delete_user(db, user_id):
                return user.username + " DELETED SUCCESSFULLY"
            else:
                return user.username + " not DELETED"
        else:
            pass 
            # raise invalid password exception

    except Exception as ex:
        logging.exception("[MAIN][Exception in delete_user] {} ".format(ex))
        

# ==================== ORDERS ========================

@app.post("/order/create")
async def order_info_receiver(order_info: OrderCreate, user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        print(" CREATED NEW ORDER [MAIN] {}".format(user.id))

        if int(order_info.user_id) == user.id :
            # order = await create_order(order_info)
            print("[MAIN] INSDIDE IF BLOCAL ",order_info)
            order = await crud.create_new_order(db, order_info)

            return order
        else :
            print(" ELSE BLOCk {}".format(order_info))

    except Exception as ex:
        logging.exception("[main][Exception in read_users_me] {} ".format(ex))


@app.get("/order/")
async def order(user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        print("[MAIN] getting all order of this user id {}".format(user.id))
        all_orders = crud.get_all_orders_by_user(db, user.id)
        redis_util.set_hm(user.user_id, all_orders)

    except Exception as ex:
        logging.exception("[main][Exception in order] {} ".format(ex))
    return all_orders

@app.get("/order/{order_id}")
async def order_status(order_id: str, user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    print(" LANDED ")
    return crud.get_order_by_id(db, order_id)


# update and cancel and all
@app.post("/order/update")
async def update_order_status(order_query: OrderQuery, user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    pass
    # dicu = order_query.model_dump()
    
    # id = int(order_query.order_id)
    # del dicu["order_id"]
    # print(" LANDED update_order_status - ", dicu)
    # await crud.update_order_status(db, id , dicu)

    # delete from redis 
    # update in db
    # then put the data in redis again


# ===============================ADMIN SPECIAL =====================================

@app.get("/auth/getallorder")
async def get_all_order(user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return crud.get_all_orders(db)


@app.get("/auth/getalluser")
async def get_all_user(user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return await crud.get_all_users(db)


# TEST CODE FOR FRONTEND
# =========================================================================================================
@app.get("/test")
async def hello():
    return {"message" : "working fine"}


@app.post("/test/login")
async def login_test(form_data: UserSignUp):
    try:
        return {"access_token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJcInRlc3QzXCIiLCJleHAiOjE2OTU3MTQzNzB9.LGXf2RVsbtrEiVTvQGRg3T1UzqmnEDEIQi8MF3AC-kI", "token_type" : "bearer"}
    
    except Exception as ex :
        logging.exception("[main][Exception in signup] {} ".format(ex))


@app.get("/test/getuser", response_model=UserInDB)
async def get_user():
    return {
  "email": "test3@testmail.com",
  "salt": "3v9YWoLV",
  "created_time": "2023-09-18T12:30:48",
  "id": 1,
  "hashed_password": "0956c5c1ff5bcc838b1b02e01e1b3fd2953f59961bcb2a008693b5442d1f124b",
  "username": "test3",
  "phone": "123456711",
}