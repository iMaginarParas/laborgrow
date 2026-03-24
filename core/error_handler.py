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
    print(f"DEBUG: Validation Errors at {request.url.path}: {error_details}")
    logger.error("Validation error", path=request.url.path, errors=error_details)
    
    # Try to get the first specific error message
    try:
        first_error = error_details[0]
        field_name = str(first_error['loc'][-1]).replace('_', ' ').capitalize()
        error_type = first_error['type']
        
        if error_type == 'value_error.missing' or error_type == 'missing':
            msg = f"{field_name} is required."
        elif 'min_length' in error_type or 'too_short' in error_type:
            limit = first_error.get('ctx', {}).get('limit_value') or first_error.get('ctx', {}).get('min_length', '?')
            msg = f"{field_name} must be at least {limit} characters long."
        elif error_type == 'value_error.email' or error_type == 'greater_than':
            msg = "Please provide valid information."
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
            "message": "Data verification failed.",
            "detail": msg
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unhandled errors. Surfacing internal error details temporarily 
    for production debugging of schema issues.
    """
    err_str = str(exc)
    full_traceback = traceback.format_exc()
    
    # Still map 'schema cache' to 503 for standard handling, 
    # but include the actual exception details for visibility.
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if "schema cache" in err_str.lower() or "does not exist" in err_str.lower():
        status_code = status.HTTP_533_SERVICE_UNAVAILABLE # Using a custom code to distinguish from Railway 503

    logger.error(
        "Internal Error Details", 
        path=request.url.path, 
        error=err_str,
        traceback=full_traceback
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": "Marketplace Error",
            "detail": err_str,
            "traceback": full_traceback[:500] # Truncated for response
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
