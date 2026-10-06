from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Kanban Board API")

# Health check endpoint
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# Mount static files (will be used for the frontend later)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Serve a basic "Hello World" HTML at the root
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Hello World</title>
        </head>
        <body>
            <h1>Hello World from FastAPI!</h1>
        </body>
    </html>
    """
