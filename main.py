from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logger import setup_logging
setup_logging()  #第一行就初始化日志

from core.startup import startup_tasks, shutdown_tasks
from routers import news, users, favorite, history, ai
from utils.exception_handlers import register_exception_handlers
import time
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def timing_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(f"[耗时] {request.method} {request.url.path} → {elapsed_ms:.2f}ms")
    return response

@app.get("/")
async def root():
    return {"message": "Hello World"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = await startup_tasks()
    yield
    await shutdown_tasks(task)


app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(ai.router)


