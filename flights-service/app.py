from fastapi import FastAPI

app = FastAPI(
    title="Flights Service",
    description="Flight booking service for TiketQ platform",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"service": "Flights Service", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "flights-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
