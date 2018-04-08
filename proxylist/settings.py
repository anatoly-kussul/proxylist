PARSE_URLS = [
    'https://hidemy.name/en/proxy-list/?anon=4#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=64#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=128#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=192#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=256#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=320#list',
]
CHECK_URLS = [
    'http://httpbin.org/ip',
]
WS_ECHO_SERVERS = [
    'wss://echo.websocket.org?encoding=text',
]
PROTOCOLS = ['http', 'socks4', 'socks5']
# no https proxy support in aiohttp yet. https://github.com/aio-libs/aiohttp/issues/2722

CHECK_WS_SUPPORT = True

PARSE_PERIOD = 300
CHECK_PERIOD = 60

MONGO_HOST = 'mongo'
MONGO_PORT = 27017
MONGO_DB = 'proxylist'
MONGO_PROXY_COLLECTION = 'proxies'

CHECK_TOTAL_MAX = 1500
CHECK_ACTIVE_MAX = 1000
CHECK_NEW_MAX = 200
CHECK_OLD_MAX = 1000

MAX_NEGATIVE_CHECKS_IN_A_ROW = 60
