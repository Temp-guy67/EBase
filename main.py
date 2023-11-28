from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services import onStartService
from host_app.database.database import Base, engine
import jwt, jwt.exceptions
import logging
from host_app.routes.user_routes import user_router
from host_app.routes.order_routes import order_router

app = FastAPI()

app.include_router(user_router)
app.include_router(order_router)


origins = ["http://localhost:3000"]  

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, 
    allow_methods=["*"],  # Allow all HTTP methods or specify specific methods (e.g., ["GET", "POST"])
    allow_headers=["*"],  # Allow all headers or specify specific headers (e.g., ["Authorization"])
)

Base.metadata.create_all(bind=engine)
        
@app.on_event("startup")
async def startService():
    await onStartService()

# ===============================ADMIN SPECIAL =====================================

# @app.get("/auth/getallorders")
# async def get_all_orders(user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
#     try:
#         if user["role"] == Account.Role.SUPER_ADMIN :
#             return await crud.get_all_orders(db)
#         else :
#             return HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="You are not authorized to this Action",
#                 headers={"WWW-Authenticate": "Bearer"}
#             )
#     except Exception as ex :
#         logging.exception("[MAIN][Exception in get_all_order] {} ".format(ex))



# @app.get("/auth/getalluser")
# async def get_all_user(user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
#     try:
#         if user["role"] == Account.Role.SUPER_ADMIN or user["role"] == Account.Role.ADMIN:
#             return await crud.get_all_users(db)
#         else :
#             return HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="You are not authorized to this Action",
#                 headers={"WWW-Authenticate": "Bearer"}
#             )
#     except Exception as ex :
#         logging.exception("[MAIN][Exception in get_all_userA] {} ".format(ex))


# @app.post("/auth/updateuser/")
# async def update_user_role(info: UserUpdate, user: UserInDB = Depends(get_current_active_user), db: Session = Depends(get_db)):
#     try:
#         print(" USER to action  is {} ".format(user))
#         if not (int(user["role"]) == Account.Role.SUPER_ADMIN or int(user["role"]) == Account.Role.ADMIN) :
#             return HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="You are not authorized to this Action",
#                 headers={"WWW-Authenticate": "Bearer"}
#             )
        
#         opr = info.opr 
#         if not opr :
#             return HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Opr param missing",
#                 headers={"WWW-Authenticate": "Bearer"}
#             )

#         admin_id = user["user_id"]
#         password_obj = await crud.get_password_data(db, admin_id)

#         if not (await verify_password(info.password, password_obj.hashed_password, password_obj.salt)) :
#             return HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 messege="You are not authorized to this Action | Password is Wrong",
#                 headers={"WWW-Authenticate": "Bearer"}
#             )

#         user_id = info.user_id 
#         role = info.new_role
#         success_msg = None
#         response = {}

        
#         if opr == "role_update":
#             new_role = None
            
#             if Account.Role.USER == role :
#                 new_role = Account.Role.USER
#             if Account.Role.ADMIN == role :
#                 new_role = Account.Role.ADMIN
#             if Account.Role.SUPER_ADMIN == role :
#                 new_role = Account.Role.SUPER_ADMIN

#             if new_role:
#                 update_info_map = {"role" : new_role}
#                 success_msg = "Role updated successfully"

#         elif opr == "verify_user":
#             update_info_map = {"is_verified" : Account.Verification.VERIFIED}
#             success_msg = "User has been verified successfully"

#         print(" OPR for this one is : " , opr  , update_info_map)
#         if update_info_map :
            
#             res = await crud.update_account_data(db, user_id, update_info_map)
#             if res :
#                 content = {"status":"200OK", "user_id" : user_id, "messege" : success_msg}
#                 return content


#     except Exception as ex :
#         logging.exception("[MAIN][Exception in verify_user] {} ".format(ex))


# TEST CODE FOR FRONTEND
# =========================================================================================================
@app.get("/test")
async def hello():
    return {"message" : "Hello Murali 😀"}


@app.post("/test/login")
async def login_test():
    try:
        return {"access_token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJcInRlc3QzXCIiLCJleHAiOjE2OTU3MTQzNzB9.LGXf2RVsbtrEiVTvQGRg3T1UzqmnEDEIQi8MF3AC-kI", "token_type" : "bearer"}
    
    except Exception as ex :
        logging.exception("[main][Exception in signup] {} ".format(ex))


@app.get("/test/getuser")
async def get_user():
    return {
  "email": "test3@testmail.com",
  "created_time": "2023-09-18T12:30:48",
  "id": 1,
  "username": "test3",
  "phone": "123456711",
}
