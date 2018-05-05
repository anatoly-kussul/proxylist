from aiohttp.web import json_response

from proxylist import settings


async def get_proxies(request):
    proxy_collection = request.app['db'][settings.MONGO_PROXY_COLLECTION]
    proxies = await proxy_collection.find(
        {'active': True},
        {
            '_id': 0,
            'ip': 1,
            'port': 1,
            'last_check': 1,
            'types': 1,
            'ws_support': 1,
            'ping': 1,
        }
    ).to_list(None)
    return json_response([proxy for proxy in proxies if 'http' in proxy['types']])
