import asyncio
import time
import logging
from random import shuffle

import aiohttp
import async_timeout
import pymongo

from proxylist import settings


async def check_ws_support(proxy, app):
    session = app['client_session']
    try:
        ws_url = settings.WS_ECHO_SERVERS[0]
        with async_timeout.timeout(5):
            async with session.ws_connect(
                    ws_url, heartbeat=1, receive_timeout=5, proxy=proxy,
            ) as ws:
                await ws.send_str('echo')
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT and msg.data == 'echo':
                    logging.debug(f'WS check success {proxy}')
                    return True
                else:
                    raise RuntimeError(f'Strange message ({msg.type}, {msg.data})')
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logging.debug(f'WS check failed {proxy} {repr(e)}')
    return False


async def update_proxy_in_db(check_result, app):
    proxy_collection = app['db'][settings.MONGO_PROXY_COLLECTION]
    ip = check_result.pop('ip')
    port = check_result.pop('port')
    if check_result['active']:
        await proxy_collection.update_one(
            {'ip': ip, 'port': port},
            {
                '$inc': {
                    'total_checks': 1,
                    'positive_checks': 1,
                },
                '$set': {
                    **check_result,
                    'negative_checks_in_a_row': 0,
                }
            }
        )
    else:
        await proxy_collection.update_one(
            {'ip': ip, 'port': port},
            {
                '$inc': {
                    'total_checks': 1,
                    'negative_checks': 1,
                    'negative_checks_in_a_row': 1,
                },
                '$set': check_result
            }
        )


async def check_request(proxy, app):
    session = app['client_session']
    urls = settings.CHECK_URLS[:]
    shuffle(urls)
    error = None
    for url in urls:
        request_start = time.time()
        try:
            with async_timeout.timeout(2):
                async with session.get(url, proxy=proxy, timeout=2) as response:
                    body = await response.text()
                    if not body:
                        raise RuntimeError('Empty body')
                # ip = proxy.split(':')[1].replace('/', '')
                # if ip not in body:
                #     raise RuntimeError(f'ip \'{ip}\' not found in body ({body})')
        except asyncio.CancelledError:
            raise
        except Exception as e:
            error = repr(e)
            continue

        ping = time.time() - request_start
        logging.debug(f'Check success {proxy} with ping {ping}')
        return ping
    logging.debug(f'Check failed {proxy} {error}')


async def check_proxy(ip, port, app):
    pings = []
    types = []
    ws_support = []

    for protocol in settings.PROTOCOLS:
        proxy = f'{protocol}://{ip}:{port}'
        logging.debug(f'Checking {proxy}')
        async with app['check_semaphore']:
            ping = await check_request(proxy, app)
            if not ping:
                continue
            pings.append(ping)
            types.append(protocol)

            # check ws support
            if settings.CHECK_WS_SUPPORT and await check_ws_support(proxy, app):
                ws_support.append(protocol)
    check_result = {
        'ip': ip,
        'port': port,
        'active': bool(pings),
        'ping': sum(pings)/len(pings) if pings else None,
        'types': types,
        'ws_support': ws_support,
        'last_check': time.time(),
    }
    await update_proxy_in_db(check_result, app)
    return check_result


async def get_proxies_for_check(app):
    proxy_collection = app['db'][settings.MONGO_PROXY_COLLECTION]

    proxies_to_check = []

    limit = min(settings.CHECK_ACTIVE_MAX, settings.CHECK_TOTAL_MAX)
    active_proxies = await proxy_collection.find(
        {'active': True}
    ).sort('last_check', pymongo.ASCENDING).limit(limit).to_list(None)
    proxies_to_check.extend(active_proxies)

    limit = min(settings.CHECK_TOTAL_MAX - len(proxies_to_check), settings.CHECK_NEW_MAX)
    new_proxies = await proxy_collection.find({'last_check': None}).limit(limit).to_list(None)
    proxies_to_check.extend(new_proxies)

    # limit = min(settings.CHECK_TOTAL_MAX - len(proxies_to_check), settings.CHECK_OLD_MAX)
    # old_dead_proxies = await proxy_collection.find(
    #     {'active': False, 'negative_checks_in_a_row': {'$lt': settings.MAX_NEGATIVE_CHECKS_IN_A_ROW}}
    # ).sort('total_checks', pymongo.ASCENDING).limit(limit).to_list(None)
    # proxies_to_check.extend(old_dead_proxies)
    old_dead_proxies = []

    logging.info(
        f'Checking {len(proxies_to_check)} proxies. '
        f'(Active: {len(active_proxies)}, New: {len(new_proxies)}, Inactive: {len(old_dead_proxies)})'
    )
    return proxies_to_check


async def check_proxies(app):
    proxies_to_check = await get_proxies_for_check(app)
    tasks = [
        check_proxy(proxy['ip'], proxy['port'], app) for proxy in proxies_to_check
    ]
    check_start = time.time()
    results = await asyncio.gather(*tasks)
    duration = round(time.time() - check_start, 2)
    total = len(results)
    active = len([proxy for proxy in results if proxy['active']])
    ws_support = len([proxy for proxy in results if proxy['ws_support']])
    logging.info(f'Checked {total} proxies. (Active {active}/{total}. With ws support {ws_support}/{active}). '
                 f'Check duration {duration}s')
