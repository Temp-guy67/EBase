from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services import onStartService
from host_app.database.database import Base, engine
import jwt, jwt.exceptions
import logging
from host_app.routes.user_routes import user_router
from host_app.routes.order_routes import order_router
from host_app.routes.auth_routes import auth_router
from host_app.routes.public_routes import public_router
from host_app.routes.services_routes import service_router


app = FastAPI()

app.include_router(user_router)
app.include_router(order_router)
app.include_router(auth_router)
app.include_router(public_router)
app.include_router(service_router)


origins = ["http://localhost:3000"]  

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, 
    allow_methods=["*"],  # Allow all HTTP methods or specify specific methods (e.g., ["GET", "POST"])
    allow_headers=["*"],  # All-ow all headers or specify specific headers (e.g., ["Authorization"])
)

Base.metadata.create_all(bind=engine)
        
@app.on_event("startup")
async def startService():
    await onStartService()


@app.get("/")
async def hello():
    return {"message" : "Entry Screen"}

@app.get("/test")
async def hello():
    return {"message" : "Hello Boss"}


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
