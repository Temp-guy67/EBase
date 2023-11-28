from fastapi import Depends, HTTPException, status, APIRouter
from host_app.database.schemas import UserInDB, OrderCreate, OrderQuery
from sqlalchemy.orm import Session
import jwt, jwt.exceptions
import logging
from host_app.database import crud
from host_app.database.database import get_db
from host_app.caching import redis_util
from host_app.caching.redis_constant import RedisConstant
from host_app.common import util
from host_app.routes import verification


order_router = APIRouter(
    prefix='/order',
    tags=['order']
)


@order_router.post("/create")
async def create_order(order_info: OrderCreate, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try: 
        if not int(user["is_verified"]):
            return  HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sorry, You are not Verified yet",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user_id = user["user_id"]
        if order_info.owner_id == user_id:
            order = await crud.create_new_order(db, order_info)
            await redis_util.set_hm(RedisConstant.ORDER_OBJ + order["order_id"], order, 1800)

            if await redis_util.get_set(RedisConstant.USER_ORDERS + user_id):
                orders_list = await redis_util.get_set(RedisConstant.USER_ORDERS + user_id)
                orders_list.append(order["order_id"])
                await redis_util.add_to_set(RedisConstant.USER_ORDERS + user_id, orders_list)

            return order
        else :
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong Path",
                headers={"WWW-Authenticate": "Bearer"}
            )

    except Exception as ex:
        logging.exception("[main][Exception in create_order] {} ".format(ex))


@order_router.get("/")
async def order(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]
        all_orders_id = set()
        all_orders = []

        if not await redis_util.get_str(RedisConstant.USER_ORDERS + user_id) :
            all_orders = crud.get_all_orders_by_user(db, user["user_id"])
            for ele in all_orders:
                single_order = ele.to_dict()
                order_id = single_order["order_id"]
                all_orders_id.add(order_id)
                await redis_util.set_hm(RedisConstant.ORDER_OBJ + order_id, single_order, 1800)
            await redis_util.set_str(RedisConstant.USER_ORDERS + user_id, await util.zipper(all_orders_id))
            
        else :
            all_orders_id_str = await redis_util.get_str(RedisConstant.USER_ORDERS + user_id)
            all_orders_id = await util.unzipper(all_orders_id_str)
            if all_orders_id :
                for single_order_id in all_orders_id:
                    single_order_obj = await crud.get_single_order(db, single_order_id)
                    all_orders.append(single_order_obj)
        return all_orders

    except Exception as ex:
        logging.exception("[main][Exception in order] {} ".format(ex))
    return all_orders



@order_router.get("/{order_id}")
async def get_single_order_info(order_id: str, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        return await crud.get_single_order(db, user["user_id"], order_id)
    except Exception as ex :
        logging.exception("[main][Exception in get_single_order_info] {} ".format(ex))


# update and cancel and all
@order_router.post("/update")
async def update_order_status(order_query: OrderQuery, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    try:
        user_id = user["user_id"]
        order_data = order_query.model_dump()
        order_id = order_data["order_id"]
        
        if order_id  :
            updated_order_obj = await crud.update_order_status(db, order_id, order_data)
            await redis_util.set_hm(RedisConstant.ORDER_OBJ + order_id, updated_order_obj, 1800)
            return {"user_id" : user_id, "order_id" : order_id, "messege":"Order has been Updated Sucessfully"}
    
    except Exception as ex:
        logging.exception("[MAIN][Exception in update_order_status] {} ".format(ex))
    
    
    
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

