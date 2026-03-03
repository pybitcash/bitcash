from __future__ import annotations

import concurrent.futures
import socket
import ssl
import os
import threading
from typing import Any, Callable

import requests

from bitcash.network.APIs import BaseAPI, SubscriptionHandle

# Import supported endpoint APIs
from bitcash.network.APIs.BitcoinDotComAPI import BitcoinDotComAPI
from bitcash.network.APIs.ChaingraphAPI import ChaingraphAPI
from bitcash.network.APIs.FulcrumProtocolAPI import FulcrumProtocolAPI
from bitcash.network.meta import Unspent
from bitcash.network.transaction import Transaction
from bitcash.types import Network, NetworkStr
from bitcash.utils import time_cache

# Dictionary of supported endpoint APIs
ENDPOINT_ENV_VARIABLES = {
    "FULCRUM": FulcrumProtocolAPI,
    "CHAINGRAPH": ChaingraphAPI,
    "BITCOINCOM": BitcoinDotComAPI,
}

# Default API call total time timeout
DEFAULT_TIMEOUT = 5

# Default sanitized endpoint, based on blockheigt, cache timeout
DEFAULT_SANITIZED_ENDPOINTS_CACHE_TIME = 300

# Max thread workers to get blockheight
THREADWORKERS = 6

BCH_TO_SAT_MULTIPLIER = 100000000


def set_service_timeout(seconds: int) -> None:
    global DEFAULT_TIMEOUT
    DEFAULT_TIMEOUT = seconds


def get_endpoints_for(network: str) -> tuple[BaseAPI, ...]:
    # For each available interface in 'ENDPOINT_ENV_VARIABLES'
    # this function will check, in order, if any env variables
    # have been set for EITHER:
    # <NAME>_API_<NETWORK>
    # OR
    # <NAME>_API_<NETWORK>_<N>
    # Where 'N' is a number starting at 1 and increasing to
    # however many endpoints you'd like.
    # If neither of these env variables have been set, it returns
    # the instantiated result of <NAME>.get_default_endpoints(network)
    _ = Network(network)  # Validate network input

    endpoints: list[BaseAPI] = []
    for endpoint in ENDPOINT_ENV_VARIABLES.keys():
        if endpoint == "CHAINGRAPH":
            if os.getenv(f"{endpoint}_API".upper()):
                endpoints.append(
                    ENDPOINT_ENV_VARIABLES[endpoint](
                        os.getenv(f"{endpoint}_API".upper()),
                        os.getenv(f"{endpoint}_API_{network}".upper()),
                    )
                )
            elif os.getenv(f"{endpoint}_API_1".upper()):
                counter = 1
                finished = False
                while not finished:
                    next_endpoint = os.getenv(f"{endpoint}_API_{counter}".upper())
                    next_pattern = os.getenv(
                        f"{endpoint}_API_{network}_{counter}".upper()
                    )
                    if next_endpoint:
                        endpoints.append(
                            ENDPOINT_ENV_VARIABLES[endpoint](
                                next_endpoint, next_pattern
                            )
                        )
                        counter += 1
                    else:
                        finished = True
            else:
                defaults_endpoints = ENDPOINT_ENV_VARIABLES[
                    endpoint
                ].get_default_endpoints(network)
                for each in defaults_endpoints:
                    if hasattr(each, "__iter__") and not isinstance(each, str):
                        endpoints.append(ENDPOINT_ENV_VARIABLES[endpoint](*each))
                    else:
                        endpoints.append(ENDPOINT_ENV_VARIABLES[endpoint](each))
        else:
            if os.getenv(f"{endpoint}_API_{network}".upper()):
                endpoints.append(
                    ENDPOINT_ENV_VARIABLES[endpoint](
                        os.getenv(f"{endpoint}_API_{network}".upper())
                    )
                )
            elif os.getenv(f"{endpoint}_API_{network}_1".upper()):
                counter = 1
                finished = False
                while not finished:
                    next_endpoint = os.getenv(
                        f"{endpoint}_API_{network}_{counter}".upper()
                    )
                    if next_endpoint:
                        endpoints.append(
                            ENDPOINT_ENV_VARIABLES[endpoint](next_endpoint)
                        )
                        counter += 1
                    else:
                        finished = True
            else:
                defaults_endpoints = ENDPOINT_ENV_VARIABLES[
                    endpoint
                ].get_default_endpoints(network)
                for each in defaults_endpoints:
                    if hasattr(each, "__iter__") and not isinstance(each, str):
                        endpoints.append(ENDPOINT_ENV_VARIABLES[endpoint](*each))
                    else:
                        endpoints.append(ENDPOINT_ENV_VARIABLES[endpoint](each))

    return tuple(endpoints)


@time_cache(max_age=DEFAULT_SANITIZED_ENDPOINTS_CACHE_TIME, cache_size=len(Network))
def get_sanitized_endpoints_for(network: NetworkStr = "mainnet") -> tuple[BaseAPI, ...]:
    """Gets endpoints sanitized by their blockheights.
    Solves the problem when an endpoint is stuck on an older block.

    :param network: network in ["mainnet", "testnet", "regtest"].
    :returns: A tuple of sanitized endpoints.
    """

    class ThreadedGetBlockheight:
        def __init__(self, endpoints: tuple[BaseAPI, ...]):
            self.endpoints = endpoints
            self.endpoints_blockheight: list[int] = [0 for _ in range(len(endpoints))]
            self._lock = threading.Lock()

        def update(self, ind: int) -> None:
            try:
                blockheight = self.endpoints[ind].get_blockheight(
                    timeout=DEFAULT_TIMEOUT
                )
            except NetworkAPI.IGNORED_ERRORS:  # pragma: no cover
                return
            with self._lock:
                self.endpoints_blockheight[ind] = blockheight

    endpoints = get_endpoints_for(network)

    threadsafe_blockheight = ThreadedGetBlockheight(endpoints)
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADWORKERS) as executor:
        executor.map(threadsafe_blockheight.update, range(len(endpoints)))

    endpoints_blockheight = threadsafe_blockheight.endpoints_blockheight

    if sum(endpoints_blockheight) == 0:
        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    # remove unreachable or un-synced endpoints
    highest_blockheight = max(endpoints_blockheight)
    pop_indices: list[int] = []
    for i in range(len(endpoints)):
        if endpoints_blockheight[i] != highest_blockheight:
            pop_indices.append(i)

    if pop_indices:
        endpoints = list(endpoints)
        for i in sorted(pop_indices, reverse=True):
            endpoints.pop(i)
        endpoints = tuple(endpoints)

    return endpoints


class NetworkAPI:
    IGNORED_ERRORS = (
        NotImplementedError,
        requests.exceptions.RequestException,
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.ProxyError,
        requests.exceptions.SSLError,
        requests.exceptions.Timeout,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        requests.exceptions.TooManyRedirects,
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.ContentDecodingError,
        requests.exceptions.StreamConsumedError,
        # SSL socket exceptions for FulcrumProtocolAPI
        ssl.SSLError,
        ssl.SSLZeroReturnError,
        ssl.SSLWantReadError,
        ssl.SSLWantWriteError,
        ssl.SSLSyscallError,
        ssl.SSLEOFError,
        # Socket exceptions
        socket.error,
        socket.timeout,
        ConnectionResetError,
        ConnectionAbortedError,
        BrokenPipeError,
        OSError,
        TimeoutError,
    )

    @classmethod
    def get_balance(cls, address: str, network: NetworkStr = "mainnet") -> int:
        """Gets the balance of an address in satoshi.

        :param address: The address in question.
        :returns: The balance in satoshi.
        :raises ConnectionError: If all API services fail.
        """
        for endpoint in get_sanitized_endpoints_for(network):
            try:
                return endpoint.get_balance(address, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_transactions(
        cls, address: str, network: NetworkStr = "mainnet"
    ) -> list[str]:
        """Gets the ID of all transactions related to an address.

        :param address: The address in question.
        :returns: A list of transaction ids.
        :raises ConnectionError: If all API services fail.
        """
        for endpoint in get_sanitized_endpoints_for(network):
            try:
                return endpoint.get_transactions(address, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_transaction(cls, txid: str, network: NetworkStr = "mainnet") -> Transaction:
        """Gets the full transaction details.

        :param txid: The transaction id in question.
        :returns: The transaction details.
        :raises ConnectionError: If all API services fail.
        """

        for endpoint in get_sanitized_endpoints_for(network):
            try:
                return endpoint.get_transaction(txid, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_tx_amount(
        cls, txid: str, txindex: int, network: NetworkStr = "mainnet"
    ) -> int:
        """Gets the amount of a given transaction output.

        :param txid: The transaction id in question.
        :param txindex: The transaction index in question.
        :returns: The amount in satoshi.
        :raises ConnectionError: If all API services fail.
        """

        for endpoint in get_sanitized_endpoints_for(network):
            try:
                return endpoint.get_tx_amount(txid, txindex, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_unspent(
        cls, address: str, network: NetworkStr = "mainnet"
    ) -> list[Unspent]:
        """Gets all unspent transaction outputs belonging to an address.

        :param address: The address in question.
        :returns: A list of unspent transaction outputs of
            :class:`~bitcash.network.meta.Unspent`.
        :raises ConnectionError: If all API services fail.
        """

        for endpoint in get_sanitized_endpoints_for(network):
            try:
                return endpoint.get_unspent(address, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_raw_transaction(
        cls, txid: str, network: NetworkStr = "mainnet"
    ) -> dict[str, Any]:
        """Gets the raw, unparsed transaction details.

        :param txid: The transaction id in question.
        :returns: The raw transaction details.
        :raises ConnectionError: If all API services fail.
        """

        for endpoint in get_sanitized_endpoints_for(network):
            try:
                return endpoint.get_raw_transaction(txid, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def broadcast_tx(
        cls, tx_hex: str, network: NetworkStr = "mainnet"
    ):  # pragma: no cover
        """Broadcasts a transaction to the blockchain.

        :param tx_hex: A signed transaction in hex form.
        :raises ConnectionError: If all API services fail.
        :raises RuntimeError: If the transaction broadcast fails.
        """
        success = None

        for endpoint in get_sanitized_endpoints_for(network):
            if isinstance(endpoint, ChaingraphAPI):
                # ChaingraphAPI does not validate if the transaction fails
                # so we skip it to avoid false negatives
                continue
            try:
                success = endpoint.broadcast_tx(tx_hex, timeout=DEFAULT_TIMEOUT)
                if not success:
                    continue
                return
            except cls.IGNORED_ERRORS:
                pass

        if success is False:
            raise ConnectionError(
                "Transaction broadcast failed, or Unspents were already used."
            )

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def subscribe_address(
        cls,
        address: str,
        callback: Callable[[str, str | None], None],
        network: NetworkStr = "mainnet",
    ) -> SubscriptionHandle:
        """Subscribes an address for push notifications.

        :param address: The address in question.
        :param callback: Function to call with (address, status_hash) on update.
        :returns: A SubscriptionHandle to manage the subscription.
        :raises ConnectionError: If all API services fail.
        """

        for endpoint in get_sanitized_endpoints_for(network):
            try:
                return endpoint.subscribe_address(
                    address, callback, timeout=DEFAULT_TIMEOUT
                )
            except cls.IGNORED_ERRORS:
                pass
        raise ConnectionError("All APIs are unreachable.")
