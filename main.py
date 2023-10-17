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
from models import Account

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
        
        account_obj = db_user[0][0]
        password_obj = db_user[0][1]
        
        user_obj = await account_obj.to_dict()
        user_obj["client_ip"] = client_ip
        user_obj["user_agent"] = user_agent

        if not account_obj:
            return HTTPException(status_code=400, detail="User Not Available")
        
        res = await verify_password( userlogin.password, password_obj.hashed_password, password_obj.salt)

        if not res:
            return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password",headers={"WWW-Authenticate": "Bearer"})
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": userlogin.email}, expires_delta=access_token_expires
        )
        user_id = user_obj["user_id"]

        await redis_util.set_hm(user_id, user_obj)
        await redis_util.set_str(access_token, user_id)
        
        return {"access_token": access_token, "token_type": "bearer", "messege" : "Login Successful"}

    except Exception as ex :
        logging.exception("[MAIN][Exception in user_login] {} ".format(ex))


async def verify_password(user_password: str, hashed_password : str, salt : str):
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
        user_id_from_token_map = await redis_util.get_str(token)

        logging.info(" GOt user_id from token map : {} ".format(user_id_from_token_map))

        if user_id_from_token_map:
            user_data = await redis_util.get_hm(user_id_from_token_map)
            logging.info(" GOt user_data MAP from token map : {} ".format(user_data))
            if user_data :
                return user_data

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)

        db_user = crud.get_user_by_email(db=db, email=token_data.email)
        if db_user is None:
            raise credentials_exception
        
        db_data = await db_user.to_dict()
        await redis_util.set_hm(db_user.user_id, db_data, 1800)
        return db_data
        
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
        password = user_data.password
        # verify password and tell them if fails operation stops here with exception and also segregate update column here, we have restrictions while updating , user cant update user name and email except admin support
        password_obj = await crud.get_password_data(db, user_id)
        
        await verify_password(password, password_obj.hashed_password, password_obj.salt)


        data = {"phone": "999000999"} 
        await crud.update_user(db, user_id, data)

    except Exception as ex:
        logging.exception("[MAIN][Exception in update_user] {} ".format(ex))



@app.post("/user/updatepassword/")
async def update_user_password(user_data : UserUpdate,user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]
        password = user_data.password
        password_obj = await crud.get_password_data(db, user_id)

        if await verify_password(password, password_obj.hashed_password, password_obj.salt):
            new_password = user_data.new_password
            new_salt = await util.generate_salt()
            new_hashed_password = await util.create_hashed_password(new_password, new_salt)
            data = {"salt": new_salt, "hashed_password" : new_hashed_password} 
            res = await crud.update_password_data(db, user_id, data)
            if res :
                await redis_util.delete_from_redis(user_id)
        else :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password is wrong",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except Exception as ex:
        logging.exception("[MAIN][Exception in update_user_password] {} ".format(ex))
        
    return {"user_id" : user_id, "messege":"Password has been Updated Sucessfully"}


@app.post("/user/delete/")
async def delete_user(user_data : UserDelete, user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]
        password = user_data.password
        password_obj = await crud.get_password_data(db, user_id)
        
        if await verify_password(password, password_obj.hashed_password, password_obj.salt):
            res = crud.delete_user(db, user_id)
            if res :
                await redis_util.delete_from_redis(user_id)
                return  {"user_id" : user_id, "messege":"User has been Deleted Sucessfully"} 
            else:
                return {"user_id" : user_id, "messege":"Failed to delete user ; Contact Admin Team"} 
        else:
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password is wrong",
                headers={"WWW-Authenticate": "Bearer"}
            )

    except Exception as ex:
        logging.exception("[MAIN][Exception in delete_user] {} ".format(ex))
        




# ==================== ORDERS ========================

@app.post("/order/create")
async def order_info_receiver(order_info: OrderCreate, user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        print(" CREATED NEW ORDER [MAIN] {}".format(user.id))
        
        if not user.is_verified:
            return  HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sorry, You are not Verified yet",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if order_info.user_id == user["user_id"] :
            order = await crud.create_new_order(db, order_info)
            return order
        else :
            return  HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong Path",
                headers={"WWW-Authenticate": "Bearer"}
            )

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

@app.get("/auth/getallorders")
async def get_all_orders(user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] == Account.Role.SUPER_ADMIN :
            return crud.get_all_orders(db)
        else :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to this access",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except Exception as ex :
        logging.exception("[MAIN][Exception in get_all_order] {} ".format(ex))



@app.get("/auth/getalluser")
async def get_all_user(user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        if user["role"] == Account.Role.SUPER_ADMIN or user["role"] == Account.Role.ADMIN:
            return await crud.get_all_users(db)
        else :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to this access",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except Exception as ex :
        logging.exception("[MAIN][Exception in get_all_user] {} ".format(ex))


@app.post("/auth/updateuser/")
async def update_user_role(info: UserUpdate, user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        print(" USER to action  is {} ".format(user))
        if not (int(user["role"]) == Account.Role.SUPER_ADMIN or int(user["role"]) == Account.Role.ADMIN) :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to this Action",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        opr = info.opr 
        if not opr :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Opr param missing",
                headers={"WWW-Authenticate": "Bearer"}
            )

        admin_id = user["user_id"]
        password_obj = await crud.get_password_data(db, admin_id)

        if not (await verify_password(info.password, password_obj.hashed_password, password_obj.salt)) :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                messege="You are not authorized to this Action | Password is Wrong",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user_id = info.user_id 
        role = info.new_role
        success_msg = None
        response = {}

        
        if opr == "role_update":
            new_role = None
            
            if Account.Role.USER == role :
                new_role = Account.Role.USER
            if Account.Role.ADMIN == role :
                new_role = Account.Role.ADMIN
            if Account.Role.SUPER_ADMIN == role :
                new_role = Account.Role.SUPER_ADMIN

            if new_role:
                update_info_map = {"role" : new_role}
                success_msg = "Role updated successfully"

        elif opr == "verify_user":
            update_info_map = {"is_verified" : Account.Verification.VERIFIED}
            success_msg = "User has been verified successfully"

        print(" OPR for this one is : " , opr  , update_info_map)
        if update_info_map :
            
            res = await crud.update_account_data(db, user_id, update_info_map)
            if res :
                content = {"status":"200OK", "user_id" : user_id, "messege" : success_msg}
                return content


    except Exception as ex :
        logging.exception("[MAIN][Exception in verify_user] {} ".format(ex))



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
  "created_time": "2023-09-18T12:30:48",
  "id": 1,
  "username": "test3",
  "phone": "123456711",
}