import logging
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from host_app.database import service_crud
from host_app.database.database import get_db
from host_app.common import common_util
from host_app.common.exceptions import Exceptions, CustomException



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
        print(" print res for update ", res)
        if res :
            api_key = res.api_key
            await common_util.delete_api_cache_from_redis(api_key)
            
            
    except Exception as ex :
        logging.exception("[VERIFICATION][Exception in update_service_info] {} ".format(ex))