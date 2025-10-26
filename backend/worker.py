import redis
import json
import time
import os
from sqlalchemy.orm import Session
from models.database import SessionLocal, ContainerHistory
import datetime

def process_containers_data ():
    redis_password = os.getenv('REDIS_PASSWORD', 'your_secure_redis_password_123')
    
    r = redis.Redis(
    host='redis',
    port=6379,
    password=redis_password,
    decode_responses=True
    )
    
    db = SessionLocal()
    
    while True:
        try:
            # Берем данные из Redis
            data = r.get("containers_status")
            
            if data:
                containers_data = json.loads(data)
                
                # Сохраняем в PostgreSQL
                for container in containers_data:
                    db_container = ContainerHistory(
                        container_name=container["name"],
                        status=container["status"],
                        image=container.get("image", "unknown"),
                        timestamp=datetime.datetime.utcnow()
                    )
                    db.add(db_container)
                
                db.commit()
                print(f" Worker saved {len(containers_data)} containers to PostgreSQL")
            else:
                print("⏳ No data in Redis yet...")
            
            time.sleep(60)
            
        except Exception as e:
            print(f"❌ Worker error: {e}")
            db.rollback()
            time.sleep(10)

if __name__ == "__main__":
    process_containers_data()