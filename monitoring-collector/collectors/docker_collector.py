import docker
import time

def main():
    client = docker.from_env()
    print("Docker Monitor started...")
    
    while True:
        try:
            containers = client.containers.list(all=True)
            print(f" Found {len(containers)} containers:")
            
            for container in containers:
                print(f"  - {container.name}: {container.status}")
            
            print("---")
            time.sleep(10)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()