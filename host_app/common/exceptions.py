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
        return {'data' : {}, 'is_success' : 'false', 'error' : f"(status_code={self.status_code!r}, detail={self.detail!r})"}
    

class Exceptions:
    REQUEST_LIMIT_EXHAUSTED="Request Limit reached"
    USER_NOT_FOUND="User Not Available"
    INCORRECT_EMAIL_PASSWORD="Incorrect email or password"
    ACCOUNT_CREATION_FAILED="Account Creation Failed"
    EMAIL_HAS_BEEN_REGISTERED="Email has been registered"
    PHONE_NUMBER_HAS_BEEN_REGISTERED="Phone number has been registered"
    CREDENTIAL_ERROR_EXCEPTION="Wrong API"
    WRONG_API="Wrong API"
    WRONG_IP="This IP is not configured for this API"
    SERVICE_NOT_VERIFIED="Your service request is not Verified yet, You can't make any action Now"
    NOT_AUTHORIZED="You are not a Admin"
    API_KEY_UNAVAILABLE="Add api_key in the header"

