from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.db_check import router as db_router
from app.api.routes.networks import router as networks_router
from app.api.routes.nodes import router as nodes_router

app = FastAPI(title="Brain-Inspired Knowledge Network API")

app.include_router(health_router)
app.include_router(db_router)
app.include_router(networks_router)
app.include_router(nodes_router)

@app.get("/")
def root():
    return {"message": "API is running."}