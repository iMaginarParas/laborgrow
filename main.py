from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import time
import uvicorn

# Strategic Production Imports
from config.settings import settings
from core.logger import logger
from core.error_handler import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
    http_exception_handler
)
from routers import (
    auth_router,
    workers_router,
    categories_router,
    bookings_router,
    jobs_router,
    admin_router
)

# Application Initialization
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- MIDDLEWARE STACK ---

# Enable CORS for cross-platform integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Structured middleware to log performance and metadata for every incoming request.
    """
    start_time = time.time()
    
    response: Response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        "Inbound request processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(process_time * 1000, 2)
    )
    
    return response

# --- EXCEPTION HANDLERS ---

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
# Note: HTTPException handler is added automatically by FastAPI, 
# but we can override it if desired using the imported http_exception_handler.

# --- ROUTE REGISTRATION (API V1) ---

# We nest all production routes under the /api/v1 version prefix
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}")
app.include_router(workers_router, prefix=f"{settings.API_V1_STR}")
app.include_router(categories_router, prefix=f"{settings.API_V1_STR}")
app.include_router(bookings_router, prefix=f"{settings.API_V1_STR}")
app.include_router(jobs_router, prefix=f"{settings.API_V1_STR}")
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}")

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
