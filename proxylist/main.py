import asyncio
import pprint
import re
import time

import aiohttp
import async_timeout
import logging
from aiohttp import web
from aiorun import run
from aiosocksy.connector import ProxyClientRequest, ProxyConnector

from proxylist.helpers import setup_logging

PROXY_REGEX = re.compile(r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*?(?P<port>\d{2,5})')
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
}
PARSE_URLS = [
    'https://hidemy.name/en/proxy-list/?anon=4#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=64#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=128#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=192#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=256#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=320#list',
]
CHECK_URLS = [
    'http://httpbin.org/ip'
]
PROTOCOLS = ['http', 'socks4', 'socks5']
# no https proxy support in aiohttp yet. https://github.com/aio-libs/aiohttp/issues/2722


async def check_proxy(ip, port, app):
    session = app['client_session']
    pings = []
    types = []
    ws_support = []
    ws_errors = {}

    for protocol in PROTOCOLS:
        url = CHECK_URLS[0]
        proxy = f'{protocol}://{ip}:{port}'
        logging.debug(f'Checking {proxy}')
        async with app['semaphore']:
            request_start = time.time()
            try:
                async with session.get(url, headers=HEADERS, proxy=proxy, timeout=2) as response:
                    body = await response.text()
                    # if ip not in body:
                    #     raise RuntimeError(f'ip not found in body ({body})')
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logging.debug(f'Check failed {proxy} {repr(e)}')
                continue

            ping = time.time() - request_start
            logging.debug(f'Check success {proxy} with ping {ping}')
            pings.append(ping)
            types.append(protocol)

            # check ws support
            try:
                with async_timeout.timeout(10):
                    async with session.ws_connect(
                            'wss://echo.websocket.org?encoding=text', heartbeat=1, receive_timeout=5, proxy=proxy,
                    ) as ws:
                        await ws.send_str('echo')
                        msg = await ws.receive()
                        if msg.type == aiohttp.WSMsgType.TEXT and msg.data == 'echo':
                            ws_support.append(protocol)
                            logging.debug(f'WS check success {proxy}')
                        else:
                            raise RuntimeError(f'Strange message ({msg.type}, {msg.data})')
            except asyncio.CancelledError:
                raise
            except Exception as e:
                ws_errors[protocol] = repr(e)
                logging.debug(f'WS check failed {proxy} {repr(e)}')

    return {
        'ip': ip,
        'port': port,
        'types': types,
        'ws_support': ws_support,
        # 'ws_errors': ws_errors,
        'ping': sum(pings)/len(pings) if pings else None,
        'active': bool(pings)
    }


async def init_app(loop=None):
    app = web.Application(
        middlewares=[
        ],
        loop=loop
    )

    # app['db'] = await init_idb()
    conn = ProxyConnector(remote_resolve=False)
    app['client_session'] = aiohttp.ClientSession(
        connector=conn, request_class=ProxyClientRequest, raise_for_status=True
    )
    app['semaphore'] = asyncio.Semaphore(100)
    app['proxies'] = []
    return app


async def get_proxies(url, app):
    session = app['client_session']
    async with session.get(url, headers=HEADERS) as response:
        html = await response.text()
    return [(proxy[0], proxy[1]) for proxy in PROXY_REGEX.findall(html)]


async def main():
    setup_logging()
    app = await init_app()
    tasks = [
        get_proxies(url, app) for url in PARSE_URLS
        ]
    proxies = []
    logging.info('Parsing proxies...')
    parse_start = time.time()
    for result in (await asyncio.gather(*tasks)):
        proxies.extend(result)
    parse_duration = round(time.time() - parse_start, 2)
    logging.info(f'Parsed {len(proxies)}. Parse duration {parse_duration}s.')
    tasks = [
        check_proxy(*proxy, app) for proxy in proxies
    ]
    check_start = time.time()
    logging.info(f'Checking {len(proxies)} proxies...')
    all_proxies = [proxy for proxy in (await asyncio.gather(*tasks))]
    active_proxies = [proxy for proxy in all_proxies if proxy['active']]
    ws_proxies = [proxy for proxy in all_proxies if proxy['ws_support']]
    check_duration = round(time.time() - check_start, 2)
    # for proxy in active_proxies:
    #     pprint.pprint(proxy)
    logging.info(
        f'Active proxies {len(active_proxies)}/{len(all_proxies)}. WS proxies {len(ws_proxies)}/{len(all_proxies)}.'
        f' Check duration {check_duration}s'
    )


if __name__ == '__main__':
    run(main())
