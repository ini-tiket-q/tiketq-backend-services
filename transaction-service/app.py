import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import logging

from adapters.db import Base, engine
from adapters.audit_middleware import AuditLoggingMiddleware, TransactionContextMiddleware
from adapters.audit_logger import audit_logger, AuditEventType
from routes import payments, transactions, orders, reports

# Configure comprehensive logging with structured format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/transaction-service.log') if os.getenv("LOG_FILE") else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security scheme for JWT Bearer token
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Transaction Service...")
    audit_logger.log_security_event(
        event_type=AuditEventType.AUTHENTICATION_SUCCESS,
        message="Transaction Service starting up",
        details={"service": "transaction-service", "version": "1.0.0"}
    )
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        audit_logger.log_security_event(
            event_type=AuditEventType.AUTHENTICATION_SUCCESS,
            message="Database initialization completed",
            details={"database_status": "ready"}
        )
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        audit_logger.log_error(
            error=e,
            context={"operation": "database_initialization"}
        )
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Transaction Service...")
    audit_logger.log_security_event(
        event_type=AuditEventType.AUTHENTICATION_SUCCESS,
        message="Transaction Service shutting down gracefully"
    )

# Create FastAPI application
app = FastAPI(
    title="Transaction Service",
    description="Transaction management service for TiketQ platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"}
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Transaction Service",
        version="1.0.0",
        description="Transaction management service for TiketQ platform",
        routes=app.routes,
    )
    
    # Add security definitions
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token in the format: Bearer <token>"
        }
    }
    
    # Apply security globally to all endpoints
    openapi_schema["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Set the custom OpenAPI schema
app.openapi = custom_openapi

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add audit logging middleware
app.add_middleware(
    AuditLoggingMiddleware,
    excluded_paths=["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico", "/"]
)

# Add transaction context middleware  
app.add_middleware(TransactionContextMiddleware)

# Register routers (reports first to avoid path conflicts with parameterized routes)
app.include_router(reports.router)      # Reports routes must come first
app.include_router(payments.router)
app.include_router(transactions.router)
app.include_router(orders.router)

# Health check endpoint
@app.get("/transactions/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "transaction-service",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/transactions")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Transaction Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )