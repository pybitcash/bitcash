import pytest

import bitcash
from bitcash.network.services import (
    BitcoinDotComAPI, BitcoreAPI, NetworkAPI, set_service_timeout
)
from tests.utils import (
    catch_errors_raise_warnings, decorate_methods, raise_connection_error
)

MAIN_ADDRESS_USED1 = 'qrg2nw20kxhspdlec82qxrgdegrq23hyuyjx2h29sy'
MAIN_ADDRESS_USED2 = 'qpr270a5sxphltdmggtj07v4nskn9gmg9yx4m5h7s4'
MAIN_ADDRESS_UNUSED = 'qzxumj0tjwwrep698rv4mnwa5ek3ddsgxuvcunqnjx'
MAIN_TX = '9bccb8d6adf53ca49cea02118871e29d3b4e5cb157dc3a475dd364e30fb20993'
TEST_ADDRESS_USED1 = 'qrnuzdzleru8c6qhpva20x9f2mp0u657luhfyxjep5'
TEST_ADDRESS_USED2 = 'qprralpnpx6zrx3w2aet97u0c6rcfrlp8v6jenepj5'
TEST_ADDRESS_USED3 = 'qpjm4n7m4r6aufkxxy5nqm5letejdm4f5sn6an6rsl'
TEST_ADDRESS_UNUSED = 'qpwn6qz29s5rv2uf0cxd7ygnwdttsuschczaz38yc5'
TEST_TX = '09d0c9773c56fac218ae084226e9db8480d9b5c6f60cc0466431d6820d344adc'
TEST_TX2 = '3c26deab2df023a8dbee15bf47701332f6661323ea117a58362b0ea9605129fd'


def all_items_common(seq):
    initial_set = set(seq[0])
    intersection_lengths = [len(set(s) & initial_set) for s in seq]
    return all_items_equal(intersection_lengths)


def all_items_equal(seq):
    initial_item = seq[0]
    return all(item == initial_item for item in seq if item is not None)


def test_set_service_timeout():
    original = bitcash.network.services.DEFAULT_TIMEOUT
    set_service_timeout(3)
    updated = bitcash.network.services.DEFAULT_TIMEOUT

    assert original != updated
    assert updated == 3

    set_service_timeout(original)


class MockBackend(NetworkAPI):
    IGNORED_ERRORS = NetworkAPI.IGNORED_ERRORS
    GET_BALANCE_MAIN = [raise_connection_error]
    GET_TRANSACTIONS_MAIN = [raise_connection_error]
    GET_UNSPENT_MAIN = [raise_connection_error]
    GET_BALANCE_TEST = [raise_connection_error]
    GET_TRANSACTIONS_TEST = [raise_connection_error]
    GET_UNSPENT_TEST = [raise_connection_error]


class TestNetworkAPI:
    def test_get_balance_main_equal(self):
        results = [call(MAIN_ADDRESS_USED2) for call in NetworkAPI.GET_BALANCE_MAIN]
        assert all(result == results[0] for result in results)

    def test_get_balance_main_failure(self):
        with pytest.raises(ConnectionError):
            MockBackend.get_balance(MAIN_ADDRESS_USED2)

    def test_get_balance_test_equal(self):
        results = [call(TEST_ADDRESS_USED2) for call in NetworkAPI.GET_BALANCE_TEST]
        assert all(result == results[0] for result in results)

    def test_get_balance_test_failure(self):
        with pytest.raises(ConnectionError):
            MockBackend.get_balance_testnet(TEST_ADDRESS_USED2)

    # FIXME: Bitcore.io only returns unspents
    # def test_get_transactions_main_equal(self):
    #     results = [call(MAIN_ADDRESS_USED1)[:100] for call in NetworkAPI.GET_TRANSACTIONS_MAIN]
    #     assert all_items_common(results)

    def test_get_transactions_main_failure(self):
        with pytest.raises(ConnectionError):
            MockBackend.get_transactions(MAIN_ADDRESS_USED1)

    def test_get_transactions_test_equal(self):
        results = [call(TEST_ADDRESS_USED2)[:100] for call in NetworkAPI.GET_TRANSACTIONS_TEST]
        assert all_items_common(results)

    def test_get_transactions_test_failure(self):
        with pytest.raises(ConnectionError):
            MockBackend.get_transactions_testnet(TEST_ADDRESS_USED2)

    def test_get_unspent_main_equal(self):
        results = [call(MAIN_ADDRESS_USED2) for call in NetworkAPI.GET_UNSPENT_MAIN]
        assert all_items_equal(results)

    def test_get_unspent_main_failure(self):
        with pytest.raises(ConnectionError):
            MockBackend.get_unspent(MAIN_ADDRESS_USED1)

    def test_get_unspent_test_equal(self):
        results = [call(TEST_ADDRESS_USED3) for call in NetworkAPI.GET_UNSPENT_TEST]
        assert all_items_equal(results)

    def test_get_unspent_test_failure(self):
        with pytest.raises(ConnectionError):
            MockBackend.get_unspent_testnet(TEST_ADDRESS_USED2)


@decorate_methods(catch_errors_raise_warnings, NetworkAPI.IGNORED_ERRORS)
class TestBitcoinDotComAPI:
    def test_get_balance_return_type(self):
        assert isinstance(BitcoinDotComAPI.get_balance(MAIN_ADDRESS_USED1), int)

    def test_get_balance_main_used(self):
        assert BitcoinDotComAPI.get_balance(MAIN_ADDRESS_USED1) > 0

    def test_get_balance_main_unused(self):
        assert BitcoinDotComAPI.get_balance(MAIN_ADDRESS_UNUSED) == 0

    def test_get_balance_test_used(self):
        assert BitcoinDotComAPI.get_balance_testnet(TEST_ADDRESS_USED2) > 0

    def test_get_balance_test_unused(self):
        assert BitcoinDotComAPI.get_balance_testnet(TEST_ADDRESS_UNUSED) == 0

    def test_get_transactions_return_type(self):
        assert iter(BitcoinDotComAPI.get_transactions(MAIN_ADDRESS_USED1))

    def test_get_transactions_main_used(self):
        assert len(BitcoinDotComAPI.get_transactions(MAIN_ADDRESS_USED1)) >= 218

    def test_get_transactions_main_unused(self):
        assert len(BitcoinDotComAPI.get_transactions(MAIN_ADDRESS_UNUSED)) == 0

    def test_get_transaction(self):
        assert len(str(BitcoinDotComAPI.get_transaction(MAIN_TX))) >= 156

    def test_get_transaction_testnet(self):
        assert len(str(BitcoinDotComAPI.get_transaction_testnet(TEST_TX2))) >= 156

    def test_get_transactions_test_used(self):
        assert len(BitcoinDotComAPI.get_transactions_testnet(TEST_ADDRESS_USED2)) >= 444

    def test_get_transactions_test_unused(self):
        assert len(BitcoinDotComAPI.get_transactions_testnet(TEST_ADDRESS_UNUSED)) == 0

    def test_get_unspent_return_type(self):
        assert iter(BitcoinDotComAPI.get_unspent(MAIN_ADDRESS_USED1))

    def test_get_unspent_main_used(self):
        assert len(BitcoinDotComAPI.get_unspent(MAIN_ADDRESS_USED2)) >= 1

    def test_get_unspent_main_unused(self):
        assert len(BitcoinDotComAPI.get_unspent(MAIN_ADDRESS_UNUSED)) == 0

    def test_get_unspent_test_used(self):
        assert len(BitcoinDotComAPI.get_unspent_testnet(TEST_ADDRESS_USED2)) >= 194

    def test_get_unspent_test_unused(self):
        assert len(BitcoinDotComAPI.get_unspent_testnet(TEST_ADDRESS_UNUSED)) == 0

    def test_get_raw_transaction(self):
        assert BitcoinDotComAPI.get_raw_transaction(MAIN_TX)['txid'] == MAIN_TX

    def test_get_raw_transaction_testnet(self):
        assert BitcoinDotComAPI.get_raw_transaction_testnet(TEST_TX)['txid'] == TEST_TX


@decorate_methods(catch_errors_raise_warnings, NetworkAPI.IGNORED_ERRORS)
class TestBitcoreAPI:
    def test_get_balance_return_type(self):
        assert isinstance(BitcoreAPI.get_balance(MAIN_ADDRESS_USED1), int)

    def test_get_balance_main_used(self):
        assert BitcoreAPI.get_balance(MAIN_ADDRESS_USED1) > 0

    def test_get_balance_main_unused(self):
        assert BitcoreAPI.get_balance(MAIN_ADDRESS_UNUSED) == 0

    def test_get_balance_test_used(self):
        assert BitcoreAPI.get_balance_testnet(TEST_ADDRESS_USED2) > 0

    def test_get_balance_test_unused(self):
        assert BitcoreAPI.get_balance_testnet(TEST_ADDRESS_UNUSED) == 0

    def test_get_transactions_return_type(self):
        assert iter(BitcoreAPI.get_transactions(MAIN_ADDRESS_USED1))

    # FIXME: Bitcore.io only returns 10 elements
    # def test_get_transactions_main_used(self):
    #     assert len(BitcoreAPI.get_transactions(MAIN_ADDRESS_USED1)) >= 218

    def test_get_transactions_main_unused(self):
        assert len(BitcoreAPI.get_transactions(MAIN_ADDRESS_UNUSED)) == 0

    # FIXME: Bitcore.io only returns 10 elements
    # def test_get_transactions_test_used(self):
    #     assert len(BitcoreAPI.get_transactions_testnet(TEST_ADDRESS_USED2)) >= 444

    def test_get_transactions_test_unused(self):
        assert len(BitcoreAPI.get_transactions_testnet(TEST_ADDRESS_UNUSED)) == 0

    def test_get_unspent_return_type(self):
        assert iter(BitcoreAPI.get_unspent(MAIN_ADDRESS_USED1))

    def test_get_unspent_main_used(self):
        assert len(BitcoreAPI.get_unspent(MAIN_ADDRESS_USED2)) >= 1

    def test_get_unspent_main_unused(self):
        assert len(BitcoreAPI.get_unspent(MAIN_ADDRESS_UNUSED)) == 0

    # FIXME: Bitcore.io only returns 10 elements
    # def test_get_unspent_test_used(self):
    #     assert len(BitcoreAPI.get_unspent_testnet(TEST_ADDRESS_USED2)) >= 194

    def test_get_unspent_test_unused(self):
        assert len(BitcoreAPI.get_unspent_testnet(TEST_ADDRESS_UNUSED)) == 0
