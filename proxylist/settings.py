PARSE_URLS = [
    'https://hidemy.name/en/proxy-list/?anon=4#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=64#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=128#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=192#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=256#list',
    'https://hidemy.name/en/proxy-list/?anon=4&start=320#list',
    'http://www.proxylists.net/',
    'https://www.ipaddress.com/proxy-list/',
    'https://www.sslproxies.org/',
    'https://freshfreeproxylist.wordpress.com/',
    'http://proxytime.ru/http',
    'https://free-proxy-list.net/',
    'https://us-proxy.org/',
    'http://fineproxy.org/eng/fresh-proxies/',
    'https://socks-proxy.net/',
    'http://cn-proxy.com/',
    'https://hugeproxies.com/home/',
    'https://geekelectronics.org/my-servisy/proxy',
    'http://pubproxy.com/api/proxy?limit=20&format=txt',
]
CHECK_URLS = [
    'http://httpbin.org/ip',
    'http://api.ipify.org?format=json',
    'http://ip-api.com/json',
    'https://ifconfig.co/json',
    'http://api.myip.com/',
]
WS_ECHO_SERVERS = [
    'wss://echo.websocket.org?encoding=text',
]
PROTOCOLS = [
    'http',
    # 'socks4',
    # 'socks5',
]
# no https proxy support in aiohttp yet. https://github.com/aio-libs/aiohttp/issues/2722

CHECK_WS_SUPPORT = False

PARSE_PERIOD = 300
CHECK_PERIOD = 60

PARSE_SEMAPHORE = 20
CHECK_SEMAPHORE = 100

MONGO_HOST = 'mongo'
MONGO_PORT = 27017
MONGO_DB = 'proxylist'
MONGO_PROXY_COLLECTION = 'proxies'

CHECK_TOTAL_MAX = 1500
CHECK_ACTIVE_MAX = 1000
CHECK_NEW_MAX = 1500
CHECK_OLD_MAX = 1000

MAX_NEGATIVE_CHECKS_IN_A_ROW = 60
