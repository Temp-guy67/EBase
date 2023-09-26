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
    email: str
    password: str 




class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class Order(BaseModel):
    user_id : int
    order_id : str 
    order_status : str
    payment_status : bool
    delivery_address : str 

class ResponseModel(BaseModel):
    status : int
    message : str 



class TestLogIn(BaseModel):
    email : str | None = None
    username : str 
    password : str
