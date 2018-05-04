class Proxy:
    def __init__(self, ip: str, port: int, **kwargs):
        self.ip = ip
        self.port = port
        self.protocols = kwargs.get('protocols', None)
        self.country = kwargs.get('country', None)
        self.country_code = kwargs.get('country_code', None)
        self.ping = kwargs.get('ping', None)
        self.last_check = kwargs.get('last_check', None)
        self.alive = kwargs.get('alive', False)
        self.total_checks = kwargs.get('total_checks', 0)
        self.positive_checks = kwargs.get('positive_checks', 0)
        self.negative_checks = kwargs.get('negative_checks', 0)
        self.ratio = kwargs.get('ratio', None)

    def __eq__(self, other):
        if not isinstance(other, Proxy):
            return False
        return self.to_dict() == other.to_dict()

    def to_dict(self):
        return {
            'ip': self.ip,
            'port': self.port,
            'protocols': self.protocols,
            'country': self.country,
            'country_code': self.country_code,
            'ping': self.ping,
            'last_check': self.last_check,
            'alive': self.alive,
            'total_checks': self.total_checks,
            'positive_checks': self.positive_checks,
            'negative_checks': self.negative_checks,
            'ratio': self.ratio,
        }
