from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from core.logger import logger
import traceback
from datetime import datetime

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle data validation errors (Pydantic) with a friendly summary.
    """
    error_details = exc.errors()
    logger.error("Validation error", path=request.url.path, errors=error_details)
    
    # Try to get the first specific error message
    try:
        first_error = error_details[0]
        field_name = str(first_error['loc'][-1]).replace('_', ' ').capitalize()
        error_type = first_error['type']
        
        if error_type == 'value_error.missing':
            msg = f"{field_name} is required."
        elif 'min_length' in error_type:
            limit = first_error.get('ctx', {}).get('limit_value', '?')
            msg = f"{field_name} must be at least {limit} characters long."
        elif error_type == 'value_error.email':
            msg = "Please provide a valid email address."
        else:
            msg = first_error.get('msg', "Invalid information provided.")
    except Exception:
        msg = "Please fill in all required information."

    # Emergency file logging for Antigravity visibility
    full_traceback = traceback.format_exc()
    try:
        with open("c:/Users/Sunil/OneDrive/Desktop/laborgro/backend/error_log.txt", "a") as f:
            f.write(f"\n--- VALIDATION ERROR {datetime.utcnow().isoformat()} ---\n")
            f.write(f"Path: {request.url.path}\n")
            f.write(f"Errors: {str(error_details)}\n")
            f.write(full_traceback)
            f.write("\n")
    except:
        pass

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": msg,
            "detail": "Data verification failed."
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

    full_traceback = traceback.format_exc()
    logger.error(
        "Internal Error", 
        path=request.url.path, 
        error=str(exc),
        traceback=full_traceback
    )

    # Emergency file logging for Antigravity visibility
    try:
        with open("c:/Users/Sunil/OneDrive/Desktop/laborgro/backend/error_log.txt", "a") as f:
            f.write(f"\n--- {datetime.utcnow().isoformat()} ---\n")
            f.write(f"Path: {request.url.path}\n")
            f.write(f"Error: {str(exc)}\n")
            f.write(full_traceback)
            f.write("\n")
    except:
        pass

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
    
    # Emergency file logging for Antigravity visibility
    try:
        with open("c:/Users/Sunil/OneDrive/Desktop/laborgro/backend/error_log.txt", "a") as f:
            f.write(f"\n--- HTTP ISSUE {datetime.utcnow().isoformat()} ---\n")
            f.write(f"Path: {request.url.path}\n")
            f.write(f"Status: {exc.status_code}\n")
            f.write(f"Detail: {exc.detail}\n")
            f.write("\n")
    except:
        pass

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )
