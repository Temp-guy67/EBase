import hashlib,string,random, logging
from sql_constants import CommonConstants
from schemas import AccountModel

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
        logging.exception("[main][Exception in signup] {} ".format(ex))



async def generate_salt():
    try:
        saltLength = CommonConstants.SALT_LENGTH
        characters = string.ascii_letters + string.digits + string.punctuation
        salt = ''.join(random.choice(characters) for _ in range(saltLength))
        return salt
    except Exception as ex :
        logging.exception("[main][Exception in signup] {} ".format(ex))









