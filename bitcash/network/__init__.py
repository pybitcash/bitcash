from .rates import (
    currency_to_satoshi,
    currency_to_satoshi_cached,
    satoshi_to_currency,
    satoshi_to_currency_cached,
)
from .services import NetworkAPI

from requests import Session

#Create a re-usable session object which re-uses connection, mantains a pool.
session = Session()
#Optional: Configure user-agent here so that upstream servers know which library/version is making the request