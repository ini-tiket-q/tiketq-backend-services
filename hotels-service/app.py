from fastapi import FastAPI

app = FastAPI(
    title="Hotels Service",
    description="Hotel booking service for TiketQ platform",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"service": "Hotels Service", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hotels-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
