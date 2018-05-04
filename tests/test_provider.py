import pytest
from asynctest import CoroutineMock

from proxylist.providers import Provider
from proxylist.proxy import Proxy

pytestmark = pytest.mark.asyncio


async def test_provider():
    provider = Provider(url='http://some_url.com/')
    assert provider.urls == ['http://some_url.com']
    provider = Provider(url='http://some_url.com', paths=['page1', 'page2'])
    assert provider.urls == ['http://some_url.com/page1', 'http://some_url.com/page2']


async def test_parse_proxies():
    provider = Provider(url='http://some_url.com', paths=['page1', 'page2'])
    provider.get_html = CoroutineMock(side_effect=['sometext127.0.0.1somemoretext8080', None])

    proxies = await provider.get_proxies()

    assert proxies == [Proxy('127.0.0.1', 8080)]
    assert provider.get_html.await_count == 2
