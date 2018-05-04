from proxylist.proxy import Proxy


def test_to_dict():
    proxy = Proxy(
        ip='127.0.0.1',
        port=80,
        alive=True,
        total_checks=42,
        positive_checks=38,
        negative_checks=4,
        country='Ukraine',
        country_code='UA',
        ping=0.1,
        last_check=12345,
        protocols=['http', 'socks4', 'socks5'],
    )
    proxy_dict = proxy.to_dict()
    proxy_from_dict = Proxy(**proxy_dict)
    assert proxy == proxy_from_dict
    assert proxy != proxy_dict
