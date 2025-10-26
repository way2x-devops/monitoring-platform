import docker
import time
import redis
import json
def main():
    client = docker.from_env()
    print("Docker Monitor started...")
    r=redis.Redis(host='redis', port=6379, decode_responses=True)
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
            
            # Сохраняем в Redis
            r.set("containers_status", json.dumps(containers_data))
            r.set("last_update", time.time())
            
            print(f"Updated {len(containers_data)} containers in Redis")
            time.sleep(10)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()