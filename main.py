import logging, prop_file
from host_app.mail_manager.config import send_email_to_client
from fastapi import FastAPI
from services import onStartService
from fastapi.middleware.cors import CORSMiddleware
from host_app.database.database import Base, engine
from host_app.routes.auth_routes import auth_router
from host_app.routes.user_routes import user_router
from host_app.common.token_bucket import TokenBucket
from host_app.routes.order_routes import order_router
from host_app.routes.public_routes import public_router
from host_app.routes.services_routes import service_router
from host_app.common.middle_ware import RateLimiterMiddleware
from host_app.caching import redis_util

app = FastAPI(title=prop_file.TITLE, summary=prop_file.SUMMARY, description=prop_file.DESCRIPTION, version=prop_file.VERSION, openapi_tags=prop_file.TAGS_METADATA, redoc_url=None)

app.include_router(public_router)
app.include_router(user_router)
app.include_router(order_router)
app.include_router(service_router)
app.include_router(auth_router)


origins = ["http://localhost:3000"]  

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, 
    allow_methods=["*"],  # Allow all HTTP methods or specify specific methods (e.g., ["GET", "POST"])
    allow_headers=["*"],  # Allow all headers or specify specific headers (e.g., ["Authorization"])
)


Base.metadata.create_all(bind=engine)
bucket = TokenBucket(capacity=20, refill_rate=15)

# Add the rate limiting middleware to the FastAPI app
app.add_middleware(RateLimiterMiddleware, bucket=bucket)
        
@app.on_event("startup")
async def startService():
    await onStartService()

@app.get("/")
async def hello():
    return {"message" : "Application loaded successfully, Kindly use the right endpoint"}


@app.get("/test/login")
async def login_test():
    try:
        res =  {"access_token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJcInRlc3QzXCIiLCJleHAiOjE2OTU3MTQzNzB9.LGXf2RVsbtrEiVTvQGRg3T1UzqmnEDEIQi8MF3AC-kI", "token_type" : "bearer"}
        return res
    
    except Exception as ex :
        logging.exception("[main][Exception in login_test] {} ".format(ex))


@app.get("/redis_check")
async def redis_check():
    redis_util.set_str("arghya","working")
    res = await redis_util.get_str("arghya")
    return {"response" : res}

# @app.get("/mail")
# async def redis_check():
#     user = {"username" : "Arghya", "order_id" : "1234", "email" : "profiletemp66@gmail.com", "status" : "IN_TRANSIT"}
#     send_email_to_client(4, user)