"""Application entry point."""

import logging

import uvicorn
from fastapi import FastAPI

from app.api.recommend_route import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Collabster Recommendation Engine",
    description="Production-grade personalised feed recommendation service.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)