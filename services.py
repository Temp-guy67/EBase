import logging
from redis_util import connect_redis

async def onStartService():
    # configure_logging()
    await connect_redis()


# Level We have  -> debug,info,warning,error,critical
# def configure_logging():
#     logging.basicConfig(
#         filename='app.log',
#         filemode='w' ,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )
#     logging.getLogger().setLevel(logging.DEBUG)
#     logging.info("")
#     logging.info("")
#     logging.info("Logger Inititated for this session ")