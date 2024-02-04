from typing import Any, Optional
from fastapi import HTTPException, status


class CustomException(HTTPException):
    def __init__(
        self,
        status_code: Optional[int] = None ,
        detail: Any = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        if not status_code :
            status_code=status.HTTP_401_UNAUTHORIZED

        super().__init__(status_code=status_code, detail=detail, headers=headers)

    def __repr__(self) -> str:
        return {'data' : {}, 'is_success' : 'false', 'error' : f"(status_code={self.status_code!r}, detail={self.detail})"}
    

class Exceptions:
    REQUEST_LIMIT_EXHAUSTED="Request Limit reached"
    USER_NOT_FOUND="User Not Available"
    INCORRECT_EMAIL_PASSWORD="Incorrect email or password"
    ACCOUNT_CREATION_FAILED="Account Creation Failed"
    EMAIL_HAS_BEEN_REGISTERED="Email has been registered"
    USERNAME_HAS_BEEN_TAKEN="User name has been taken, Try with different User Name"
    PHONE_NUMBER_HAS_BEEN_REGISTERED="Phone number has been registered"
    CREDENTIAL_ERROR_EXCEPTION="Credential Error"
    WRONG_API="Wrong API"
    WRONG_IP="This IP is not configured for this API"
    WRONG_PASSWORD="Password provided is Wrong"
    SERVICE_NOT_VERIFIED='Your service request is not Verified yet, You can not make any action Now'
    USER_NOT_VERIFIED='Your account is not Verified yet , Kindly Contact Org Admin. You can not make any action Now'
    NOT_AUTHORIZED="You are not a Admin"
    API_KEY_UNAVAILABLE="Add right api_key in the header"
    TRYING_FROM_DIFFERENT_DEVICE="You are trying from different Device, Try login again"
    FAILED_TO_VALIDATE_CREDENTIALS="Failed to validate Token Credentials, Login Again"
    OPERATION_FAILED="Operaion Failed"
    USER_HAS_BEEN_DELETED="User Has been deleted, Contact Service Admin to reactive"

    # Order Exceptions
    FAILED_TO_CREATE_NEW_ORDER="Failed to Create Order"
    UNAVAILABLE_ORDER_STATUS="Unavailable Order Status"