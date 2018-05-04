import pytest

from proxylist.db_engine import DBEngine


pytestmark = pytest.mark.asyncio


async def test_not_implemented():
    engine = DBEngine()
    with pytest.raises(NotImplementedError):
        await engine.get_proxies()
    with pytest.raises(NotImplementedError):
        await engine.add_proxies([])
