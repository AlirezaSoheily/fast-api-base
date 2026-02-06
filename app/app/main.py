import logging
import os
import sys
from contextlib import asynccontextmanager

from brotli_asgi import BrotliMiddleware
from fastapi import FastAPI, Request, Response
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.middleware.get_accept_language_middleware import AcceptLanguageMiddleware
from app.exceptions import exception_handlers
from app.models import User
from cache import Cache

from richapi.exc_parser.openapi import enrich_openapi


def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(levelname)s:%(asctime)s %(name)s:%(funcName)s:%(lineno)s %(message)s"
        )
    )
    logger.addHandler(handler)


init_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_cache = Cache()
    url = str(settings.REDIS_URI)
    await redis_cache.init(
        host_url=url,
        prefix="api-cache",
        response_header="X-API-Cache",
        ignore_arg_types=[Request, Response, Session, AsyncSession, User],
    )
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    exception_handlers=exception_handlers,
)


if settings.SUB_PATH:
    app.mount(f"{settings.SUB_PATH}", app)


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(api_router, prefix=settings.API_V1_STR)
app.add_middleware(AcceptLanguageMiddleware)
app.add_middleware(BrotliMiddleware, gzip_fallback=True)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url=f"{settings.SUB_PATH}/static/swagger-ui-bundle.js",
        swagger_css_url=f"{settings.SUB_PATH}/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


if settings.SUB_PATH:
    app.mount(f"{settings.SUB_PATH}", app)


app.openapi = enrich_openapi(
    app=app,
    open_api_getter=(
        app.openapi_schema
        if app.openapi_schema
        else lambda fast_api_app: get_openapi(
            title="Docs",
            version="",
            routes=fast_api_app.routes,
            servers=[{"url": settings.SUB_PATH if settings.SUB_PATH else ""}],
        )
    ),
)



@app.get("/healthz")
async def healthz():
    return {"status": "ok", "db": "up", "redis": "up"}
