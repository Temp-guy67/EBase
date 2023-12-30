
from host_app.caching import redis_util

async def redis_set_test():
    arr = ["a", "b", "c"]
    arr = set(arr)
    await redis_util.add_to_set("TEST1", arr,100)
    # await redis_util.add_to_set("TEST1", ["e","f","b"],100)
    a2 = await redis_util.get_set("TEST1")
    is_member_i = await redis_util.is_member_in_set("TEST1", "c")
    print("TEST RESULT ", a2, is_member_i , " TYPE OF ", type(a2))
    arr2 = list(a2)
    print( " TYPE OF after type cast ", type(arr2))
    await redis_util.remove_from_set("TEST1", "c")
    
    a2 = await redis_util.get_set("TEST1")
    is_member_i = await redis_util.is_member_in_set("TEST1", "c")
    print("TEST RESULT after removal ", a2,   is_member_i)