from contextlib import asynccontextmanager

import toml
from beanie import init_beanie
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from melly.appmellyapi.auth import jwt_auth
from melly.appmellyapi.db import api_mongo_client, api_models
from melly.appmellyapi.views.articles import article_router
from melly.appmellyapi.views.bookmark import bookmark_router
from melly.appmellyapi.views.collection import collection_router
from melly.appmellyapi.views.me import me_router
from melly.libshared.logger import logger
from melly.libshared.settings import api_settings

pyproject = toml.load("pyproject.toml")
version = pyproject.get("project").get("version")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Beanie...")
    await init_beanie(database=api_mongo_client[api_settings.db_name], document_models=api_models)
    yield


description = """
![Melly](https://cdn.sleek.email/images/86e8909f-0ea8-4c90-bcd3-d8277a993ba0-melly.jpg)

Learn from others, share your knowledge, and grow your network with Melly. Melly is a social learning platform that 
allows people to share bookmarks, notes, and highlights from their favorites.

[https://melly.com](https://melly.com)
"""

app = FastAPI(
    title="Melly API",
    description=description,
    version=version,
    host=api_settings.host,
    port=api_settings.port,
    debug=api_settings.debug,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
jwt_auth.init_app(app)

# User facing routes
app.include_router(router=me_router, prefix="/v1")
app.include_router(router=article_router, prefix="/v1")
app.include_router(router=bookmark_router, prefix="/v1")
app.include_router(router=collection_router, prefix="/v1")
