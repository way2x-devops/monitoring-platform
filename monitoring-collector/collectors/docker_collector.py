import docker
import time
import json

def monitor_containers():
    client = docker.from_env()
    while True:
        containers = client.containers.list(all=True)
        for container in containers:
            print(f"Container: {container.name}, Status: {container.status}")
        time.sleep(5)

if __name__ == "__main__":
    monitor_containers()