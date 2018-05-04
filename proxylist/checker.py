import asyncio
import time
import logging
from random import shuffle

import aiohttp
import async_timeout
import pymongo
from aiosocksy.connector import ProxyConnector, ProxyClientRequest

from proxylist import settings


class Checker:
    URL = ''

    def __init__(self, semaphore=None, timeout=5):
        if semaphore is None:
            self.semaphore = asyncio.Semaphore(5)
        else:
            self.semaphore = semaphore
        self.logger = logging.getLogger('proxylist.checker')
        self.timeout = timeout

    async def check_proxy(self, ip, port):
        pings = []
        protocols = []
        country = None
        country_code = None
        external_ip = None
        for protocol in settings.PROTOCOLS:
            proxy_str = f'{protocol}://{ip}:{port}'
            self.logger.debug(f'Checking {proxy_str}')
            result = await self.get_response(proxy_str)
            country = result['country']
            country_code = result['country_code']
            external_ip = result['external_ip']
            pings.append(result['ping'])
            protocols.append(protocol)
        return {
            'ping': sum(pings)/len(pings) if pings else None,
            'protocols': protocols,
            'country': country,
            'country_code': country_code,
            'external_ip': external_ip,
        }

    async def get_response(self, proxy_str):
        conn = ProxyConnector(remote_resolve=False)
        async with self.semaphore:
            time_start = time.time()
            async with aiohttp.ClientSession(
                    connector=conn, request_class=ProxyClientRequest, raise_for_status=True) as session:
                async with session.get(self.URL, timeout=self.timeout, proxy=proxy_str) as response:
                    result = await self.parse_response(response)
                    ping = time.time() - time_start
                    result['ping'] = ping
                    return result

    async def parse_response(self, response):
        """
        :param response:
        :return: (external ip, country, country code)
        """
        raise NotImplementedError


class CheckerIpApi(Checker):
    URL = 'http://ip-api.com/json'

    async def parse_response(self, response):
        response_dict = await response.json()
        return {
            'country': response_dict['country'],
            'country_code': response_dict['country_code'],
            'external_ip': response_dict['query'],
        }


class CheckerIfConfig(Checker):
    URL = 'https://ifconfig.co/json'

    async def parse_response(self, response):
        response_dict = await response.json()
        return {
            'country': response_dict['country'],
            'country_code': response_dict['country_iso'],
            'external_ip': response_dict['ip'],
        }


class CheckerMyIP(Checker):
    URL = 'http://api.myip.com/'

    async def parse_response(self, response):
        response_dict = await response.json()
        return {
            'country': response_dict['country'],
            'country_code': response_dict['cc'],
            'external_ip': response_dict['ip'],
        }


class CheckerApiIp(Checker):
    URL = 'https://api.ip.sb/geoip'

    async def parse_response(self, response):
        response_dict = await response.json()
        return {
            'country': response_dict['country'],
            'country_code': response_dict['country_code'],
            'external_ip': response_dict['ip'],
        }


class CheckerWTF(Checker):
    URL = 'https://wtfismyip.com/json'

    async def parse_response(self, response):
        response_dict = await response.json()
        return {
            'country': response_dict['YourFuckingLocation'].rsplit(',', maxsplit=1)[1].strip(),
            'country_code': response_dict['YourFuckingCountryCode'],
            'external_ip': response_dict['YourFuckingIPAddress'],
        }


CHECKERS = [
    CheckerIfConfig(),
    CheckerIpApi(),
    CheckerMyIP(),
    CheckerWTF(),
    CheckerApiIp(),
]


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
    ip = proxy.split(':')[1].replace('/', '')
    error = None
    for url in urls:
        request_start = time.time()
        try:
            async with session.get(url, proxy=proxy, timeout=2) as response:
                body = await response.text()
                if ip not in body:
                    raise RuntimeError(f'ip \'{ip}\' not found in body ({body})')
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

    limit = min(settings.CHECK_TOTAL_MAX - len(proxies_to_check), settings.CHECK_OLD_MAX)
    old_dead_proxies = await proxy_collection.find(
        {'active': False, 'negative_checks_in_a_row': {'$lt': settings.MAX_NEGATIVE_CHECKS_IN_A_ROW}}
    ).sort('total_checks', pymongo.ASCENDING).limit(limit).to_list(None)
    proxies_to_check.extend(old_dead_proxies)

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
