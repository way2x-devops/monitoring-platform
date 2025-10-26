import docker
import time
import redis
import json
import os
import requests

def save_to_database(containers_data):
    try:
        # Отправляем данные в backend для сохранения в БД
        response = requests.post(
            "http://backend:8000/api/metrics/containers",
            json=containers_data,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Data saved to PostgreSQL")
        else:
            print(f"❌ Failed to save data: {response.status_code}")
    except Exception as e:
        print(f"❌ Database save error: {e}")

def main():
    client = docker.from_env()
    print("🚀 Docker Monitor started...")
    
    redis_password = os.getenv('REDIS_PASSWORD', 'your_secure_redis_password_123')
    r = redis.Redis(
        host='redis',
        port=6379, 
        password=redis_password,
        decode_responses=True
    )
    
    while True:
        try:
            containers = client.containers.list(all=True)
            containers_data = []
            
            for container in containers:
                containers_data.append({
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "id": container.short_id
                })
            
            # Сохраняем в Redis (для текущих данных)
            r.set("containers_status", json.dumps(containers_data))
            r.set("last_update", time.time())
            
            # Сохраняем в PostgreSQL (для истории)
            save_to_database(containers_data)
            
            print(f"📊 Updated {len(containers_data)} containers")
            time.sleep(30)  # Сохраняем каждые 30 секунд
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()