from pydantic import BaseModel
from typing import Dict

class User(BaseModel):
    email: str
    phone : str
    username: str | None = None

class UserSignUp(User):
    password : str

class UserInDB(User):
    hashed_password : str 
    salt : str
    id : int

class UserLogin(BaseModel):
    username : str | None = None
    email: str | None = None
    password: str 

class UserSignUpResponse(User):
    user_id : str

class UserUpdate(BaseModel):
    user_id : str 
    email : str | None = None
    phone : str | None = None
    new_password : str | None = None
    password : str 


class UserDelete(BaseModel):
    user_id : str 
    email : str | None = None
    phone : str | None = None
    password : str 

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class OrderCreate(BaseModel):
    user_id : str
    product_id : str
    delivery_address : str 

class OrderToDB(OrderCreate):
    owner_id : int
    order_status : int | None = None
    payment_status : int | None = None

class OrderToClient(OrderToDB):
    order_id : str 

class OrderQuery(BaseModel):
    order_id : str 
    order_status : str | None = None 
    delivery_address : str | None = None


class ResponseModel(BaseModel):
    status : int
    message : str 


