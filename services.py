import logging, os
from host_app.caching.redis_util import connect_redis
from datetime import datetime

async def onStartService():
    configure_logging()
    await connect_redis()


# Level We have  -> debug,info,warning,error,critical
def configure_logging():
    log_folder = '/host_app/logs/log_files'  # Change this to the desired folder path
    os.makedirs(log_folder, exist_ok=True)
    
    date_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_folder, f'app_{date_time_str}.log')

    # Create the log folder if it doesn't exist
    
    logging.basicConfig(
        filename=log_file,
        filemode='w' ,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("")
    logging.info("")
    logging.info("Logger Inititated for this session ")
    logging.info("")