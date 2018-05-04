import pytest

from proxylist.db_engine import InMemoryDB
from proxylist.proxy import Proxy


pytestmark = pytest.mark.asyncio


@pytest.fixture
def in_memory_db():
    engine = InMemoryDB()
    return engine


async def test_get_proxies_0(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []


async def test_add_proxies(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    add_proxies = [Proxy(ip='127.0.0.1', port=80), Proxy(ip='0.0.0.0', port=1080)]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 2

    add_proxies = [Proxy(ip='0.0.0.0', port=80), Proxy(ip='0.0.0.0', port=1080)]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 1


async def test_get_proxies_limit(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    add_proxies = [Proxy(ip='127.0.0.1', port=80), Proxy(ip='0.0.0.0', port=1080)]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 2

    proxies = await in_memory_db.get_proxies(limit=1)

    assert len(proxies) == 1


async def test_get_proxies_filter_alive(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    alive_proxy = Proxy(ip='127.0.0.1', port=80, alive=True)
    dead_proxy = Proxy(ip='0.0.0.0', port=1080)
    add_proxies = [alive_proxy, dead_proxy]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 2

    proxies = await in_memory_db.get_proxies()

    assert len(proxies) == 2

    proxies = await in_memory_db.get_proxies(alive=True)

    assert len(proxies) == 1
    assert proxies[0] == alive_proxy

    proxies = await in_memory_db.get_proxies(alive=False)

    assert len(proxies) == 1
    assert proxies[0] == dead_proxy


async def test_get_proxies_filter_max_ping(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    low_ping = Proxy(ip='127.0.0.1', port=80, alive=True, ping=5)
    high_ping = Proxy(ip='0.0.0.0', port=1080, alive=True, ping=10)
    add_proxies = [low_ping, high_ping]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 2

    proxies = await in_memory_db.get_proxies()

    assert len(proxies) == 2

    proxies = await in_memory_db.get_proxies(max_ping=7)

    assert len(proxies) == 1
    assert proxies[0] == low_ping


async def test_get_proxies_filter_protocols(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    http_proxy = Proxy(ip='127.0.0.1', port=1, alive=True, protocols=['http'])
    socks4_proxy = Proxy(ip='127.0.0.1', port=2, alive=True, protocols=['socks4'])
    socks5_proxy = Proxy(ip='127.0.0.1', port=3, alive=True, protocols=['socks5'])
    http_socks4_proxy = Proxy(ip='127.0.0.1', port=4, alive=True, protocols=['http', 'socks4'])
    http_socks5_proxy = Proxy(ip='127.0.0.1', port=5, alive=True, protocols=['http', 'socks5'])
    socks4_socks5_proxy = Proxy(ip='127.0.0.1', port=6, alive=True, protocols=['socks4', 'socks5'])
    all_proxy = Proxy(ip='127.0.0.1', port=7, alive=True, protocols=['http', 'socks4', 'socks5'])
    add_proxies = [http_proxy, socks4_proxy, socks5_proxy, http_socks4_proxy,
                   http_socks5_proxy, socks4_socks5_proxy, all_proxy]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 7

    proxies = await in_memory_db.get_proxies(protocols=['http', 'socks4'])

    assert len(proxies) == 6

    assert http_proxy in proxies
    assert socks4_proxy in proxies
    assert socks5_proxy not in proxies
    assert http_socks4_proxy in proxies
    assert http_socks5_proxy in proxies
    assert socks4_socks5_proxy in proxies
    assert all_proxy in proxies

    proxies = await in_memory_db.get_proxies(protocols=['http'])

    assert len(proxies) == 4

    assert http_proxy in proxies
    assert socks4_proxy not in proxies
    assert socks5_proxy not in proxies
    assert http_socks4_proxy in proxies
    assert http_socks5_proxy in proxies
    assert socks4_socks5_proxy not in proxies
    assert all_proxy in proxies


async def test_get_proxies_filter_max_ratio(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    high_ratio = Proxy(ip='127.0.0.1', port=80, alive=True, total_checks=10, positive_checks=7, ratio=0.7)
    low_ratio = Proxy(ip='127.0.0.1', port=81, alive=True, total_checks=10, positive_checks=3, ratio=0.3)
    add_proxies = [low_ratio, high_ratio]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 2

    proxies = await in_memory_db.get_proxies(ratio=0.6)

    assert len(proxies) == 1
    assert proxies[0] == high_ratio


async def test_get_proxies_filter_country(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    ua_1 = Proxy(ip='127.0.0.1', port=1, alive=True, country='Ukraine', country_code='UA')
    ua_2 = Proxy(ip='127.0.0.1', port=2, alive=True, country='UKRAINE', country_code='UA')
    ua_3 = Proxy(ip='127.0.0.1', port=3, alive=True, country='ukraine', country_code='UA')
    ua_4 = Proxy(ip='127.0.0.1', port=4, alive=True, country='Ukraine', country_code='Ua')
    ua_5 = Proxy(ip='127.0.0.1', port=5, alive=True, country='Ukraine', country_code='ua')
    not_ua = Proxy(ip='127.0.0.1', port=6, alive=True, country='England', country_code='EN')
    add_proxies = [ua_1, ua_2, ua_3, ua_4, ua_5, not_ua]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 6

    proxies = await in_memory_db.get_proxies(country='ukraine')
    assert len(proxies) == 5
    assert ua_1 in proxies and ua_2 in proxies and ua_3 in proxies and ua_4 in proxies and ua_5 in proxies
    assert not_ua not in proxies

    proxies = await in_memory_db.get_proxies(country='Ukraine')
    assert len(proxies) == 5
    assert ua_1 in proxies and ua_2 in proxies and ua_3 in proxies and ua_4 in proxies and ua_5 in proxies
    assert not_ua not in proxies

    proxies = await in_memory_db.get_proxies(country='UKRAINE')
    assert len(proxies) == 5
    assert ua_1 in proxies and ua_2 in proxies and ua_3 in proxies and ua_4 in proxies and ua_5 in proxies
    assert not_ua not in proxies

    proxies = await in_memory_db.get_proxies(country='UA')
    assert len(proxies) == 5
    assert ua_1 in proxies and ua_2 in proxies and ua_3 in proxies and ua_4 in proxies and ua_5 in proxies

    proxies = await in_memory_db.get_proxies(country='Ua')
    assert len(proxies) == 5
    assert ua_1 in proxies and ua_2 in proxies and ua_3 in proxies and ua_4 in proxies and ua_5 in proxies
    assert not_ua not in proxies

    proxies = await in_memory_db.get_proxies(country='ua')
    assert len(proxies) == 5
    assert ua_1 in proxies and ua_2 in proxies and ua_3 in proxies and ua_4 in proxies and ua_5 in proxies
    assert not_ua not in proxies


async def test_get_proxies_filter_last_check(in_memory_db, freezer):
    freezer.move_to('1970-01-01 00:02:35')
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    short_time_age = Proxy(ip='127.0.0.1', port=80, alive=True, last_check=150)
    long_time_ago = Proxy(ip='127.0.0.1', port=81, alive=True, last_check=10)
    add_proxies = [short_time_age, long_time_ago]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 2

    proxies = await in_memory_db.get_proxies(last_check=10)

    assert len(proxies) == 1
    assert proxies[0] == short_time_age


async def test_get_proxies_sort_ping(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    first_proxy = Proxy(ip='127.0.0.1', port=80, alive=True, ping=0.1)
    second_proxy = Proxy(ip='127.0.0.1', port=81, alive=True, ping=0.2)
    none_proxy = Proxy(ip='127.0.0.1', port=82)
    add_proxies = [first_proxy, second_proxy, none_proxy]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 3

    sort_by = 'ping'
    proxies = await in_memory_db.get_proxies(sort_by=sort_by)
    assert len(proxies) == 2
    assert proxies == [first_proxy, second_proxy]

    proxies = await in_memory_db.get_proxies(sort_by=sort_by, reverse=True)
    assert len(proxies) == 2
    assert proxies == [second_proxy, first_proxy]


async def test_get_proxies_sort_last_check(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    first_proxy = Proxy(ip='127.0.0.1', port=80, alive=True, last_check=1)
    second_proxy = Proxy(ip='127.0.0.1', port=81, alive=True, last_check=2)
    none_proxy = Proxy(ip='127.0.0.1', port=82)
    add_proxies = [first_proxy, second_proxy, none_proxy]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 3

    sort_by = 'last_check'
    proxies = await in_memory_db.get_proxies(sort_by=sort_by)
    assert len(proxies) == 2
    assert proxies == [first_proxy, second_proxy]

    proxies = await in_memory_db.get_proxies(sort_by=sort_by, reverse=True)
    assert len(proxies) == 2
    assert proxies == [second_proxy, first_proxy]


async def test_get_proxies_sort_ratio(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    first_proxy = Proxy(ip='127.0.0.1', port=80, alive=True, ratio=0.1)
    second_proxy = Proxy(ip='127.0.0.1', port=81, alive=True, ratio=0.2)
    none_proxy = Proxy(ip='127.0.0.1', port=82)
    add_proxies = [first_proxy, second_proxy, none_proxy]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 3

    sort_by = 'ratio'
    proxies = await in_memory_db.get_proxies(sort_by=sort_by)
    assert len(proxies) == 2
    assert proxies == [first_proxy, second_proxy]

    proxies = await in_memory_db.get_proxies(sort_by=sort_by, reverse=True)
    assert len(proxies) == 2
    assert proxies == [second_proxy, first_proxy]


async def test_get_proxies_sort_total_checks(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    first_proxy = Proxy(ip='127.0.0.1', port=80, alive=True, total_checks=10)
    second_proxy = Proxy(ip='127.0.0.1', port=81, alive=True, total_checks=20)
    none_proxy = Proxy(ip='127.0.0.1', port=82)
    add_proxies = [first_proxy, second_proxy, none_proxy]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 3

    sort_by = 'total_checks'
    proxies = await in_memory_db.get_proxies(sort_by=sort_by)
    assert len(proxies) == 3
    assert proxies == [none_proxy, first_proxy, second_proxy]

    proxies = await in_memory_db.get_proxies(sort_by=sort_by, reverse=True)
    assert len(proxies) == 3
    assert proxies == [second_proxy, first_proxy, none_proxy]


async def test_get_proxies_sort_raise(in_memory_db):
    proxies = await in_memory_db.get_proxies()
    assert proxies == []

    first_proxy = Proxy(ip='127.0.0.1', port=80, alive=True, total_cehcks=10)
    second_proxy = Proxy(ip='127.0.0.1', port=81, alive=True, total_checks=20)
    none_proxy = Proxy(ip='127.0.0.1', port=82)
    add_proxies = [first_proxy, second_proxy, none_proxy]
    added_count = await in_memory_db.add_proxies(add_proxies)

    assert added_count == 3

    sort_by = 'something_else'
    with pytest.raises(ValueError):
        await in_memory_db.get_proxies(sort_by=sort_by)

