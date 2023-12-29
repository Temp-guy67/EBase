
from fastapi import HTTPException,status
# This object will only be used in routes


class ResponseObject:
    def __init__(self, status = status.HTTP_401_UNAUTHORIZED, data = dict() , exception = None, daily_request_count_left = -1):
        self.status = status
        self.data = data 
        self.exception = exception
        self.daily_request_count_left = daily_request_count_left
        
    def set_status(self, status: str):
        self.status = status

    def set_exception(self, exception: HTTPException):
        self.exception = exception

    def set_data(self, data):
        self.data = data

    def set_status(self, status:str):
        self.status = status
    
    def set_daily_request_count_left(self, daily_request_count_left: int):
        self.daily_request_count_left = daily_request_count_left

    def set_status_and_exception(self, status:str, exception: HTTPException):
        self.status = status
        self.exception = exception

        
    def to_dict(self):
        return {
            "status" : self.status, 
            "is_success" : self.is_success,
            "data" : self.data,
            "message" : self.message,
            "exception" : self.exception,
            "daily_request_count_left" : self.daily_request_count_left
        }