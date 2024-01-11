

class ContentObject:
    def __init__(self, data : dict = None, details : str = None, is_success: bool = False):
        self.data = data
        self.details = details 
        self.is_success = is_success
    
    def set_data(self, data: dict):
        self.data = data

    def set_details(self, details: str):
        self.details = details

    def set_success_status(self, is_success: bool):
        self.is_success = is_success

    
    def to_string(self):
        return {
            'self.data' : self.data,
            'self.details' : self.details,
            'self.is_success' : self.is_success,
        }