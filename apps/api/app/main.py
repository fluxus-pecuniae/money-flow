"""FastAPI entrypoint for the control plane."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.app.api.routes import router as api_router
from core.config.settings import get_settings
from core.logging.setup import configure_logging, get_logger


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.logging)
    logger = get_logger(__name__)
    logger.info("api_startup", environment=settings.app.environment.value)
    yield
    logger.info("api_shutdown", environment=settings.app.environment.value)


app = FastAPI(
    title="Money Flow Control API",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(api_router)

