from typing import Any, Optional
from fastapi import HTTPException, status


class CustomException(HTTPException):
    def __init__(
        self,
        status_code: status.HTTP_401_UNAUTHORIZED,
        detail: Any = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        
class Exceptions:
    REQUEST_LIMIT_EXHAUSTED = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Request Limit reached",
        headers={"WWW-Authenticate": "Bearer"},
    )

    EMAIL_HAS_BEEN_REGISTERED = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email has been registered",
        headers={"WWW-Authenticate": "Bearer"},
    )

    PHONE_NUMBER_HAS_BEEN_REGISTERED = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phone number has been registered",
        headers={"WWW-Authenticate": "Bearer"},
    )

    CREDENTIAL_ERROR_EXCEPTION = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Wrong API",
        headers={"WWW-Authenticate": "Bearer"},
    )

    WRONG_API = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Wrong API",
        headers={"WWW-Authenticate": "Bearer"},
    )

    WRONG_IP = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="This IP is not configured for this API",
        headers={"WWW-Authenticate": "Bearer"},
    )

    SERVICE_NOT_VERIFIED = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your service request is not Verified yet, You can't make any action Now",
        headers={"WWW-Authenticate": "Bearer"},
    )

    NOT_AUTHORIZED = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not a Admin",
        headers={"WWW-Authenticate": "Bearer"},
    )

