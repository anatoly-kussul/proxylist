import asyncio
import re
import logging
import time

import pymongo

from proxylist import settings

PROXY_REGEX = re.compile(r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*?(?P<port>\d{2,5})')
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
}


async def parse_proxies_from_url(url, app):
    session = app['client_session']
    proxies = []
    try:
        async with app['parse_semaphore'], session.get(url, headers=HEADERS) as response:
            html = await response.text()
        proxies = [(proxy[0], proxy[1]) for proxy in PROXY_REGEX.findall(html)]
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logging.warning(f'Error parsing proxies from \'{url}\'. ({repr(e)}')
    if not proxies:
        logging.warning(f'Parsed 0 proxies from \'{url}\'.')
    return proxies


async def add_proxies(proxies, app):
    proxy_collection = app['db'][settings.MONGO_PROXY_COLLECTION]

    formatted_proxies = [
        {
            'ip': proxy[0],
            'port': int(proxy[1]),
            'active': None,
            'last_check': None,
            'total_checks': 0,
            'positive_checks': 0,
            'negative_checks': 0,
            'negative_checks_in_a_row': 0,
            'types': None,
            'ws_support': None,
            'ping': None,
        }
        for proxy in proxies
    ]

    try:
        result = await proxy_collection.insert_many(formatted_proxies, ordered=False)
        return len(result.inserted_id)
    except pymongo.errors.BulkWriteError as bwe:
        # logging.debug(f'Mongo errors {bwe.details}')
        return bwe.details['nInserted']


async def parse_proxies(app):
    logging.info('Parsing proxies...')
    tasks = [
        parse_proxies_from_url(url, app) for url in settings.PARSE_URLS
    ]
    parse_start = time.time()
    proxies = []
    for proxy_list in await asyncio.gather(*tasks):
        proxies.extend(proxy_list)
    parse_duration = round(time.time() - parse_start, 2)
    logging.info(f'Parsed {len(proxies)} proxies. Parse duration {parse_duration}s.')
    if proxies:
        new_proxies = await add_proxies(proxies, app)
    logging.info(f'Added {new_proxies} new proxies to db.')
