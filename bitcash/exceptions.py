class InsufficientFunds(Exception):
    pass


class InvalidAddress(Exception):
    pass


class InvalidNetwork(Exception):
    pass


class InvalidEndpointURLProvided(Exception):
    pass


class InvalidEndpointResponse(Exception):
    pass


class TLSHandshakeError(ConnectionError):
    pass


class DataNotFound(Exception):
    pass


class InvalidCashToken(ValueError):
    pass
