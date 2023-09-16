from fastapi import Depends, FastAPI, HTTPException, status
from schemas import UserCreate, UserSignUp
from fastapi.middleware.cors import CORSMiddleware
from services import onStartService
from database import engine, Base, SessionLocal
from crud import get_user_by_email, create_user

import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your allowed origins (e.g., ["https://example.com"])
    allow_methods=["*"],  # Allow all HTTP methods or specify specific methods (e.g., ["GET", "POST"])
    allow_headers=["*"],  # Allow all headers or specify specific headers (e.g., ["Authorization"])
)

Base.metadata.create_all(bind=engine)

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
async def create_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
    try:
        print(" DATA RECEIVED : ", user)
        db_user = get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
        # print(" ENDED : ", user)
        return create_user(db=db, user=user)
    except Exception as ex :
        logging.exception("[main][Exception in create_user] {} ".format(ex))


# @app.get("/users/", response_model=list[schemas.User])
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users(db, skip=skip, limit=limit)
#     return users


# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user


# @app.post("/users/{user_id}/items/", response_model=schemas.Item)
# def create_item_for_user(
#     user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
# ):
#     return crud.create_user_item(db=db, item=item, user_id=user_id)




@app.get("/test")
async def hello():
    return {"message" : "working fine"}

# @app.post("/signup")
# async def signup(form_data:UserCreate):
#     try:
#         print(" Received user data ot sign up ", form_data)
#         # res =  await create_new_user(form_data)
#         # return res
#         return {"token" : "123455678"}
    
#     except Exception as ex :
#         logging.exception("[main][Exception in signup] {} ".format(ex))

    

@app.get("/login")
async def login():

    return {"message" : "working fine"}

@app.get("/getuser")
async def hello():
    return {"name" : "Taposh Paul", "age" : "19"}


@app.get("/order")
async def hello():
    return {"message" : "working fine"}



# async def create_new_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
#     try:
#         db_user = crud.get_user_by_email(db, email=user.email)
#         if db_user:
#             raise HTTPException(status_code=400, detail="Email already registered")
        
#         # db_user = crud.get_user_by_phone(db, phone=user.phone)
#         # if db_user:
#         #     raise HTTPException(status_code=400, detail="Phone Number already registered")
        
#         salt = await generate_salt()
#         hashed_password = await create_hashed_password(user.password, salt)

#         return await crud.create_user(db=db, user=user, salt=salt, hashed_password=hashed_password)
#     except Exception as ex :
#         logging.exception("[sql_app main][Exception in create_new_user] {} ".format(ex))


# def get_user(user_id: int, db: SessionLocal = Depends(get_db)):
#     try:
#         db_user = crud.get_user_by_id(db, user_id=user_id)
#         if db_user is None:
#             raise HTTPException(status_code=404, detail="User not found")
#         return db_user
#     except Exception as ex :
#         logging.exception("[main][Exception in signup] {} ".format(ex))


# async def is_user_already_signedup(email:str, phone : str):
#     try:
#         db = get_db()
#         db_user = crud.get_user_by_email(email, db)
#         if db_user:
#             return 1
#         db = get_db()
#         db_user = crud.get_user_by_phone(phone, db)
#         if db_user:
#             return 2
#         return 0
#     except Exception as ex :
#         logging.exception("[main][Exception in signup] {} ".format(ex))
    

    