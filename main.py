import logging, prop_file
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
    allow_headers=["*"],  # Allow all headers or specify specific headers (e.g., ["Authorization"])
)


Base.metadata.create_all(bind=engine)
bucket = TokenBucket(capacity=10, refill_rate=5)

# Add the rate limiting middleware to the FastAPI app
app.add_middleware(RateLimiterMiddleware, bucket=bucket)
        
@app.on_event("startup")
async def startService():
    await onStartService()

@app.get("/")
async def hello():
    return {"message" : "Application loaded successfully"}


@app.get("/test/login")
async def login_test():
    try:
        res =  {"access_token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJcInRlc3QzXCIiLCJleHAiOjE2OTU3MTQzNzB9.LGXf2RVsbtrEiVTvQGRg3T1UzqmnEDEIQi8MF3AC-kI", "token_type" : "bearer"}
        return res
    
    except Exception as ex :
        logging.exception("[main][Exception in login_test] {} ".format(ex))

@app.get("/flsuh")
async def flush():
    try:
        redis_util.flush_all()
        print(" All data has been flushed")
    except Exception as ex :
        logging.exception("[main][Exception in flush] {} ".format(ex))




# import json
    
# @app.get("/redis")
# async def redis():
#     try:
        
#         # Sample dictionary
#         my_dict = {'name': 'John', 'age': 30, 'city': 'New York'}

#         # Serialize the dictionary to a JSON-formatted string
#         json_string = json.dumps(my_dict)

#         # Display the serialized string
#         print("Serialized String:", json_string ," type is  : => ", type(json_string))
        
#         # Deserialize the JSON-formatted string back to a dictionary
#         new_dict = json.loads(json_string)

#         # Display the deserialized dictionary
#         print("Deserialized Dictionary:", new_dict ," type is  : => ", type(new_dict))

        
    
#         redis_util.set_str("test", json_string, 300)
#         res = await redis_util.get_str("test")
#         dict_res = json.loads(res)
        
#         print("restuld => ", res, " type is  : => ", type(res) , " dict_res => " , dict_res , " type is  : => ", type(dict_res), dict_res["age"])
#     except Exception as ex :
#         logging.exception("[main][Exception in redis] {} ".format(ex))