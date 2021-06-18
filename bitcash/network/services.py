import os
import requests

# Import supported endpoint APIs
from bitcash.network.APIs.BitcoinDotComAPI import BitcoinDotComAPI

# Dictionary of supported endpoint APIs
ENDPOINT_ENV_VARIABLES = {"BITCOINCOM": BitcoinDotComAPI}

# Default API call total time timeout
DEFAULT_TIMEOUT = 5

BCH_TO_SAT_MULTIPLIER = 100000000

NETWORKS = {"mainnet", "testnet", "regtest"}


def set_service_timeout(seconds):
    global DEFAULT_TIMEOUT
    DEFAULT_TIMEOUT = seconds


def get_endpoints_for(network):
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

    endpoints = []
    for endpoint in ENDPOINT_ENV_VARIABLES.keys():
        if os.getenv(f"{endpoint}_API_{network}".upper()):
            endpoints.append(
                ENDPOINT_ENV_VARIABLES[endpoint](
                    os.getenv(f"{endpoint}_API_{network}".upper())))
        elif os.getenv(f"{endpoint}_API_{network}_1".upper()):
            counter = 1
            finished = False
            while not finished:
                next_endpoint = os.getenv(
                    f"{endpoint}_API_{network}_{counter}".upper())
                if next_endpoint:
                    endpoints.append(
                        ENDPOINT_ENV_VARIABLES[endpoint](next_endpoint)
                    )
                    counter += 1
                else:
                    finished = True
        else:
            defaults_endpoints = ENDPOINT_ENV_VARIABLES[endpoint].get_default_endpoints(network)
            for each in defaults_endpoints:
                endpoints.append(ENDPOINT_ENV_VARIABLES[endpoint](each))

    return endpoints


class NetworkAPI:
    IGNORED_ERRORS = (
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
    )

    @classmethod
    def get_balance(cls, address, network="mainnet"):
        """Gets the balance of an address in satoshi.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``int``
        """

        for endpoint in get_endpoints_for(network):
            try:
                return endpoint.get_balance(address, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_transactions(cls, address, network="mainnet"):
        """Gets the ID of all transactions related to an address.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``list`` of ``str``
        """

        for endpoint in get_endpoints_for(network):
            try:
                return endpoint.get_transactions(address, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_transaction(cls, txid, network="mainnet"):
        """Gets the full transaction details.

        :param txid: The transaction id in question.
        :type txid: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``Transaction``
        """

        for endpoint in get_endpoints_for(network):
            try:
                return endpoint.get_transaction(txid, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_tx_amount(cls, txid, txindex, network="mainnet"):
        """Gets the amount of a given transaction output.

        :param txid: The transaction id in question.
        :type txid: ``str``
        :param txindex: The transaction index in question.
        :type txindex: ``int``
        :raises ConnectionError: If all API services fail.
        :rtype: ``Decimal``
        """

        for endpoint in get_endpoints_for(network):
            try:
                return endpoint.get_tx_amount(txid, txindex, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_unspent(cls, address, network="mainnet"):
        """Gets all unspent transaction outputs belonging to an address.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``list`` of :class:`~bitcash.network.meta.Unspent`
        """

        for endpoint in get_endpoints_for(network):
            try:
                return endpoint.get_unspent(address, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def get_raw_transaction(cls, txid, network="mainnet"):
        """Gets the raw, unparsed transaction details.

        :param txid: The transaction id in question.
        :type txid: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``Transaction``
        """

        for endpoint in get_endpoints_for(network):
            try:
                return endpoint.get_raw_transaction(txid, timeout=DEFAULT_TIMEOUT)
            except cls.IGNORED_ERRORS:  # pragma: no cover
                pass

        raise ConnectionError("All APIs are unreachable.")  # pragma: no cover

    @classmethod
    def broadcast_tx(cls, tx_hex, network="mainnet"):  # pragma: no cover
        """Broadcasts a transaction to the blockchain.

        :param tx_hex: A signed transaction in hex form.
        :type tx_hex: ``str``
        :raises ConnectionError: If all API services fail.
        """
        success = None

        for endpoint in get_endpoints_for(network):
            try:
                success = endpoint.broadcast_tx(tx_hex, timeout=DEFAULT_TIMEOUT)
                if not success:
                    continue
                return
            except cls.IGNORED_ERRORS:
                pass

        if not success:
            raise ConnectionError(
                "Transaction broadcast failed, or " "Unspents were already used."
            )

        raise ConnectionError("All APIs are unreachable.")
