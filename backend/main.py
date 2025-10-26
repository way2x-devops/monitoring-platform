import redis
import json
import os
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models.database import get_db, create_tables, ContainerHistory, SystemMetrics
import datetime


app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

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

@app.on_event("startup")
async def startup_event():
    create_tables()

# API для сохранения данных в БД
@app.post("/api/metrics/containers")
async def save_containers_metrics(containers_data: list, db: Session = Depends(get_db)):
    for container in containers_data:
        db_container = ContainerHistory(
            container_name=container["name"],
            status=container["status"],
            image=container.get("image", "unknown"),
            timestamp=datetime.datetime.utcnow()
        )
        db.add(db_container)
    db.commit()
    return {"message": "Data saved successfully"}

# API для чтения исторических данных
@app.get("/api/metrics/containers/history")
async def get_containers_history(hours: int = 24, db: Session = Depends(get_db)):
    time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    
    containers = db.query(ContainerHistory).filter(
        ContainerHistory.timestamp >= time_threshold
    ).all()
    
    return [
        {
            "name": c.container_name,
            "status": c.status,
            "image": c.image,
            "timestamp": c.timestamp.isoformat()
        }
        for c in containers
    ]