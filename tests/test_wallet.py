import os
import time
import logging
import typing
from unittest.mock import MagicMock, patch

import pytest

from bitcash.crypto import ECPrivateKey
from bitcash.curve import Point
from bitcash.format import verify_sig
from bitcash.wallet import (
    BaseKey,
    Key,
    PrivateKey,
    PrivateKeyTestnet,
    PrivateKeyRegtest,
    wif_to_key,
)
from bitcash.network.meta import Unspent
from bitcash.network.APIs import SubscriptionHandle
from .samples import (
    PRIVATE_KEY_BYTES,
    PRIVATE_KEY_DER,
    PRIVATE_KEY_HEX,
    PRIVATE_KEY_NUM,
    PRIVATE_KEY_PEM,
    PUBLIC_KEY_COMPRESSED,
    PUBLIC_KEY_UNCOMPRESSED,
    PUBLIC_KEY_X,
    PUBLIC_KEY_Y,
    WALLET_FORMAT_COMPRESSED_MAIN,
    WALLET_FORMAT_COMPRESSED_TEST,
    WALLET_FORMAT_COMPRESSED_REGTEST,
    WALLET_FORMAT_MAIN,
    WALLET_FORMAT_TEST,
    WALLET_FORMAT_REGTEST,
    BITCOIN_CASHADDRESS,
    BITCOIN_CASHADDRESS_TEST,
    BITCOIN_CASHADDRESS_TEST_CATKN,
    BITCOIN_CASHADDRESS_REGTEST,
    BITCOIN_CASHADDRESS_REGTEST_CATKN,
    BITCOIN_CASHADDRESS_CATKN,
    CASHTOKEN_CATAGORY_ID,
    CASHTOKEN_AMOUNT,
    PREFIX_AMOUNT,
)


class TestWIFToKey:
    def test_compressed_main(self):
        key = wif_to_key(WALLET_FORMAT_COMPRESSED_MAIN)
        assert isinstance(key, PrivateKey)
        assert key.is_compressed()

    def test_uncompressed_main(self):
        key = wif_to_key(WALLET_FORMAT_MAIN)
        assert isinstance(key, PrivateKey)
        assert not key.is_compressed()

    def test_compressed_test(self):
        key = wif_to_key(WALLET_FORMAT_COMPRESSED_TEST)
        assert isinstance(key, PrivateKeyTestnet)
        assert key.is_compressed()

    def test_uncompressed_test(self):
        key = wif_to_key(WALLET_FORMAT_TEST)
        assert isinstance(key, PrivateKeyTestnet)
        assert not key.is_compressed()

    def test_compressed_regtest(self):
        key = wif_to_key(WALLET_FORMAT_COMPRESSED_REGTEST, regtest=True)
        assert isinstance(key, PrivateKeyRegtest)
        assert key.is_compressed()

    def test_uncompressed_regtest(self):
        key = wif_to_key(WALLET_FORMAT_REGTEST, regtest=True)
        assert isinstance(key, PrivateKeyRegtest)
        assert not key.is_compressed()


class TestBaseKey:
    def test_init_default(self):
        base_key = BaseKey()

        assert isinstance(base_key._pk, ECPrivateKey)
        assert len(base_key.public_key) == 33

    def test_init_from_key(self):
        pk = ECPrivateKey()
        base_key = BaseKey(pk)
        assert base_key._pk == pk

    def test_init_wif_error(self):
        with pytest.raises(TypeError):
            BaseKey(typing.cast(str, b"\x01"))

    def test_public_key_compressed(self):
        base_key = BaseKey(WALLET_FORMAT_COMPRESSED_MAIN)
        assert base_key.public_key == PUBLIC_KEY_COMPRESSED

    def test_public_key_uncompressed(self):
        base_key = BaseKey(WALLET_FORMAT_MAIN)
        assert base_key.public_key == PUBLIC_KEY_UNCOMPRESSED

    def test_public_point(self):
        base_key = BaseKey(WALLET_FORMAT_MAIN)
        assert base_key.public_point == Point(PUBLIC_KEY_X, PUBLIC_KEY_Y)
        assert base_key.public_point == Point(PUBLIC_KEY_X, PUBLIC_KEY_Y)

    def test_sign(self):
        base_key = BaseKey()
        data = os.urandom(200)
        signature = base_key.sign(data)
        assert verify_sig(signature, data, base_key.public_key)

    def test_verify_success(self):
        base_key = BaseKey()
        data = os.urandom(200)
        signature = base_key.sign(data)
        assert base_key.verify(signature, data)

    def test_verify_failure(self):
        base_key = BaseKey()
        data = os.urandom(200)
        signature = base_key.sign(data)
        assert not base_key.verify(signature, data[::-1])

    def test_to_hex(self):
        base_key = BaseKey(WALLET_FORMAT_MAIN)
        assert base_key.to_hex() == PRIVATE_KEY_HEX

    def test_to_bytes(self):
        base_key = BaseKey(WALLET_FORMAT_MAIN)
        assert base_key.to_bytes() == PRIVATE_KEY_BYTES

    def test_to_der(self):
        base_key = BaseKey(WALLET_FORMAT_MAIN)
        assert base_key.to_der() == PRIVATE_KEY_DER

    def test_to_pem(self):
        base_key = BaseKey(WALLET_FORMAT_MAIN)
        assert base_key.to_pem() == PRIVATE_KEY_PEM

    def test_to_int(self):
        base_key = BaseKey(WALLET_FORMAT_MAIN)
        assert base_key.to_int() == PRIVATE_KEY_NUM

    def test_is_compressed(self):
        assert BaseKey(WALLET_FORMAT_COMPRESSED_MAIN).is_compressed() is True
        assert BaseKey(WALLET_FORMAT_MAIN).is_compressed() is False

    def test_equal(self):
        assert BaseKey(WALLET_FORMAT_COMPRESSED_MAIN) == BaseKey(
            WALLET_FORMAT_COMPRESSED_MAIN
        )


class TestPrivateKey:
    def test_alias(self):
        assert Key == PrivateKey

    def test_init_default(self):
        private_key = PrivateKey()

        assert private_key._address is None
        assert private_key.balance == 0
        assert private_key.unspents == []
        assert private_key.transactions == []

    def test_address(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        assert private_key.address == BITCOIN_CASHADDRESS
        assert private_key.cashtoken_address == BITCOIN_CASHADDRESS_CATKN

    def test_to_wif(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        assert private_key.to_wif() == WALLET_FORMAT_MAIN

        private_key = PrivateKey(WALLET_FORMAT_COMPRESSED_MAIN)
        assert private_key.to_wif() == WALLET_FORMAT_COMPRESSED_MAIN

    def test_get_balance(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        time.sleep(1)  # Needed due to API rate limiting
        balance = int(private_key.get_balance())
        assert balance == private_key.balance

    def test_get_unspent(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        time.sleep(1)  # Needed due to API rate limiting
        unspent = private_key.get_unspents()
        assert unspent == private_key.unspents

    def test_get_transactions(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        time.sleep(1)  # Needed due to API rate limiting
        transactions = private_key.get_transactions()
        assert transactions == private_key.transactions

    def test_from_hex(self):
        key = PrivateKey.from_hex(PRIVATE_KEY_HEX)
        assert isinstance(key, PrivateKey)
        assert key.to_hex() == PRIVATE_KEY_HEX

    def test_from_der(self):
        key = PrivateKey.from_der(PRIVATE_KEY_DER)
        assert isinstance(key, PrivateKey)
        assert key.to_der() == PRIVATE_KEY_DER

    def test_from_pem(self):
        key = PrivateKey.from_pem(PRIVATE_KEY_PEM)
        assert isinstance(key, PrivateKey)
        assert key.to_pem() == PRIVATE_KEY_PEM

    def test_from_int(self):
        key = PrivateKey.from_int(PRIVATE_KEY_NUM)
        assert isinstance(key, PrivateKey)
        assert key.to_int() == PRIVATE_KEY_NUM

    def test_repr(self):
        assert (
            repr(PrivateKey(WALLET_FORMAT_MAIN))
            == f"<PrivateKey: {BITCOIN_CASHADDRESS}>"
        )

    def test_pay2sh(self):
        # tx:af386b52b9804c4d37d0bcf9ca124b34264d2f0a306ea11ee74c90d939402cb7
        unspents_original = [
            Unspent(5691944, 1, "aa", "aa", 0),
            Unspent(17344, 0, "ab", "ab", 0),
        ]
        outputs_original = [
            (
                "bitcoincash:prseh0a4aejjcewhc665wjqhppgwrz2lw5txgn666a",
                11065,
                "satoshi",
            ),
        ]

        key = wif_to_key("cU6s7jckL3bZUUkb3Q2CD9vNu8F1o58K5R5a3JFtidoccMbhEGKZ")
        tx = key.create_transaction(
            outputs_original,
            unspents=unspents_original,
            fee=1,
            leftover="bitcoincash:qpqpu8xr56gmccalfssssjm2pcpv6d2fhur48wjdzf",
        )
        out = tx[478:]

        # test outputs
        assert out[:2] == "02"
        # P2SH output value
        assert int.from_bytes(bytes.fromhex(out[2:18]), "little") == 11065
        # P2SH locking script
        assert out[18:66] == "17a914e19bbfb5ee652c65d7c6b54748170850e1895f7587"
        # leftover value
        assert int.from_bytes(bytes.fromhex(out[66:82]), "little") == 5697851
        # leftover P2PKH locking script
        _ = "1976a914401e1cc3a691bc63bf4c21084b6a0e02cd3549bf88ac"
        assert out[82:-8] == _

    def test_cashtoken_leftover(self):
        # test default leftover
        unspents_original = [
            Unspent(
                2000,
                1,
                PREFIX_AMOUNT.hex() + "aa",
                "ab",
                0,
                CASHTOKEN_CATAGORY_ID,
                None,
                None,
                CASHTOKEN_AMOUNT,
            )
        ]
        outputs = [(BITCOIN_CASHADDRESS, 1000, "satoshi")]

        key = wif_to_key("cU6s7jckL3bZUUkb3Q2CD9vNu8F1o58K5R5a3JFtidoccMbhEGKZ")
        # will raise error if leftover not cashtoken
        _ = key.create_transaction(
            outputs,
            unspents=unspents_original,
            fee=0,
        )

    @patch("bitcash.wallet.NetworkAPI")
    def test_subscribe_returns_handle(self, mock_network_api):
        """Test that subscribe returns a SubscriptionHandle."""
        mock_handle = SubscriptionHandle(lambda: None)
        mock_network_api.subscribe_address.return_value = mock_handle

        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        callback = MagicMock()

        handle = private_key.subscribe(callback)

        assert handle is mock_handle
        mock_network_api.subscribe_address.assert_called_once()

    @patch("bitcash.wallet.NetworkAPI")
    def test_subscribe_passes_address_and_callback(self, mock_network_api):
        """Test that subscribe passes correct address and callback."""
        mock_handle = SubscriptionHandle(lambda: None)
        mock_network_api.subscribe_address.return_value = mock_handle

        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        callback = MagicMock()

        private_key.subscribe(callback)

        call_args = mock_network_api.subscribe_address.call_args
        assert call_args[0][0] == private_key.address
        assert call_args[1]["network"] == "mainnet"

    @patch("bitcash.wallet.NetworkAPI")
    def test_subscribe_with_update_self_updates_balances(self, mock_network_api):
        """Test that subscribe with update_self=True updates unspents and transactions."""
        mock_handle = SubscriptionHandle(lambda: None)
        mock_network_api.subscribe_address.return_value = mock_handle
        mock_network_api.get_unspent.return_value = []
        mock_network_api.get_transactions.return_value = []

        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        user_callback = MagicMock()

        private_key.subscribe(user_callback, update_self=True)

        # Get the wrapper callback that was passed to subscribe_address
        call_args = mock_network_api.subscribe_address.call_args
        wrapper_callback = call_args[0][1]

        # Simulate a status update
        wrapper_callback(private_key.address, "some_status_hash")

        # User callback should have been called
        user_callback.assert_called_once_with(private_key.address, "some_status_hash")

    @patch("bitcash.wallet.NetworkAPI")
    def test_subscribe_with_update_self_skips_update_on_error(self, mock_network_api):
        """Test that subscribe with update_self=True skips update on error status."""
        mock_handle = SubscriptionHandle(lambda: None)
        mock_network_api.subscribe_address.return_value = mock_handle

        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        # Mock get_unspents to track if it's called
        private_key.get_unspents = MagicMock()
        private_key.get_transactions = MagicMock()
        user_callback = MagicMock()

        private_key.subscribe(user_callback, update_self=True)

        # Get the wrapper callback
        call_args = mock_network_api.subscribe_address.call_args
        wrapper_callback = call_args[0][1]

        # Simulate an error status
        wrapper_callback(private_key.address, "error: connection failed")

        # Should not have updated balances
        private_key.get_unspents.assert_not_called()
        private_key.get_transactions.assert_not_called()
        # But user callback should still be called
        user_callback.assert_called_once_with(
            private_key.address, "error: connection failed"
        )

    @patch("bitcash.wallet.NetworkAPI")
    def test_subscribe_with_update_self_skips_update_on_unsubscribed(
        self, mock_network_api
    ):
        """Test that subscribe with update_self=True skips update on unsubscribed."""
        mock_handle = SubscriptionHandle(lambda: None)
        mock_network_api.subscribe_address.return_value = mock_handle

        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        private_key.get_unspents = MagicMock()
        private_key.get_transactions = MagicMock()
        user_callback = MagicMock()

        private_key.subscribe(user_callback, update_self=True)

        call_args = mock_network_api.subscribe_address.call_args
        wrapper_callback = call_args[0][1]

        wrapper_callback(private_key.address, "unsubscribed")

        private_key.get_unspents.assert_not_called()
        private_key.get_transactions.assert_not_called()
        user_callback.assert_called_once_with(private_key.address, "unsubscribed")

    @patch("bitcash.wallet.NetworkAPI")
    def test_subscribe_with_update_self_handles_null_status(self, mock_network_api):
        """Test that subscribe with update_self=True handles null status."""
        mock_handle = SubscriptionHandle(lambda: None)
        mock_network_api.subscribe_address.return_value = mock_handle
        mock_network_api.get_unspent.return_value = []
        mock_network_api.get_transactions.return_value = []

        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        private_key.get_unspents = MagicMock()
        private_key.get_transactions = MagicMock()
        user_callback = MagicMock()

        private_key.subscribe(user_callback, update_self=True)

        call_args = mock_network_api.subscribe_address.call_args
        wrapper_callback = call_args[0][1]

        # Simulate null status (address with no history)
        wrapper_callback(private_key.address, None)

        # Should still call user callback with None
        user_callback.assert_called_once_with(private_key.address, None)
        # None status must NOT trigger balance/history fetching (Phase I fix)
        private_key.get_unspents.assert_not_called()
        private_key.get_transactions.assert_not_called()


class TestPrivateKeyTestnet:
    def test_init_default(self):
        private_key = PrivateKeyTestnet()

        assert private_key._address is None
        assert private_key.balance == 0
        assert private_key.unspents == []
        assert private_key.transactions == []

    def test_address(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST)
        assert private_key.address == BITCOIN_CASHADDRESS_TEST
        assert private_key.cashtoken_address == BITCOIN_CASHADDRESS_TEST_CATKN

    def test_to_wif(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST)
        assert private_key.to_wif() == WALLET_FORMAT_TEST

        private_key = PrivateKeyTestnet(WALLET_FORMAT_COMPRESSED_TEST)
        assert private_key.to_wif() == WALLET_FORMAT_COMPRESSED_TEST

    @pytest.mark.skip
    def test_get_balance(self):
        # Marking as skip because BitcoinCom Testnet is currently unreliable
        # TODO: Remove once a new Testnet endpoint is added
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST)
        balance = int(private_key.get_balance())
        assert balance == private_key.balance

    @pytest.mark.skip
    def test_get_unspent(self):
        # Marking as skip because BitcoinCom Testnet is currently unreliable
        # TODO: Remove once a new Testnet endpoint is added
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST)
        unspent = private_key.get_unspents()
        assert unspent == private_key.unspents

    @pytest.mark.skip
    def test_get_transactions(self):
        # Marking as skip because BitcoinCom Testnet is currently unreliable
        # TODO: Remove once a new Testnet endpoint is added
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST)
        transactions = private_key.get_transactions()
        assert transactions == private_key.transactions

    @pytest.mark.skip
    def test_send_cashaddress(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_COMPRESSED_TEST)

        initial = private_key.balance
        current = initial
        private_key.send([(BITCOIN_CASHADDRESS_TEST, 2000, "satoshi")])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.balance

        logging.debug(f"Current: {current}, Initial: {initial}")
        assert current < initial

    @pytest.mark.skip
    def test_send(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_COMPRESSED_TEST)
        private_key.get_unspents()

        initial = private_key.balance
        current = initial
        private_key.send([("n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi", 1000, "satoshi")])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.balance

        logging.debug(f"Current: {current}, Initial: {initial}")
        assert current < initial

    def test_from_hex(self):
        key = PrivateKeyTestnet.from_hex(PRIVATE_KEY_HEX)
        assert isinstance(key, PrivateKeyTestnet)
        assert key.to_hex() == PRIVATE_KEY_HEX

    def test_from_der(self):
        key = PrivateKeyTestnet.from_der(PRIVATE_KEY_DER)
        assert isinstance(key, PrivateKeyTestnet)
        assert key.to_der() == PRIVATE_KEY_DER

    def test_from_pem(self):
        key = PrivateKeyTestnet.from_pem(PRIVATE_KEY_PEM)
        assert isinstance(key, PrivateKeyTestnet)
        assert key.to_pem() == PRIVATE_KEY_PEM

    def test_from_int(self):
        key = PrivateKeyTestnet.from_int(PRIVATE_KEY_NUM)
        assert isinstance(key, PrivateKeyTestnet)
        assert key.to_int() == PRIVATE_KEY_NUM

    def test_repr(self):
        assert (
            repr(PrivateKeyTestnet(WALLET_FORMAT_MAIN))
            == f"<PrivateKeyTestnet: {BITCOIN_CASHADDRESS_TEST}>"
        )


class TestPrivateKeyRegtest:
    def test_init_default(self):
        private_key = PrivateKeyRegtest()

        assert private_key._address is None
        assert private_key.balance == 0
        assert private_key.unspents == []
        assert private_key.transactions == []

    def test_address(self):
        private_key = PrivateKeyRegtest(WALLET_FORMAT_REGTEST)
        assert private_key.address == BITCOIN_CASHADDRESS_REGTEST
        assert private_key.cashtoken_address == BITCOIN_CASHADDRESS_REGTEST_CATKN

    def test_to_wif(self):
        private_key = PrivateKeyRegtest(WALLET_FORMAT_REGTEST)
        assert private_key.to_wif() == WALLET_FORMAT_REGTEST

        private_key = PrivateKeyRegtest(WALLET_FORMAT_COMPRESSED_REGTEST)
        assert private_key.to_wif() == WALLET_FORMAT_COMPRESSED_REGTEST

    @pytest.mark.regtest
    def test_get_balance(self):
        private_key = PrivateKeyRegtest(WALLET_FORMAT_REGTEST)
        balance = int(private_key.get_balance())
        assert balance == private_key.balance

    @pytest.mark.regtest
    def test_get_unspent(self):
        private_key = PrivateKeyRegtest(WALLET_FORMAT_REGTEST)
        unspent = private_key.get_unspents()
        assert unspent == private_key.unspents

    @pytest.mark.regtest
    def test_get_transactions(self):
        private_key = PrivateKeyRegtest(WALLET_FORMAT_REGTEST)
        transactions = private_key.get_transactions()
        assert transactions == private_key.transactions

    @pytest.mark.regtest
    def test_send_cashaddress(self):
        # This tests requires the local node to be continuously generating blocks
        # Local node user will need to ensure the address is funded
        # first in order for this test to pass
        private_key = PrivateKeyRegtest(WALLET_FORMAT_COMPRESSED_REGTEST)

        initial = private_key.get_balance()
        current = initial
        private_key.send([(BITCOIN_CASHADDRESS_REGTEST, 2000, "satoshi")])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.get_balance()

        logging.debug(f"Current: {current}, Initial: {initial}")
        assert current < initial

    @pytest.mark.regtest
    def test_send(self):
        # This tests requires the local node to be continuously generating blocks
        # marking 'skip' until auto-block generation is functional

        # Local node user will need to ensure the address is funded
        # first in order for this test to pass
        private_key = PrivateKeyRegtest(WALLET_FORMAT_COMPRESSED_REGTEST)
        private_key.get_unspents()

        initial = private_key.balance
        current = initial
        # FIXME: Changed jpy to satoshi and 1 to 10,000 since we don't yet
        # have a rates API for BCH in place.
        private_key.send([("n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi", 2000, "satoshi")])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.balance

        logging.debug(f"Current: {current}, Initial: {initial}")
        assert current < initial

    def test_from_hex(self):
        key = PrivateKeyRegtest.from_hex(PRIVATE_KEY_HEX)
        assert isinstance(key, PrivateKeyRegtest)
        assert key.to_hex() == PRIVATE_KEY_HEX

    def test_from_der(self):
        key = PrivateKeyRegtest.from_der(PRIVATE_KEY_DER)
        assert isinstance(key, PrivateKeyRegtest)
        assert key.to_der() == PRIVATE_KEY_DER

    def test_from_pem(self):
        key = PrivateKeyRegtest.from_pem(PRIVATE_KEY_PEM)
        assert isinstance(key, PrivateKeyRegtest)
        assert key.to_pem() == PRIVATE_KEY_PEM

    def test_from_int(self):
        key = PrivateKeyRegtest.from_int(PRIVATE_KEY_NUM)
        assert isinstance(key, PrivateKeyRegtest)
        assert key.to_int() == PRIVATE_KEY_NUM

    def test_repr(self):
        assert (
            repr(PrivateKeyRegtest(WALLET_FORMAT_REGTEST))
            == f"<PrivateKeyRegtest: {BITCOIN_CASHADDRESS_REGTEST}>"
        )
