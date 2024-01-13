
from fastapi import status, Response
import json
# This object will only be used in routes


class ResponseObject:
    def __init__(self, status = status.HTTP_200_OK, data = dict() , is_success = True, daily_request_count_left = -1):
        self.status = status
        self.data = data 
        self.is_success = is_success
        self.daily_request_count_left = daily_request_count_left
        
    def set_status(self, status: str):
        self.status = status

    def set_data(self, data):
        self.data = data
    
    def set_daily_request_count_left(self, daily_request_count_left: int):
        self.daily_request_count_left = daily_request_count_left

        
    def to_dict(self):
        return {
            "status" : self.status, 
            "is_success" : self.is_success,
            "data" : self.data,
            "daily_request_count_left" : self.daily_request_count_left
        }