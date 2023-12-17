

class ResponseObject:
    def __init__(self, status = None, is_success = False , data = dict() , messege = ""):
        self.status = status
        self.is_success = is_success
        self.data = data 
        self.messege = messege