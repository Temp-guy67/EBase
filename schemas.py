from pydantic import BaseModel
from typing import Dict
from pydantic import EmailStr

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
    is_verified : int
    role : int

class UserUpdate(BaseModel):
    user_id : str 
    email : str | None = None
    phone : str | None = None
    new_password : str | None = None
    new_role : int | None = None
    opr : str | None = None
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
    email: str | None = None


class OrderCreate(BaseModel):
    owner_id : str
    product_id : str
    delivery_address : str 
    receivers_mobile : str 
    order_quantity : int


class OrderQuery(BaseModel):
    order_id : str 
    order_status : int | None = None 
    order_quantity : int | None = None
    delivery_address : str | None = None
    receivers_mobile : str | None = None

class ResponseModel(BaseModel):
    status : int
    message : str 


