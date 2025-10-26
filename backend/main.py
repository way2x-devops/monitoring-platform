from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Monitoring Platform API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}