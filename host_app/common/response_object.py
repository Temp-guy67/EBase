


# This object will only be used in routes


class ResponseObject:
    def __init__(self, status = None, is_success = False , data = dict() , message = "", exception = None, daily_request_count_left = -1):
        self.status = status
        self.is_success = is_success
        self.data = data 
        self.message = message
        self.exception = exception
        self.daily_request_count_left = daily_request_count_left
        
    
    def set_data(self, data):
        self.data = data
        
    def to_dict(self):
        return {
            "status" : self.status, 
            "is_success" : self.is_success,
            "data" : self.data,
            "message" : self.message,
            "exception" : self.exception,
            "daily_request_count_left" : self.daily_request_count_left
        }