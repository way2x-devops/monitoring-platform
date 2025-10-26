from fastapi import FastAPI
import redis
import json
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Monitoring Platform API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
# Подключение к Redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)

@app.get("/api/containers")
async def get_containers():
    try:
        # Читаем данные из Redis
        data = r.get("containers_status")
        if data:
            return json.loads(data)
        else:
            return {"error": "No data available"}
    except Exception as e:
        return {"error": str(e)}