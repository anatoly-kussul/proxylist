import time
from operator import attrgetter


class DBEngine:
    ALLOWED_SORT_OPTIONS = ['ping', 'last_check', 'ratio', 'total_checks']

    async def add_proxies(self, proxies):
        """
        Adds new proxies to db
        :param proxies: list of Proxy objecys
        :return: count of added new proxies
        """
        raise NotImplementedError

    async def get_proxies(self, alive=None, max_ping=None, protocols=None, last_check=None,
                          ratio=None, country=None, limit=None, sort_by=None, reverse=False):
        """
        Get list of alive proxies with given filters from db.
        :param alive: alive
        :param max_ping: max ping in seconds
        :param protocols: support any of given protocols
        :param last_check: checked less than given seconds ago
        :param ratio: positive checks / total checks ratio
        :param country: country
        :param limit: max len of return list
        :param sort_by: proxy property to sort by
        :param reverse: reverse sort order
        :return: list of Proxy objects
        """
        raise NotImplementedError


class InMemoryDB(DBEngine):
    def __init__(self):
        self.proxies = {}

    async def add_proxies(self, proxies):
        count = 0
        for proxy in proxies:
            key = (proxy.ip, proxy.port)
            if key not in self.proxies:
                self.proxies[key] = proxy
                count += 1
        return count

    async def get_proxies(self, alive=None, max_ping=None, protocols=None, last_check=None,
                          ratio=None, country=None, limit=None, sort_by=None, reverse=False):
        proxies = []
        current_time = time.time()
        sorted_proxies = self.proxies.values()
        if sort_by is not None:
            if sort_by not in self.ALLOWED_SORT_OPTIONS:
                raise ValueError(f'Sort by option must be in {self.ALLOWED_SORT_OPTIONS}')
            filtered_proxies = (proxy for proxy in self.proxies.values() if getattr(proxy, sort_by) is not None)
            sorted_proxies = sorted(filtered_proxies, key=attrgetter(sort_by), reverse=reverse)

        for proxy in sorted_proxies:
            if limit and len(proxies) >= limit:
                break
            if alive is not None and proxy.alive != alive:
                continue
            if max_ping and proxy.ping > max_ping:
                continue
            if protocols and not set(protocols) & set(proxy.protocols):
                continue
            if last_check and current_time - proxy.last_check > last_check:
                continue
            if ratio and proxy.ratio < ratio:
                continue
            if country and country.lower() != proxy.country.lower() and country.lower() != proxy.country_code.lower():
                continue
            proxies.append(proxy)
        return proxies
