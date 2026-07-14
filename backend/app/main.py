import logging
from importlib import import_module
from .routes import runs, ws

_fastapi = import_module("fastapi")
_fastapi_cors = import_module("fastapi.middleware.cors")
FastAPI = _fastapi.FastAPI
CORSMiddleware = _fastapi_cors.CORSMiddleware

# Configure logging formats
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(title="Threadwright Orchestration Engine", version="0.1.0")

origins = [
    "http://localhost:5173",        # Vite default local port
    "http://localhost:3000",        # Alternative local port
    "https://threadwright.vercel.app" # Your production frontend on Vercel
]

# Configure CORS Middleware for Frontend React routing
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API and Socket routes
app.include_router(runs.router)
app.include_router(ws.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}