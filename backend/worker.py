import redis
import json
import time
import os
from sqlalchemy.orm import Session
from models.database import SessionLocal, ContainerHistory, create_tables
import datetime

def process_containers_data():
    # Подключение к Redis
    redis_password = os.getenv('REDIS_PASSWORD', 'your_secure_redis_password_123')
    r = redis.Redis(
        host='redis',
        port=6379,
        password=redis_password,
        decode_responses=True
    )
    
    # Подключение к PostgreSQL
    db = SessionLocal()

    try:
        # Проверяем существует ли таблица
        db.query(ContainerHistory).first()
    except:
        print(" Tables don't exist, creating...")
        create_tables()
        print(" Tables created")
    
    print("🛠️ Worker started...")
    
    while True:
        try:
            data = r.get("containers_status")
            
            if data:
                containers_data = json.loads(data)
                containers_to_save = []
                
                # БЕЗОПАСНАЯ ПРОВЕРКА ДУБЛИКАТОВ
                for container in containers_data:
                    container_name = container["name"]
                    current_status = container["status"]
                    
                    try:
                        # Проверяем последнюю запись в БД
                        last_record = db.query(ContainerHistory).filter(
                            ContainerHistory.container_name == container_name
                        ).order_by(ContainerHistory.timestamp.desc()).first()
                        
                        # Если нет записей или статус изменился
                        if not last_record or last_record.status != current_status:
                            containers_to_save.append(container)
                            
                    except Exception as e:
                        # Если таблицы нет, сохраняем все данные
                        print(f"⚠️ Table error, saving all data: {e}")
                        containers_to_save = containers_data
                        break
                
                # Сохраняем данные
                if containers_to_save:
                    for container in containers_to_save:
                        db_container = ContainerHistory(
                            container_name=container["name"],
                            status=container["status"],
                            image=container.get("image", "unknown"),
                            timestamp=datetime.datetime.utcnow()
                        )
                        db.add(db_container)
                    
                    db.commit()
                    print(f"✅ Worker saved {len(containers_to_save)} containers to PostgreSQL")
                else:
                    print("⏳ No container status changes detected")
            
            else:
                print("⏳ No data in Redis yet...")
            
            time.sleep(60)
            
        except Exception as e:
            print(f"❌ Worker error: {e}")
            db.rollback()
            time.sleep(10)

if __name__ == "__main__":
    process_containers_data()