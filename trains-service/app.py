from fastapi import FastAPI

app = FastAPI(
    title="Trains Service",
    description="TiketQ Trains Service API",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Trains Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "trains"}