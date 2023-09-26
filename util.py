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




# async def authenticate_user(email: str, password: str, db: Session):
#     user = await get_user_by_email(db=db, email=email)

#     if not user:
#         return False

#     if not user.verify_password(password):
#         return False

#     return user


# async def create_token(user=user):
#     user_obj = _schemas.User.from_orm(user)

#     token = _jwt.encode(user_obj.dict(), JWT_SECRET)

#     return dict(access_token=token, token_type="bearer")


# async def get_current_user(
#     db: _orm.Session = _fastapi.Depends(get_db),
#     token: str = _fastapi.Depends(oauth2schema),
# ):
#     try:
#         payload = _jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
#         user = db.query(_models.User).get(payload["id"])
#     except:
#         raise _fastapi.HTTPException(
#             status_code=401, detail="Invalid Email or Password"
#         )

#     return _schemas.User.from_orm(user)






   

