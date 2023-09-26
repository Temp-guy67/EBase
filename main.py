from fastapi import Depends, FastAPI, HTTPException, status
from schemas import UserSignUp, Token, TokenData, UserLogin, UserInDB, TestLogIn
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from services import onStartService
from database import engine, Base, SessionLocal
from crud import get_user_by_email, create_new_user, get_user_by_phone, get_user_by_username
from util import create_hashed_password
from sql_constants import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import logging
from datetime import datetime, timedelta
from typing import Annotated



# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your allowed origins (e.g., ["https://example.com"])
    allow_methods=["*"],  # Allow all HTTP methods or specify specific methods (e.g., ["GET", "POST"])
    allow_headers=["*"],  # Allow all headers or specify specific headers (e.g., ["Authorization"])
)

Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
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


@app.post("/signup")
async def sign_up(user: UserSignUp, db: Session = Depends(get_db)):
    try:
        db_user = get_user_by_email(db, email=user.email)
        if db_user:
            return HTTPException(status_code=400, detail="Email already registered")
        
        db_user = get_user_by_phone(db, phone=user.phone)
        if db_user:
            return HTTPException(status_code=400, detail="Phone already registered")

        return await create_new_user(db=db, user=user)

    except Exception as ex :
        logging.exception("[main][Exception in sign_up] {} ".format(ex))


async def user_login(user_email, password, db: Session = Depends(get_db)):
    try:
        db_user = get_user_by_email(db, email=user_email)
        
        if not db_user:
            return HTTPException(status_code=400, detail="User Not Available")
    
        res = await verify_password(db_user.hashed_password, db_user.salt, password)
        if not res :
            return HTTPException(status_code=401, detail="Invalid email and password")
        return db_user

    except Exception as ex :
        logging.exception("[main][Exception in login] {} ".format(ex))


async def verify_password(hashed_password : str, salt: str, user_password: str):
    try:
        temp_hashed_password = await create_hashed_password(user_password, salt)
        return temp_hashed_password == hashed_password

    except Exception as ex:
        logging.exception("[main][Exception in verify_password] {} ".format(ex))




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
        logging.exception("[main][Exception in create_access_token] {} ".format(ex))
        


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    except Exception as ex :
        logging.exception("[main][Exception in get_current_user] {} ".format(ex))
    db_user = get_user_by_username(db, username=token_data.username)
    if db_user is None:
        raise credentials_exception
    return db_user


async def get_current_active_user(current_user: Annotated[UserInDB, Depends(get_current_user)]):
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    try:
        user = await user_login(form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password",headers={"WWW-Authenticate": "Bearer"})
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as ex :
        logging.exception("[main][Exception in login_for_access_token] {} ".format(ex))

    


@app.get("/users/me/")
async def read_users_me(user: UserInDB = Depends(get_current_active_user)):
    try:
        return user

    except Exception as ex:
        logging.exception("[main][Exception in read_users_me] {} ".format(ex))
        
   


# TEST CODE FOR FRONTEND
# =========================================================================================================
@app.get("/test")
async def hello():
    return {"message" : "working fine"}


@app.post("/test/login")
async def login_test(form_data: TestLogIn):
    try:
        print(" Received user data on LOGIN ", form_data)
        return {"access_token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJcInRlc3QzXCIiLCJleHAiOjE2OTU3MTQzNzB9.LGXf2RVsbtrEiVTvQGRg3T1UzqmnEDEIQi8MF3AC-kI", "token_type" : "bearer"}
    
    except Exception as ex :
        logging.exception("[main][Exception in signup] {} ".format(ex))


@app.get("/test/getuser", response_model=UserInDB)
async def get_user():
    print(" LANDED in GETUSER TEST")
    return {
  "email": "test3@testmail.com",
  "salt": "3v9YWoLV",
  "created_time": "2023-09-18T12:30:48",
  "id": 1,
  "hashed_password": "0956c5c1ff5bcc838b1b02e01e1b3fd2953f59961bcb2a008693b5442d1f124b",
  "username": "test3",
  "phone": "123456711",
}