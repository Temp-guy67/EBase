from fastapi import Depends, HTTPException, status, APIRouter, Response
from fastapi.responses import JSONResponse
from host_app.common.response_object import ResponseObject
from host_app.database.schemas import UserInDB, OrderCreate, OrderQuery
from sqlalchemy.orm import Session
import logging
from host_app.database import crud
from host_app.database.database import get_db
from host_app.caching import redis_util
from host_app.caching.redis_constant import RedisConstant
from host_app.common import order_util
from host_app.routes import verification
from host_app.common.exceptions import CustomException,Exceptions


order_router = APIRouter(
    prefix='/order',
    tags=['order']
)


@order_router.post("/create")
async def create_order(order_info: OrderCreate, user: UserInDB = Depends(verification.get_current_active_user)):
    try: 
        logging.info("Data received for create_order : {} [user_id] {}".format(order_info, user["user_id"]))
        user_id, user_org = user["user_id"], user["service_org"]

        order = await order_util.create_order(user_id, user_org, order_info)
        
        if not order:
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.FAILED_TO_CREATE_NEW_ORDER).__repr__())

        return JSONResponse(status_code=401, content=ResponseObject(data=order).to_dict())
    
    except Exception as ex:
        logging.exception("[ORDER_ROUTES][Exception in create_order] {} ".format(ex))


@order_router.get("/")
async def get_order(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        logging.info("Data received for get_order [user_id] {}".format( user["user_id"]))
        respObj = ResponseObject()
        user_id = user["user_id"]
        user_org = user["service_org"]
        all_orders_obj = await order_util.get_all_orders(db, user_id, user_org)
        
        if not all_orders_obj:
            exp = CustomException(detail="Orders don't exits")
            respObj.set_exception(exp)
            return respObj

        respObj.set_status(status.HTTP_200_OK)
        respObj.set_data(all_orders_obj)

    except Exception as ex:
        logging.exception("[ORDER_ROUTES][Exception in order] {} ".format(ex))
    return respObj



@order_router.get("/{order_id}")
async def get_single_order_info(order_id: str, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        respObj = ResponseObject()
        user_id = user["user_id"]
        service_org = user["service_org"]
        order_obj = await order_util.get_single_order(db, user_id, order_id, service_org)
        
        if not order_obj:
            exp = CustomException(detail="Order doesn't exits")
            respObj.set_exception(exp)
            return respObj
        respObj.set_status(status.HTTP_200_OK)
        respObj.set_data(order_obj)

    except Exception as ex :
        logging.exception("[ORDER_ROUTES][Exception in get_single_order_info] {} ".format(ex))
    return respObj



# update and cancel and all
@order_router.post("/update")
async def update_order_status(order_query: OrderQuery, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        respObj = ResponseObject()
        user_id = user["user_id"]
        order_data = order_query.model_dump()
        service_org = user["service_org"]
        
        res = await order_util.update_order_object(db, user_id, order_data, service_org)
        
        if not res:
            exp = CustomException(detail="Failed to Update Order")
            respObj.set_exception(exp)
            return respObj
        
        respObj.set_status(status.HTTP_200_OK)
        respObj.set_data(res)
        return respObj
    
    except Exception as ex:
        logging.exception("[ORDER_ROUTES][Exception in update_order_status] {} ".format(ex))
    


# under construction
@order_router.get("/delete/{order_id}")
async def delete_order(order_id: str, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]

        if order_id  :
            status = crud.delete_order(db, order_id, user_id)
            if status :
                await redis_util.delete_from_redis(RedisConstant.ORDER_OBJ + order_id)
                return {"user_id" : user_id, "order_id" : order_id, "messege":"Order has been Deleted Sucessfully"}
            else :
                return {"user_id" : user_id, "order_id" : order_id, "messege":"Not Authorized"}
                
    except Exception as ex:
        logging.exception("[MAIN][Exception in delete_order] {} ".format(ex))

