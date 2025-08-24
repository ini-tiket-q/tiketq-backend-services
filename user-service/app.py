from fastapi import FastAPI
from routes.user_routes import router

app = FastAPI(
    title="User Service",
    description="User profile management service for TiketQ platform",
    version="1.0.0"
)

app.include_router(router)

@app.get("/")
async def root():
    return {"service": "User Service", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000) 