from pydantic import BaseModel
from typing import Dict, Union
from pydantic import EmailStr
from typing import Union


class User(BaseModel):
    email: str
    phone : str
    service_org : str

class UserSignUp(User):
    password : str
    username : Union[str, None] = None
    role : Union[str, None] = None


class UserInDB(User):
    hashed_password : str 
    salt : str
    id : int

class UserLogin(BaseModel):
    username : Union[str, None] = None
    email: Union[str, None] = None
    password: str 

class UserSignUpResponse(User):
    user_id : str
    is_verified : int
    role : int
    username : str

class UserUpdate(BaseModel):
    user_id : str 
    email : Union[str, None] = None
    phone : Union[str, None] = None
    new_password : Union[str, None] = None
    new_role : Union[int, None] = None
    opr : Union[str, None] = None
    password : str 


class UserDelete(BaseModel):
    user_id : str 
    email : Union[str, None] = None
    phone : Union[str, None] = None
    password : str 

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Union[str, None] = None


class OrderCreate(BaseModel):
    product_id : str
    delivery_address : str 
    receivers_mobile : str 
    order_quantity : int


class OrderQuery(BaseModel):
    order_id : str 
    order_status : Union[int, None] = None 
    order_quantity : Union[int, None] = None
    delivery_address : Union[str, None] = None
    receivers_mobile : Union[str, None] = None

class ResponseModel(BaseModel):
    status : int
    message : str 


class ServiceSignup(BaseModel):
    service_name : str
    service_org : str 
    phone : str
    password : str
    subscription_mode : Union[str, None] = None
    registration_mail : str 
    ip_ports : list

            




