from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from core.logger import logger
import traceback

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle data validation errors (Pydantic).
    """
    error_details = exc.errors()
    logger.error("Validation error", path=request.url.path, errors=error_details)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": error_details}
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle errors originating from SQLAlchemy/Database.
    """
    logger.error("Database error", path=request.url.path, description=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred. Please try again later."}
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for any unhandled application exceptions.
    """
    # Log the full traceback for critical inspection
    logger.error(
        "Unhandled exception", 
        path=request.url.path, 
        error=str(exc),
        traceback=traceback.format_exc()
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Our team has been notified."}
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Log and return predictable HTTP errors.
    """
    logger.warning("HTTP Exception", path=request.url.path, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
