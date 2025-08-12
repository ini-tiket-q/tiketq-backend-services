from fastapi import FastAPI

app = FastAPI(
    title="PPOB Service",
    description="PPOB service for TiketQ platform",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"service": "PPOB Service", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ppob-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
