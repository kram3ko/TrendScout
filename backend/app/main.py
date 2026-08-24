import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.auth.router import router as auth_router
from app.auth.service import AuthService
from app.core.config import get_settings
from app.core.db import SessionFactory
from app.products.router import router as products_router
from app.salesboost.router import router as salesboost_router
from app.scraping.category_router import router as amazon_categories_router
from app.scraping.router import router as runs_router
from app.tasks.broker import broker

API_PREFIX = "/api"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if not broker.is_worker_process:
        await broker.startup()

    async with SessionFactory() as session:
        await AuthService(session).ensure_user(
            settings.bootstrap_username, settings.bootstrap_password
        )
    logger.info(
        "Scoring provider: %s", settings.llm_provider if settings.llm_enabled else "fallback"
    )

    yield

    if not broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(
    title="TrendScout",
    summary="Amazon trend scouting, AI scoring and analytics for e-commerce buyers",
    version="0.1.0",
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
    redoc_url=f"{API_PREFIX}/redoc",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix=API_PREFIX)
api.include_router(auth_router)
api.include_router(products_router)
api.include_router(amazon_categories_router)
api.include_router(runs_router)
api.include_router(salesboost_router)
app.include_router(api)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
