from typing import Annotated
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials, APIKeyHeader
from services import onStartService
from host_app.database.database import Base, engine
import logging
from host_app.routes.user_routes import user_router
from host_app.routes.order_routes import order_router
from host_app.routes.auth_routes import auth_router
from host_app.routes.public_routes import public_router
from host_app.routes.services_routes import service_router
from host_app.logs import log_manager

app = FastAPI(debug=True , title="Cruxx", summary="Ecommerce Backend as service", description="sadsdadasdadad")

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

security = HTTPBearer()
api_he = APIKeyHeader(name="api_key")


@app.get("/test_method")
def read_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)], api_key : str = Depends(api_he)):
    print(" CREDENTIAL IS  ", credentials.credentials , " API KEY ", api_key)
    return {"token": credentials, "api_key" : api_key}


@app.get("/")
async def hello():
    return {"message" : "Entry Screen"}

@app.get("/logs")
async def read_logs():
    res = await log_manager.read_logs()
    return res


@app.get("/test/login")
async def login_test():
    try:
        res =  {"access_token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJcInRlc3QzXCIiLCJleHAiOjE2OTU3MTQzNzB9.LGXf2RVsbtrEiVTvQGRg3T1UzqmnEDEIQi8MF3AC-kI", "token_type" : "bearer"}
        return res
    
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



class FixedContentQueryChecker:
    def __init__(self, fixed_content: str):
        
        self.fixed_content = fixed_content

    def __call__(self, q: str = ""):
        print(" Fixed content YOYOYOYOYO ", self.fixed_content)
        if q:
            return self.fixed_content in q
        return False


checker = FixedContentQueryChecker("/query")


@app.get("/query")
async def read_query_check(fixed_content_included: Annotated[bool, Depends(checker)]):
    return {"fixed_content_in_query": fixed_content_included}