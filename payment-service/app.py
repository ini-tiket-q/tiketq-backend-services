from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from routes.payment import router as payment_router

load_dotenv()

app = FastAPI(
    title="TiketQ Payment Service",
    description="Payment processing service for TiketQ platform with Midtrans integration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payment_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "payment-service"}
@app.get("/", tags=["root"])
async def root():
    return {
        "service": "TiketQ Payment Service",
        "version": "1.0.0",
        "documentation": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
