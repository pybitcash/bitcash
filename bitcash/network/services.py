import logging

import requests
from cashaddress import convert as cashaddress
from decimal import Decimal

from bitcash.network import currency_to_satoshi
from bitcash.network.meta import Unspent
from bitcash.network.transaction import Transaction, TxPart

DEFAULT_TIMEOUT = 30

BCH_TO_SAT_MULTIPLIER = 100000000


def set_service_timeout(seconds):
    global DEFAULT_TIMEOUT
    DEFAULT_TIMEOUT = seconds


class InsightAPI:
    MAIN_ENDPOINT = ''
    MAIN_ADDRESS_API = ''
    MAIN_BALANCE_API = ''
    MAIN_UNSPENT_API = ''
    MAIN_TX_PUSH_API = ''
    MAIN_TX_API = ''
    MAIN_TX_AMOUNT_API = ''
    TX_PUSH_PARAM = ''

    @classmethod
    def get_balance(cls, address):
        r = requests.get(cls.MAIN_BALANCE_API.format(address), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        return r.json()

    @classmethod
    def get_transactions(cls, address):
        r = requests.get(cls.MAIN_ADDRESS_API.format(address), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        return r.json()['transactions']

    @classmethod
    def get_transaction(cls, txid):
        r = requests.get(cls.MAIN_TX_API.format(txid), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        response = r.json(parse_float=Decimal)

        tx = Transaction(response['txid'], response['blockheight'],
                (Decimal(response['valueIn']) * BCH_TO_SAT_MULTIPLIER).normalize(),
                (Decimal(response['valueOut']) * BCH_TO_SAT_MULTIPLIER).normalize(),
                (Decimal(response['fees']) * BCH_TO_SAT_MULTIPLIER).normalize())

        for txin in response['vin']:
            part = TxPart(txin['addr'], txin['valueSat'], txin['scriptSig']['asm'])
            tx.add_input(part)

        for txout in response['vout']:
            addr = None
            if 'addresses' in txout['scriptPubKey'] and txout['scriptPubKey']['addresses'] is not None:
                addr = txout['scriptPubKey']['addresses'][0]

            part = TxPart(addr,
                    (Decimal(txout['value']) * BCH_TO_SAT_MULTIPLIER).normalize(),
                    txout['scriptPubKey']['asm'])
            tx.add_output(part)

        return tx

    @classmethod
    def get_tx_amount(cls, txid, txindex):
        r = requests.get(cls.MAIN_TX_AMOUNT_API.format(txid), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        response = r.json(parse_float=Decimal)
        return (Decimal(response['vout'][txindex]['value']) * BCH_TO_SAT_MULTIPLIER).normalize()

    @classmethod
    def get_unspent(cls, address):
        r = requests.get(cls.MAIN_UNSPENT_API.format(address), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        return [
            Unspent(currency_to_satoshi(tx['amount'], 'bch'),
                    tx['confirmations'],
                    tx['scriptPubKey'],
                    tx['txid'],
                    tx['vout'])
            for tx in r.json()
        ]

    @classmethod
    def broadcast_tx(cls, tx_hex):  # pragma: no cover
        r = requests.post(cls.MAIN_TX_PUSH_API, json={cls.TX_PUSH_PARAM: tx_hex}, timeout=DEFAULT_TIMEOUT)
        return True if r.status_code == 200 else False


class CashExplorerBitcoinDotComAPI(InsightAPI):
    """
    cashexplorer.bitcoin.com
    No testnet, sadly. Also uses legacy addresses only.
    """
    MAIN_ENDPOINT = 'https://cashexplorer.bitcoin.com/api/'
    MAIN_ADDRESS_API = MAIN_ENDPOINT + 'addr/{}'
    MAIN_BALANCE_API = MAIN_ADDRESS_API + '/balance'
    MAIN_UNSPENT_API = MAIN_ADDRESS_API + '/utxo'
    MAIN_TX_PUSH_API = MAIN_ENDPOINT + 'tx/send'
    MAIN_TX_API = MAIN_ENDPOINT + 'tx/{}'
    MAIN_TX_AMOUNT_API = MAIN_TX_API
    TX_PUSH_PARAM = 'rawtx'

    @classmethod
    def get_balance(cls, address):
        # As of 2018-05-16, cashexplorer.bitcoin.com only supports legacy addresses.
        address = cashaddress.to_legacy_address(address)
        r = requests.get(cls.MAIN_BALANCE_API.format(address), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        return r.json()

    @classmethod
    def get_transactions(cls, address):
        # As of 2018-05-16, cashexplorer.bitcoin.com only supports legacy addresses.
        address = cashaddress.to_legacy_address(address)
        r = requests.get(cls.MAIN_ADDRESS_API.format(address), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        return r.json()['transactions']

    @classmethod
    def get_unspent(cls, address):
        # As of 2018-05-16, cashexplorer.bitcoin.com only supports legacy addresses.
        address = cashaddress.to_legacy_address(address)
        r = requests.get(cls.MAIN_UNSPENT_API.format(address), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        return [
            Unspent(currency_to_satoshi(tx['amount'], 'bch'),
                    tx['confirmations'],
                    tx['scriptPubKey'],
                    tx['txid'],
                    tx['vout'])
            for tx in r.json()
        ]


class BlockdozerAPI(InsightAPI):
    MAIN_ENDPOINT = 'https://blockdozer.com/api/'
    MAIN_ADDRESS_API = MAIN_ENDPOINT + 'addr/{}'
    MAIN_BALANCE_API = MAIN_ADDRESS_API + '/balance'
    MAIN_UNSPENT_API = MAIN_ADDRESS_API + '/utxo'
    MAIN_TX_PUSH_API = MAIN_ENDPOINT + 'tx/send'
    MAIN_TX_API = MAIN_ENDPOINT + 'tx/{}'
    MAIN_TX_AMOUNT_API = MAIN_TX_API
    TEST_ENDPOINT = 'https://tbch.blockdozer.com/api/'
    TEST_ADDRESS_API = TEST_ENDPOINT + 'addr/{}'
    TEST_BALANCE_API = TEST_ADDRESS_API + '/balance'
    TEST_UNSPENT_API = TEST_ADDRESS_API + '/utxo'
    TEST_TX_PUSH_API = TEST_ENDPOINT + 'tx/send'
    TEST_TX_API = TEST_ENDPOINT + 'tx/{}'
    TEST_TX_AMOUNT_API = TEST_TX_API
    TX_PUSH_PARAM = 'rawtx'

    @classmethod
    def get_balance_testnet(cls, address):
        r = requests.get(cls.TEST_BALANCE_API.format(address), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        return r.json()

    @classmethod
    def get_transactions_testnet(cls, address):
        r = requests.get(cls.TEST_ADDRESS_API.format(address), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        return r.json()['transactions']

    @classmethod
    def get_transaction_testnet(cls, txid):
        r = requests.get(cls.TEST_TX_API.format(txid), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        response = r.json(parse_float=Decimal)

        tx = Transaction(response['txid'], response['blockheight'],
                (Decimal(response['valueIn']) * BCH_TO_SAT_MULTIPLIER).normalize(),
                (Decimal(response['valueOut']) * BCH_TO_SAT_MULTIPLIER).normalize(),
                (Decimal(response['fees']) * BCH_TO_SAT_MULTIPLIER).normalize())

        for txin in response['vin']:
            part = TxPart(txin['addr'], txin['valueSat'], txin['scriptSig']['asm'])
            tx.add_input(part)

        for txout in response['vout']:
            addr = None
            if 'addresses' in txout['scriptPubKey'] and txout['scriptPubKey']['addresses'] is not None:
                addr = txout['scriptPubKey']['addresses'][0]

            part = TxPart(addr,
                    (Decimal(txout['value']) * BCH_TO_SAT_MULTIPLIER).normalize(),
                    txout['scriptPubKey']['asm'])
            tx.add_output(part)

        return tx

    @classmethod
    def get_tx_amount_testnet(cls, txid, txindex):
        r = requests.get(cls.TEST_TX_AMOUNT_API.format(txid), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        response = r.json(parse_float=Decimal)
        return (Decimal(response['vout'][txindex]['value']) * BCH_TO_SAT_MULTIPLIER).normalize()

    @classmethod
    def get_unspent_testnet(cls, address):
        r = requests.get(cls.TEST_UNSPENT_API.format(address), timeout=DEFAULT_TIMEOUT)
        if r.status_code != 200:  # pragma: no cover
            raise ConnectionError
        unspents = []
        for tx in r.json():
            # In weird conditions, the API will send back unspents without a scriptPubKey.
            if 'scriptPubKey' in tx:
                unspents.append(Unspent(currency_to_satoshi(tx['amount'], 'bch'),
                                        tx['confirmations'],
                                        tx['scriptPubKey'],
                                        tx['txid'],
                                        tx['vout']))
            else:
                logging.warning('Unspent without scriptPubKey.')

        return unspents

    @classmethod
    def broadcast_tx_testnet(cls, tx_hex):  # pragma: no cover
        r = requests.post(cls.TEST_TX_PUSH_API, json={cls.TX_PUSH_PARAM: tx_hex}, timeout=DEFAULT_TIMEOUT)
        if r.status_code == 200:
            return True
        else:
            logging.error(r.text)
            return False


class NetworkAPI:
    IGNORED_ERRORS = (ConnectionError,
                      requests.exceptions.ConnectionError,
                      requests.exceptions.Timeout,
                      requests.exceptions.ReadTimeout)

    GET_BALANCE_MAIN = [CashExplorerBitcoinDotComAPI.get_balance,
                        BlockdozerAPI.get_balance]
    GET_TRANSACTIONS_MAIN = [CashExplorerBitcoinDotComAPI.get_transactions,
                             BlockdozerAPI.get_transactions]
    GET_UNSPENT_MAIN = [CashExplorerBitcoinDotComAPI.get_unspent,
                        BlockdozerAPI.get_unspent]
    BROADCAST_TX_MAIN = [CashExplorerBitcoinDotComAPI.broadcast_tx,
                         BlockdozerAPI.broadcast_tx]
    GET_TX_MAIN = [CashExplorerBitcoinDotComAPI.get_transaction,
                   BlockdozerAPI.get_transaction]
    GET_TX_AMOUNT_MAIN = [CashExplorerBitcoinDotComAPI.get_tx_amount,
                          BlockdozerAPI.get_tx_amount]

    GET_BALANCE_TEST = [BlockdozerAPI.get_balance_testnet]
    GET_TRANSACTIONS_TEST = [BlockdozerAPI.get_transactions_testnet]
    GET_UNSPENT_TEST = [BlockdozerAPI.get_unspent_testnet]
    BROADCAST_TX_TEST = [BlockdozerAPI.broadcast_tx_testnet]
    GET_TX_TEST = [BlockdozerAPI.get_transaction_testnet]
    GET_TX_AMOUNT_TEST = [BlockdozerAPI.get_tx_amount_testnet]

    @classmethod
    def get_balance(cls, address):
        """Gets the balance of an address in satoshi.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``int``
        """

        for api_call in cls.GET_BALANCE_MAIN:
            try:
                return api_call(address)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def get_balance_testnet(cls, address):
        """Gets the balance of an address on the test network in satoshi.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``int``
        """

        for api_call in cls.GET_BALANCE_TEST:
            try:
                return api_call(address)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def get_transactions(cls, address):
        """Gets the ID of all transactions related to an address.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``list`` of ``str``
        """

        for api_call in cls.GET_TRANSACTIONS_MAIN:
            try:
                return api_call(address)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def get_transactions_testnet(cls, address):
        """Gets the ID of all transactions related to an address on the test
        network.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``list`` of ``str``
        """

        for api_call in cls.GET_TRANSACTIONS_TEST:
            try:
                return api_call(address)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def get_transaction(cls, txid):
        """Gets the full transaction details.

        :param txid: The transaction id in question.
        :type txid: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``Transaction``
        """

        for api_call in cls.GET_TX_MAIN:
            try:
                return api_call(txid)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def get_transaction_testnet(cls, txid):
        """Gets the full transaction details on the test
        network.

        :param txid: The transaction id in question.
        :type txid: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``Transaction``
        """

        for api_call in cls.GET_TX_TEST:
            try:
                return api_call(txid)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def get_tx_amount(cls, txid, txindex):
        """Gets the amount of a given transaction output.

        :param txid: The transaction id in question.
        :type txid: ``str``
        :param txindex: The transaction index in question.
        :type txindex: ``int``
        :raises ConnectionError: If all API services fail.
        :rtype: ``Decimal``
        """

        for api_call in cls.GET_TX_AMOUNT_MAIN:
            try:
                return api_call(txid, txindex)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def get_tx_amount_testnet(cls, txid, txindex):
        """Gets the amount of a given transaction output on the
        test network.

        :param txid: The transaction id in question.
        :type txid: ``str``
        :param txindex: The transaction index in question.
        :type txindex: ``int``
        :raises ConnectionError: If all API services fail.
        :rtype: ``Decimal``
        """

        for api_call in cls.GET_TX_AMOUNT_TEST:
            try:
                return api_call(txid, txindex)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def get_unspent(cls, address):
        """Gets all unspent transaction outputs belonging to an address.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``list`` of :class:`~bitcash.network.meta.Unspent`
        """

        for api_call in cls.GET_UNSPENT_MAIN:
            try:
                return api_call(address)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def get_unspent_testnet(cls, address):
        """Gets all unspent transaction outputs belonging to an address on the
        test network.

        :param address: The address in question.
        :type address: ``str``
        :raises ConnectionError: If all API services fail.
        :rtype: ``list`` of :class:`~bitcash.network.meta.Unspent`
        """

        for api_call in cls.GET_UNSPENT_TEST:
            try:
                return api_call(address)
            except cls.IGNORED_ERRORS:
                pass

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def broadcast_tx(cls, tx_hex):  # pragma: no cover
        """Broadcasts a transaction to the blockchain.

        :param tx_hex: A signed transaction in hex form.
        :type tx_hex: ``str``
        :raises ConnectionError: If all API services fail.
        """
        success = None

        for api_call in cls.BROADCAST_TX_MAIN:
            try:
                success = api_call(tx_hex)
                if not success:
                    continue
                return
            except cls.IGNORED_ERRORS:
                pass

        if success is False:
            raise ConnectionError('Transaction broadcast failed, or '
                                  'Unspents were already used.')

        raise ConnectionError('All APIs are unreachable.')

    @classmethod
    def broadcast_tx_testnet(cls, tx_hex):  # pragma: no cover
        """Broadcasts a transaction to the test network's blockchain.

        :param tx_hex: A signed transaction in hex form.
        :type tx_hex: ``str``
        :raises ConnectionError: If all API services fail.
        """
        success = None

        for api_call in cls.BROADCAST_TX_TEST:
            try:
                success = api_call(tx_hex)
                if not success:
                    continue
                return
            except cls.IGNORED_ERRORS:
                pass

        if success is False:
            raise ConnectionError('Transaction broadcast failed, or '
                                  'Unspents were already used.')

        raise ConnectionError('All APIs are unreachable.')
