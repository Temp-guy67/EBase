from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse
from host_app.common.response_object import ResponseObject
from host_app.database.schemas import UserInDB, OrderCreate
from sqlalchemy.orm import Session
import logging
from host_app.database import models
from host_app.database.database import get_db
from host_app.common import order_util
from host_app.routes import verification
from host_app.common.exceptions import CustomException,Exceptions


order_router = APIRouter(
    prefix='/order',
    tags=['order']
)


@order_router.post("/create", summary=" To create a new order")
async def create_order(order_info: OrderCreate, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    """
    To Create a new order :
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)
    - **X-Access-Token**: `required` in Header (Just put your token you got by Login response header. that in authorize box on top right)

    *Body:*
    - **product_id**: `required` Product_ID must be start with "prd". e.g: prd_123.
    - **delivery_address**: `required`
    - **receivers_mobile**: `required`
    - **order_quantity**: `required` in int

    *Response:*
    - Response Body :
        **Success Response of Order Object or any issue. Check mail for order confirmation**
    """
    

    try: 
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        logging.info("Data received for create_order : {} [user_id] {}".format(order_info, user["user_id"]))
        user_id, user_org = user["user_id"], user["service_org"]
        prd_check = await product_id_validateion(order_info.product_id)

        if not prd_check:
            return JSONResponse(status_code=401, content=CustomException(detail="INVALID PRODUCT ID PATTERN").__repr__())

        order = await order_util.create_order(db, user_id, user_org, order_info)
        if not order:
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.FAILED_TO_CREATE_NEW_ORDER).__repr__())

        return JSONResponse(status_code=200, content=ResponseObject(data=order).to_dict())
    
    except Exception as ex:
        logging.exception("[ORDER_ROUTES][Exception in create_order] {} ".format(ex))


@order_router.get("/", summary="To get all order created by this user")
async def get_orders(user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    """
    To get all order created by this user:
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)
    - **X-Access-Token**: `required` in Header (Just put your token you got by Login response header. that in authorize box on top right)

    *Body:*
    - Nothing

    *Response:*
    - Response Body :
        **All the Order created by the user **
    """
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        logging.info("Data received for get_orders [user_id] {}".format( user["user_id"]))
        user_id, user_org = user["user_id"], user["service_org"]

        all_orders_obj = await order_util.get_all_orders(db, user_id, user_org)
        if not all_orders_obj:
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.OPERATION_FAILED).__repr__())
        
        return JSONResponse(status_code=200, content=ResponseObject(data=all_orders_obj).to_dict())

    except Exception as ex:
        logging.exception("[ORDER_ROUTES][Exception in get_orders] {} ".format(ex))


@order_router.get("/{order_id}", summary="To get any specific order created by this user")
async def get_single_order_info(order_id: str, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    """
    To get any specific order created by this user:
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)
    - **X-Access-Token**: `required` in Header (Just put your token you got by Login response header. that in authorize box on top right)

    *Body:*
    - Nothing

    *Response:*
    - Response Body :
        **the Order created by the user **
    """
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        logging.info("Data received for get_single_order_info [user_id] {}".format( user["user_id"]))
        user_id, user_org = user["user_id"], user["service_org"]

        order_obj = await order_util.get_single_order(db, order_id, user_id, user_org)
        if not order_obj:
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.OPERATION_FAILED).__repr__())
        
        return JSONResponse(status_code=200, content=ResponseObject(data=order_obj).to_dict())

    except Exception as ex :
        logging.exception("[ORDER_ROUTES][Exception in get_single_order_info] {} ".format(ex))


@order_router.get("/cancel/{order_id}", summary="To cancel any order")
async def cancel_order(order_id: str, user: UserInDB = Depends(verification.get_current_active_user), db: Session = Depends(get_db)):
    """
    To Cancel any specific order created by this user:
    *Header:*
    - **X-Api-key**: `required` in Header (Just put your api key that in authorize box on top right)
    - **X-Access-Token**: `required` in Header (Just put your token you got by Login response header. that in authorize box on top right)

    *Body:*
    - Nothing

    *Response:*
    - Response Body :
        **Success Response **
    """
    try:
        if not isinstance(user, dict):
            return JSONResponse(status_code=401, content=CustomException(detail=user).__repr__())
        
        logging.info("Data received for cancel_order [user_id] {}".format( user["user_id"]))
        user_id, user_org = user["user_id"], user["service_org"]

        order_data = dict()
        order_data["order_status"] = models.Orders.OrderStatus.CANCELED
        order_obj = await order_util.update_order_object(db, user_id, order_id, order_data, user_org)
        if not order_obj:
            return JSONResponse(status_code=401, content=CustomException(detail=Exceptions.OPERATION_FAILED).__repr__())
        
        return JSONResponse(status_code=200, content=ResponseObject(data={"message" : "Order canceled successfully"}).to_dict())
                
    except Exception as ex:
        logging.exception("[ORDER_ROUTES][Exception in cancel_order] {} ".format(ex))


# helper method
async def product_id_validateion(product_id : str):
    if product_id :
        x = product_id.split("_")
        if len(x) == 2 and x[0] == "prd":
            return True
    return False