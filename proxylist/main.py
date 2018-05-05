import asyncio
import logging

import aiohttp
from aiohttp import web
from aiosocksy.connector import ProxyClientRequest, ProxyConnector
import pymongo
from motor import motor_asyncio

from proxylist.checker import check_proxies
from proxylist.handlers import get_proxies
from proxylist.helpers import setup_logging, periodic, run_coro_in_background
from proxylist.parser import parse_proxies
from proxylist import settings


async def init_app(loop=None):
    app = web.Application(
        middlewares=[
        ],
        loop=loop
    )

    conn = ProxyConnector(remote_resolve=False)
    app['client_session'] = aiohttp.ClientSession(
        connector=conn, request_class=ProxyClientRequest, raise_for_status=True
    )
    app['check_semaphore'] = asyncio.Semaphore(settings.CHECK_SEMAPHORE)
    app['parse_semaphore'] = asyncio.Semaphore(settings.PARSE_SEMAPHORE)
    app['db'] = await init_db()
    app.router.add_get("/", get_proxies)
    return app


async def init_db():
    mongo_client = motor_asyncio.AsyncIOMotorClient(settings.MONGO_HOST, settings.MONGO_PORT)
    # await mongo_client.drop_database(settings.MONGO_DB)
    db = mongo_client[settings.MONGO_DB]

    await db[settings.MONGO_PROXY_COLLECTION].create_index(
        [('ip', pymongo.ASCENDING), ('port', pymongo.ASCENDING)], unique=True
    )

    return db


def main():
    setup_logging(verbose=True)
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app(loop=loop))
    app['proxy_parser'] = run_coro_in_background(periodic(period=settings.PARSE_PERIOD)(parse_proxies)(app), loop=loop)
    app['proxy_checker'] = run_coro_in_background(periodic(period=settings.CHECK_PERIOD)(check_proxies)(app), loop=loop)
    try:
        logging.info('Proxylist started.')
        web.run_app(app, port=8080, print=logging.debug)
    except KeyboardInterrupt:
        logging.info('Proxylist stopped.')


if __name__ == '__main__':
    main()
