import hashlib,string,random, logging
from sql_constants import CommonConstants

# signup_map = {**signup_model.model_dump()}   # to get from model object to dictionary
# test2 = UserSignUp.model_validate(test)  # to convert dictionary to Object( base model)


async def create_hashed_password(password, salt):
    try:
        concatenated_string = password + salt
        hash_object = hashlib.sha256()
        hash_object.update(concatenated_string.encode('utf-8'))
        hashed_password = hash_object.hexdigest()
        return hashed_password
    except Exception as ex :
        logging.exception("[util][Exception in signup] {} ".format(ex))



async def generate_salt(saltLength : int or None = None):
    try:
        if not saltLength :
            saltLength = CommonConstants.SALT_LENGTH
        characters = string.ascii_letters + string.digits + string.punctuation
        salt = ''.join(random.choice(characters) for _ in range(saltLength))
        return salt
    except Exception as ex :
        logging.exception("[util][Exception in signup] {} ".format(ex))


async def create_order_id(user_id : str):
    try :
        random = ''.join([random.choice(string.ascii_letters
            + string.digits) for n in range(32)])
        x = user_id[5:] + random
        return x
    
    except Exception as ex :
        logging.exception("[util][Exception in create_order_id] {} ".format(ex))






   

