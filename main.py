from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import time
import uvicorn
import os
from starlette.exceptions import HTTPException as StarletteHTTPException

# Strategic Production Imports
from config.settings import settings
from core.logger import logger
from database import init_supabase
from core.error_handler import (
    validation_exception_handler,
    generic_exception_handler,
    http_exception_handler
)
from routers import (
    auth_router,
    workers_router,
    categories_router,
    bookings_router,
    jobs_router,
    admin_router,
    applications_router,
    reviews_router,
    hire_router,
    worker_dashboard_router,
    notifications_router,
    chat_router,
    admin_auth_router,
    admin_control_center_router,
    admin_users_router,
    admin_workers_router,
    admin_bookings_router
)

# Application Initialization
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
async def startup_event():
    """
    Bootstrap the application resources.
    """
    init_supabase()
    logger.info("Application bootstrap complete", status="ready")

# --- MIDDLEWARE STACK ---

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Structured middleware to log performance and metadata for every incoming request.
    """
    # Print for immediate terminal visibility
    print(f"DEBUG: {request.method} {request.url.path}")
    
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log status code to terminal
    print(f"DEBUG: Result {response.status_code} path {request.url.path}")
    
    logger.info(
        "Inbound request processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(process_time * 1000, 2)
    )
    
    return response

# Enable CORS for cross-platform integration
# In development, we allow all origins matching localhost/127.0.0.1 on any port.
# Outer-most middleware (last added)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*", # Total wildcard for dev bypass
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- EXCEPTION HANDLERS ---

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# --- ROUTE REGISTRATION (API V1) ---

# We nest all production routes under the /api/v1 version prefix
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}")
app.include_router(workers_router, prefix=f"{settings.API_V1_STR}")
app.include_router(categories_router, prefix=f"{settings.API_V1_STR}")
app.include_router(bookings_router, prefix=f"{settings.API_V1_STR}")
app.include_router(jobs_router, prefix=f"{settings.API_V1_STR}")
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}")
app.include_router(applications_router, prefix=f"{settings.API_V1_STR}")
app.include_router(reviews_router, prefix=f"{settings.API_V1_STR}")
app.include_router(hire_router, prefix=f"{settings.API_V1_STR}")
app.include_router(worker_dashboard_router, prefix=f"{settings.API_V1_STR}")
app.include_router(notifications_router, prefix=f"{settings.API_V1_STR}")
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}")
app.include_router(admin_auth_router, prefix=f"{settings.API_V1_STR}/admin")
app.include_router(admin_control_center_router, prefix=f"{settings.API_V1_STR}")
app.include_router(admin_users_router, prefix=f"{settings.API_V1_STR}")
app.include_router(admin_workers_router, prefix=f"{settings.API_V1_STR}")
app.include_router(admin_bookings_router, prefix=f"{settings.API_V1_STR}")

@app.get("/")
async def root():
    """
    Service landing page for health verification.
    """
    return {
        "message": f"LaborGrow Production API Gateway",
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "online"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
