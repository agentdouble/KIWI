from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    response = JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )
    response.headers["Retry-After"] = str(exc.retry_after)
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    return response

AUTH_RATE_LIMIT = "5/minute"
UPLOAD_RATE_LIMIT = "10/hour"
API_RATE_LIMIT = "100/minute"
AI_RATE_LIMIT = "20/minute"