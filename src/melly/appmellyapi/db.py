import asyncio

from motor.motor_asyncio import AsyncIOMotorClient

from melly.libaccount.models import SocialAuthSession, User
from melly.libarticle.models import Article
from melly.libcollection.models import BookmarkItem
from melly.libshared.settings import api_settings

client_options = {"appname": "appmellyapi"}
api_mongo_client = AsyncIOMotorClient(api_settings.mongo_url, **client_options)
api_mongo_client.get_io_loop = asyncio.get_running_loop

api_models = [User, SocialAuthSession, Article, BookmarkItem]
