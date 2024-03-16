import hashlib, string, random, logging, secrets
from host_app.common.constants import CommonConstants

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



async def zipper(arr : list):
    try :
        if len(arr) > 1 :
            s = "_!_".join(arr)
        else :
            s = arr[0]
        return s
        
    except Exception as ex :
        logging.exception("[util][Exception in zipper] {} ".format(ex))
        
        
async def unzipper(s : str):
    try :
        arr = s.split("_!_")
        return arr
        
    except Exception as ex :
        logging.exception("[util][Exception in unzipper] {} ".format(ex))
    

async def generate_secure_random_string():
    length = 5
    letters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(letters) for _ in range(length))
   
# async def create_org():
#     try:
        
#         while True :
#             org = 

#     except Exception as ex :
#         logging.exception("[PUBLIC_ROUTES][Exception in create_org] {} ".format(ex))

async def create_otp():
    return random.randint(10000,99999)
