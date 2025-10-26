from fastapi import FastAPI
import redis
import json
import os
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Monitoring Platform API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
# Подключение к Redis

redis_password = os.getenv('REDIS_PASSWORD', 'your_secure_redis_password_123')

r = redis.Redis(
    host='redis',
    port=6379, 
    password=redis_password,
    decode_responses=True
)

@app.get("/api/containers")
async def get_containers():
    try:
        # Redis<-api
        data = r.get("containers_status")
        if data:
            return json.loads(data)
        else:
            return {"error": "No data available"}
    except Exception as e:
        return {"error": str(e)}