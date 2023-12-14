import logging
from host_app.caching import redis_util

async def update_user_details_int_redis(user_id:str, access_token: str , user_obj: dict):
    try :
        await redis_util.set_hm(user_id, user_obj)
        redis_util.set_str(access_token, user_id)

    except Exception as ex :
        logging.exception("[USER_UTIL][Exception in update_user_details_int_redis] {} ".format(ex))