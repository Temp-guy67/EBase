from fastapi import HTTPException, status


class Exceptions:
    REQUEST_LIMIT_EXHAUST = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Request Limit reached",
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

