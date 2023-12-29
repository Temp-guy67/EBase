import hashlib, string, random, logging, secrets
from host_app.database.sql_constants import CommonConstants

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


async def generate_salt(saltLength : int):
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
        ord_id = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(10)])
        x = user_id[5:] + "_" + ord_id
        return x
    
    except Exception as ex :
        logging.exception("[util][Exception in create_order_id] {} ".format(ex))


async def zipper(arr : list):
    try :
        s = "_!_".join(arr)
        # print("Zipped data ", s)
        return s
        
    except Exception as ex :
        logging.exception("[util][Exception in zipper] {} ".format(ex))
        
        
async def unzipper(s : str):
    try :
        arr = s.split("_!_")
        # print("UN Zipped data ", s)
        return arr
        
    except Exception as ex :
        logging.exception("[util][Exception in unzipper] {} ".format(ex))
    

async def generate_secure_random_string():
    length = 5
    letters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(letters) for _ in range(length))
   

