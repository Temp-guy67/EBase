from pydantic import BaseModel
from typing import Union


class User(BaseModel):
    email: str
    phone : str

class UserSignUp(User):
    username : Union[str, None] = None
    role : Union[str, None] = None


class UserInDB(User):
    hashed_password : str 
    salt : str
    id : int

class UserLogin(BaseModel):
    email: str
    password: str 

class UserSignUpResponse(User):
    user_id : str
    is_verified : int
    role : int
    username : str
    daily_request_left : Union[int, None] = None


class UserUpdate(BaseModel):
    email : Union[str, None] = None
    username : Union[str, None] = None
    phone : Union[str, None] = None
    new_password : Union[str, None] = None
    new_role : Union[int, None] = None
    opr : Union[str, None] = None
    password : str 


class UserDelete(BaseModel):
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
    order_status : Union[int, None] = None 
    order_quantity : Union[int, None] = None
    delivery_address : Union[str, None] = None
    receivers_mobile : Union[str, None] = None

class ResponseModel(BaseModel):
    status : int
    message : str 


class ServiceSignup(BaseModel):
    service_org : str
    service_name : str
    phone : str
    subscription_mode : Union[str, None] = None
    registration_mail : str 
    ip_ports :  Union[list, None] = None    

            




