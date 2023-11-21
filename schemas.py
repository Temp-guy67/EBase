from pydantic import BaseModel
from typing import Dict
from pydantic import EmailStr
from typing import Union

class User(BaseModel):
    email: str
    phone : str
    username: Union[str, None] = None

class UserSignUp(User):
    password : str

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
    owner_id : str
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


