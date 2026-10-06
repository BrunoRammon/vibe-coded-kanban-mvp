import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Kanban Board API")

# Ensure the static directory exists so FastAPI doesn't crash on startup
os.makedirs("backend/static", exist_ok=True)

# Health check endpoint
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# Mount Next.js static files at root
app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")
