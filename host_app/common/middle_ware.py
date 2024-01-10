from fastapi import Request, HTTPException
from host_app.common.token_bucket import TokenBucket
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
from fastapi.responses import JSONResponse



class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, bucket: TokenBucket):
        super().__init__(app)
        self.bucket = bucket  # Initialize the middleware with a token bucket

    async def dispatch(self, request: Request, call_next):
        # Process each incoming request
        if self.bucket.take_token():
            # If a token is available, proceed with the request
            return await call_next(request)
        # If no tokens are available, return a 429 error (rate limit exceeded)
        return JSONResponse(status_code=400, content={"Messege" : "Beyond limit"})
