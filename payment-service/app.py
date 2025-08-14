from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import router dengan jelas
from routes.payment import router as payment_router

app = FastAPI(
    title="TiketQ Payment Service",
    description="Payment processing service for TiketQ platform using Midtrans",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include payment router dengan explicit import
app.include_router(payment_router, prefix="/payments", tags=["payments"])

@app.get("/", tags=["root"])
async def root():
    return {
        "service": "TiketQ Payment Service",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "payment-service"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
