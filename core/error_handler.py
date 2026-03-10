from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from core.logger import logger
import traceback

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle data validation errors (Pydantic) with a friendly summary.
    """
    error_details = exc.errors()
    logger.error("Validation error", path=request.url.path, errors=error_details)
    
    # Extract just the field names for a cleaner message
    missing_fields = [str(err['loc'][-1]) for err in error_details if err['type'] == 'value_error.missing']
    
    msg = "Please fill in all required information."
    if missing_fields:
        msg = f"Incomplete information. Please check: {', '.join(missing_fields)}"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": msg,
            "detail": "Data verification failed. Please check your input."
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unhandled errors, mapping raw database errors to polite messages.
    """
    err_str = str(exc).lower()
    
    # Determine the friendliest message based on the internal error
    if "schema cache" in err_str or "does not exist" in err_str or "relation" in err_str:
        friendly_msg = "Our marketplace is currently undergoing a scheduled update. Please try again in a few minutes."
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif "connection" in err_str or "timeout" in err_str:
        friendly_msg = "We're having trouble connecting to our services. Please check your internet and try again."
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        friendly_msg = "Something went wrong on our end. We've been notified and are looking into it!"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    logger.error(
        "Internal Error", 
        path=request.url.path, 
        error=str(exc),
        traceback=traceback.format_exc()
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": friendly_msg
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standardize HTTP errors with a consistent 'message' field.
    """
    logger.warning("HTTP Issue", path=request.url.path, detail=exc.detail)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )
