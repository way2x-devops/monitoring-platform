from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Monitoring Platform API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

import docker

@app.get("/api/containers")
async def get_containers():
    client = docker.from_env()
    containers = client.containers.list(all=True)
    return [{"name": c.name, "status": c.status} for c in containers]