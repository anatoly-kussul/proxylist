import re
import asyncio
import logging
import time

import aiohttp

from proxylist.proxy import Proxy


class Provider:
    PROXY_REGEX = re.compile(r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*?(?P<port>\d{2,5})')
    HEADERS = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }

    def __init__(self, url, paths=None, semaphore=None, timeout=10):
        self.url = url
        if self.url.endswith('/'):
            self.url = self.url[:-1]
        if paths is None:
            self.urls = [self.url]
        else:
            self.urls = [
                f'{self.url}/{path}'
                for path in paths
            ]
        self.logger = logging.getLogger(f'proxylist.provider')
        if semaphore is None:
            self.semaphore = asyncio.Semaphore(5)
        else:
            self.semaphore = semaphore
        self.timeout = timeout

    async def get_proxies(self):
        self.logger.info(f'Parsing proxies from {self.url}...')
        tasks = [
            self.get_html(url) for url in self.urls
        ]
        parse_start = time.time()
        proxies = []
        for html in await asyncio.gather(*tasks):
            if html is not None:
                proxies.extend(self.find_proxies_on_page(html))
        parse_duration = round(time.time() - parse_start, 2)
        self.logger.info(f'Parsed {len(proxies)} proxies from {self.url}. Parse duration {parse_duration}s.')
        return proxies

    async def get_html(self, url):  # pragma: no cover
        try:
            async with aiohttp.ClientSession() as session:
                async with self.semaphore, session.get(url, headers=self.HEADERS) as response:
                    html = await response.text()
                    return html
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.warning(f'Error getting response from \'{url}\'. ({repr(e)}')

    def find_proxies_on_page(self, html):
        proxies = [Proxy(proxy[0], int(proxy[1])) for proxy in self.PROXY_REGEX.findall(html)]
        return proxies


PROVIDERS = [
    Provider(
        url='https://hidemy.name/',
        paths=[
            'en/proxy-list/?anon=4#list',
            'en/proxy-list/?anon=4&start=64#list',
            'en/proxy-list/?anon=4&start=128#list',
            'en/proxy-list/?anon=4&start=192#list',
            'en/proxy-list/?anon=4&start=256#list',
            'en/proxy-list/?anon=4&start=320#list',
        ],
    ),
]

