import redis,logging, json

redis_client = None
async def connect_redis():
    global redis_client
    
    # for AWS redis
    redis_client = redis.Redis(
    host='redis-14958.c212.ap-south-1-1.ec2.cloud.redislabs.com',
    port=14958,
    password='test1', decode_responses=True)

    # for aws put http://port
    # for local redis
    # redis_client = redis.Redis(host="localhost", port="6379", decode_responses=True)
    logging.info("Redis Inititated for this session Successfully {} ".format(redis_client))

# Convert the Redis Hash back to a Python dictionary
# python_dict = {key.decode('utf-8'): value.decode('utf-8') for key, value in stored_dict.items()}

# To set in Millis use `pexpire`
# In redis cloud they convert the byte to string and provides, but in out redis , they dont

def flush_all():
    redis_client.flushall()


def delete_from_redis(key:str):
    try :
        redis_client.delete(key)
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in delete_from_redis] {} ".format(ex))


async def is_exists(key : str):
    try:
        res = redis_client.exists(key)
        return True if res else False
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in is_exists] {} ".format(ex))


def set_hm(key:str, val:dict, ttl_in_sec: int = 3600):
    try:
        if key and val :
            json_string = json.dumps(val)
            set_str(key, json_string, ttl_in_sec)
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in set_hm] {} ".format(ex))
    

async def get_hm(key:str):
    try:
        json_string = await get_str(key)
        if json_string :
            return  json.loads(json_string)
    
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in get_hm] {} ".format(ex))


# String only
def set_str(key: str, val:str, ttl_in_sec:int = 3600):
    try:
        redis_client.set(key, val)
        redis_client.expire(key, ttl_in_sec)
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in set_str] {} ".format(ex))


async def get_str(key: str):
    try:
        byte_data = redis_client.get(key)
        return byte_data
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in get_str] {} ".format(ex))
    

# Set culture
def add_to_set(set_name:str, val:list, ttl_in_sec: int = 1800):
    try:
        redis_client.sadd(set_name,*val)
        redis_client.expire(set_name, ttl_in_sec)
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in add_to_set] {} ".format(ex))


async def get_set(set_name:str):
    try:
        set_items = redis_client.smembers(set_name)
        return set_items
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in get_set] {} ".format(ex))


async def is_member_in_set(set_name:str, item:str):
    try:
        is_member = redis_client.sismember(set_name, item)
        return is_member
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in is_member_is_set] {} ".format(ex))


async def remove_from_set(set_name:str, item:str):
    try:
        removed = redis_client.srem(set_name, item)
        return removed
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in remove_from_set] {} ".format(ex))


# hget     
def set_hset(key:str, field : str, val:str):
    try:
        redis_client.hset(key, field, val)
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in set_hget] {} ".format(ex))
    

async def get_hget(key:str, field : str):
    try:
        res = redis_client.hget(key, field)
        return res
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in get_hget] {} ".format(ex))


async def get_hgetall(key:str):
    try:
        all_data = redis_client.hgetall(key)
        return all_data
    except Exception as ex :
        logging.exception("[REDIS_UTIL][Exception in get_hgetall] {} ".format(ex))
