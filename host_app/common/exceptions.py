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

