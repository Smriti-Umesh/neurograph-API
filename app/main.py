from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.db_check import router as db_router
from app.api.routes.networks import router as networks_router
from app.api.routes.nodes import router as nodes_router
from app.api.routes.edges import router as edges_router


app = FastAPI(title="Brain-Inspired Knowledge Network API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(db_router)
app.include_router(networks_router)
app.include_router(nodes_router)
app.include_router(edges_router)


@app.get("/")
def root():
    return {"message": "API is running."}