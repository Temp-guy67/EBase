from pydantic import BaseModel
from typing import Dict

class UserSignUp(BaseModel):
    email: str
    phone : str
    username: str | None = None

class UserCreate(UserSignUp):
    password: str 
    
class AccountModel(UserSignUp):
    salt: str 
    hashed_password: str 

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: str
    password: str 


class Token(BaseModel):
    token : str




# class Order(BaseModel):
#     user_id : int
#     order_id : str 
#     order_status : str
#     payment_status : bool
#     delivery_address : str 

# class ResponseModel(BaseModel):
#     status : int
#     message : str 


