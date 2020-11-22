import logging
import os
import requests
from decimal import Decimal

from bitcash.exceptions import InvalidNetwork, InvalidAddress
from bitcash.network import currency_to_satoshi
from bitcash.network.meta import Unspent
from bitcash.network.transaction import Transaction, TxPart

DEFAULT_TIMEOUT = 30

BCH_TO_SAT_MULTIPLIER = 100000000

NETWORKS = {"mainnet", "testnet", "regtest"}


def set_service_timeout(seconds):
    global DEFAULT_TIMEOUT
    DEFAULT_TIMEOUT = seconds


class BitcoinDotComAPI:
    """ rest.bitcoin.com API """

    NETWORK_ENDPOINTS = {
        "mainnet": os.getenv("BITCOINCOM_API_MAINNET", "https://rest.bitcoin.com/v2/"),
        "testnet": os.getenv("BITCOINCOM_API_TESTNET", "https://trest.bitcoin.com/v2/"),
        "regtest": os.getenv("BITCOINCOM_API_REGTEST", "http://localhost:12500/v2/"),
    }
    UNSPENT_PATH = "address/utxo/{}"
    ADDRESS_PATH = "address/details/{}"
    RAW_TX_PATH = "rawtransactions/sendRawTransaction/{}"
    TX_DETAILS_PATH = "transaction/details/{}"

    TX_PUSH_PARAM = "rawtx"

    @classmethod
    def network_endpoint(cls, network):
        if network not in NETWORKS:
            raise InvalidNetwork(f"No endpoints found for network {network}")
        return cls.NETWORK_ENDPOINTS[network]

    @classmethod
    def get_balance(cls, address, network):
        API = cls.network_endpoint(network) + cls.ADDRESS_PATH
        r = requests.get(API.format(address), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        balance = data["balanceSat"] + data["unconfirmedBalanceSat"]
        return balance

    @classmethod
    def get_transactions(cls, address, network):
        API = cls.network_endpoint(network) + cls.ADDRESS_PATH
        r = requests.get(API.format(address), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()["transactions"]

    @classmethod
    def get_transaction(cls, txid, network):
        API = cls.network_endpoint(network) + cls.TX_DETAILS_PATH
        r = requests.get(API.format(txid), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        response = r.json(parse_float=Decimal)

        tx = Transaction(
            response["txid"],
            response["blockheight"],
            (Decimal(response["valueIn"]) * BCH_TO_SAT_MULTIPLIER).normalize(),
            (Decimal(response["valueOut"]) * BCH_TO_SAT_MULTIPLIER).normalize(),
            (Decimal(response["fees"]) * BCH_TO_SAT_MULTIPLIER).normalize(),
        )

        for txin in response["vin"]:
            part = TxPart(txin["cashAddress"], txin["value"], txin["scriptSig"]["asm"])
            tx.add_input(part)

        for txout in response["vout"]:
            addr = None
            if (
                "cashAddrs" in txout["scriptPubKey"]
                and txout["scriptPubKey"]["cashAddrs"] is not None
            ):
                addr = txout["scriptPubKey"]["cashAddrs"][0]

            part = TxPart(
                addr,
                (Decimal(txout["value"]) * BCH_TO_SAT_MULTIPLIER).normalize(),
                txout["scriptPubKey"]["asm"],
            )
            tx.add_output(part)

        return tx

    @classmethod
    def get_tx_amount(cls, txid, txindex, network):
        API = cls.network_endpoint(network) + cls.TX_DETAILS_PATH
        r = requests.get(API.format(txid), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        response = r.json(parse_float=Decimal)
        return (
            Decimal(response["vout"][txindex]["value"]) * BCH_TO_SAT_MULTIPLIER
        ).normalize()

    @classmethod
    def get_unspent(cls, address, network):
        API = cls.network_endpoint(network) + cls.UNSPENT_PATH
        r = requests.get(API.format(address), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return [
            Unspent(
                currency_to_satoshi(tx["amount"], "bch"),
                tx["confirmations"],
                r.json()["scriptPubKey"],
                tx["txid"],
                tx["vout"],
            )
            for tx in r.json()["utxos"]
        ]

    @classmethod
    def get_raw_transaction(cls, txid, network):
        API = cls.network_endpoint(network) + cls.TX_DETAILS_PATH
        r = requests.get(API.format(txid), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        response = r.json(parse_float=Decimal)
        return response

    @classmethod
    def broadcast_tx(cls, tx_hex, network):  # pragma: no cover
        API = cls.network_endpoint(network) + cls.RAW_TX_PATH
        r = requests.get(API.format(tx_hex))
        return True if r.status_code == 200 else False


class BitcoreAPI:
    """ Insight API v8 """

    NETWORK_ENDPOINTS = {
        "mainnet": os.getenv(
            "BITCORE_API_MAINNET", "https://api.bitcore.io/api/BCH/mainnet/"
        ),
        "testnet": os.getenv(
            "BITCORE_API_TESTNET", "https://api.bitcore.io/api/BCH/testnet/"
        ),
    }

    MAIN_ENDPOINT = "https://api.bitcore.io/api/BCH/mainnet/"
    ADDRESS_API = "address/{}"
    BALANCE_API = ADDRESS_API + "/balance"
    UNSPENT_API = ADDRESS_API + "/?unspent=true"
    TX_PUSH_API = "tx/send"
    TX_API = "tx/{}"
    TX_AMOUNT_API = TX_API
    TX_PUSH_PARAM = "rawTx"

    @classmethod
    def network_endpoint(cls, network):
        if network not in NETWORKS:
            raise InvalidNetwork(f"No endpoints found for network {network}")
        return cls.NETWORK_ENDPOINTS[network]

    @classmethod
    def remove_prefix(cls, address):
        if ":" in address:
            address = address.split(":")[1]
        return address
        # else:
        #     raise InvalidAddress(address)

    @classmethod
    def get_unspent(cls, address, network):
        address = cls.remove_prefix(address)
        API = cls.network_endpoint(network) + cls.UNSPENT_API
        r = requests.get(API.format(address), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        unspents = []
        for tx in r.json():
            # In weird conditions, the API will send back unspents
            # without a scriptPubKey.
            if "script" in tx:
                unspents.append(
                    Unspent(
                        currency_to_satoshi(tx["value"], "satoshi"),
                        tx["confirmations"],
                        tx["script"],
                        tx["mintTxid"],
                        tx["mintIndex"],
                    )
                )
            else:
                logging.warning("Unspent without scriptPubKey.")

        return unspents

    @classmethod
    def get_transactions(cls, address, network):
        address = cls.remove_prefix(address)
        API = cls.network_endpoint(network) + cls.ADDRESS_API
        r = requests.get(API.format(address), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return [tx["mintTxid"] for tx in r.json()]

    @classmethod
    def get_balance(cls, address, network):
        address = cls.remove_prefix(address)
        API = cls.network_endpoint(network) + cls.BALANCE_API
        r = requests.get(API.format(address), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()["balance"]

    @classmethod
    def get_tx_amount(cls, txid, txindex, network):
        API = cls.network_endpoint(network) + cls.TX_AMOUNT_API
        r = requests.get(API.format(txid), timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        response = r.json(parse_float=Decimal)
        return (
            Decimal(response["vout"][txindex]["value"]) * BCH_TO_SAT_MULTIPLIER
        ).normalize()

    @classmethod
    def broadcast_tx(cls, tx_hex, network):  # pragma: no cover
        API = cls.network_endpoint(network) + cls.TX_PUSH_API
        r = requests.post(
            API,
            json={cls.TX_PUSH_PARAM: tx_hex, "network": network, "coin": "BCH"},
            timeout=DEFAULT_TIMEOUT,
        )
        return True if r.status_code == 200 else False


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

    GET_BALANCE = [BitcoinDotComAPI.get_balance, BitcoreAPI.get_balance]
    GET_TRANSACTIONS = [BitcoinDotComAPI.get_transactions, BitcoreAPI.get_transactions]
    GET_UNSPENT = [BitcoinDotComAPI.get_unspent, BitcoreAPI.get_unspent]
    BROADCAST_TX = [BitcoinDotComAPI.broadcast_tx, BitcoreAPI.broadcast_tx]
    GET_TX = [BitcoinDotComAPI.get_transaction, BitcoinDotComAPI.get_transaction]
    GET_TX_AMOUNT = [BitcoinDotComAPI.get_tx_amount, BitcoreAPI.get_tx_amount]
    GET_RAW_TX = [
        BitcoinDotComAPI.get_raw_transaction,
        BitcoinDotComAPI.get_raw_transaction,
    ]

    @classmethod
    def get_balance(cls, address, network="mainnet"):
        """Gets the balance of an address in satoshi.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``int``
        """

        for api_call in cls.GET_BALANCE:
            try:
                return api_call(address, network)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def get_transactions(cls, address, network="mainnet"):
        """Gets the ID of all transactions related to an address.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``list`` of ``str``
        """

        for api_call in cls.GET_TRANSACTIONS:
            try:
                return api_call(address, network)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def get_transaction(cls, txid, network="mainnet"):
        """Gets the full transaction details.

        :param txid: The transaction id in question.
        :type txid: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``Transaction``
        """

        for api_call in cls.GET_TX:
            try:
                return api_call(txid, network)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

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

        for api_call in cls.GET_TX_AMOUNT:
            try:
                return api_call(txid, txindex, network)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def get_unspent(cls, address, network="mainnet"):
        """Gets all unspent transaction outputs belonging to an address.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``list`` of :class:`~bitcash.network.meta.Unspent`
        """

        for api_call in cls.GET_UNSPENT:
            try:
                return api_call(address, network)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def get_raw_transaction(cls, txid, network="mainnet"):
        """Gets the raw, unparsed transaction details.

        :param txid: The transaction id in question.
        :type txid: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``Transaction``
        """

        for api_call in cls.GET_RAW_TX:
            try:
                return api_call(txid, network)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError("All APIs are unreachable.")

    @classmethod
    def broadcast_tx(cls, tx_hex, network="mainnet"):  # pragma: no cover
        """Broadcasts a transaction to the blockchain.

        :param tx_hex: A signed transaction in hex form.
        :type tx_hex: ``str``
        :raises ConnectionError: If all API services fail.
        """
        success = None

        for api_call in cls.BROADCAST_TX:
            try:
                success = api_call(tx_hex, network)
                if not success:
                    continue
                return
            except cls.IGNORED_ERRORS:
                pass

        if success is False:
            raise ConnectionError(
                "Transaction broadcast failed, or " "Unspents were already used."
            )

        raise ConnectionError("All APIs are unreachable.")
