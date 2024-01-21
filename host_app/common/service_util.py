import logging
from fastapi import Depends
from sqlalchemy.orm import Session
from host_app.database import service_crud
from host_app.database.database import get_db
from host_app.common import common_util



# under supervision
async def update_service_info(service_id: int, service_update_data: dict, db: Session = Depends(get_db)):
    try:
        # service name and IP ports
        possible_update = ["service_name", "ip_ports"]
        service_update_map = dict()
        
        for k,v in service_update_data.items():
            if k in possible_update :
                if type(v) != str :
                    v = str(v)
                service_update_map[k] = v
        await service_crud.update_service_data(db, service_id, service_update_map)
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in update_service_info] {} ".format(ex))
        

async def verify_service(service_id: int, db: Session ):
    try:
        service_update_map = dict()
        service_update_map["is_verified"] = 1
        res = await service_crud.update_service_data(db, service_id, service_update_map)
        if res :
            await common_util.delete_api_cache_from_redis(res.api_key)
            return {"message" : "Service Updated"}
            
            
    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in update_service_info] {} ".format(ex))
        

async def verify_user(user_id: int, db: Session ):
    try:
        account_update_map = dict()
        account_update_map["is_verified"] = 1
        res = await common_util.update_account_info(user_id, account_update_map, db) 
        return res   
            
    except Exception as ex :
        logging.exception("[SERVICE_UTIL][Exception in verify_user] {} ".format(ex))