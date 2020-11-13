import os
import time
import logging

import pytest

from bitcash.crypto import ECPrivateKey
from bitcash.curve import Point
from bitcash.format import verify_sig
from bitcash.wallet import (
    BaseKey, Key, PrivateKey, PrivateKeyTestnet, PrivateKeyRegtest, wif_to_key
)
from bitcash.exceptions import InvalidAddress
from .samples import (
    PRIVATE_KEY_BYTES, PRIVATE_KEY_DER,
    PRIVATE_KEY_HEX, PRIVATE_KEY_NUM, PRIVATE_KEY_PEM,
    PUBLIC_KEY_COMPRESSED, PUBLIC_KEY_UNCOMPRESSED, PUBLIC_KEY_X,
    PUBLIC_KEY_Y, WALLET_FORMAT_COMPRESSED_MAIN, WALLET_FORMAT_COMPRESSED_TEST,
    WALLET_FORMAT_COMPRESSED_REGTEST, WALLET_FORMAT_MAIN,
    WALLET_FORMAT_TEST, WALLET_FORMAT_REGTEST,
    BITCOIN_CASHADDRESS, BITCOIN_CASHADDRESS_TEST, BITCOIN_CASHADDRESS_REGTEST,
    BITCOIN_ADDRESS_TEST_PAY2SH
)

TRAVIS = 'TRAVIS' in os.environ


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
            BaseKey(b'\x00')

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
        assert BaseKey(WALLET_FORMAT_COMPRESSED_MAIN) == BaseKey(WALLET_FORMAT_COMPRESSED_MAIN)


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

    def test_to_wif(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        assert private_key.to_wif() == WALLET_FORMAT_MAIN

        private_key = PrivateKey(WALLET_FORMAT_COMPRESSED_MAIN)
        assert private_key.to_wif() == WALLET_FORMAT_COMPRESSED_MAIN

    def test_get_balance(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        balance = int(private_key.get_balance())
        assert balance == private_key.balance

    def test_get_unspent(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        unspent = private_key.get_unspents()
        assert unspent == private_key.unspents

    def test_get_transactions(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
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
        assert repr(PrivateKey(WALLET_FORMAT_MAIN)) == '<PrivateKey: bitcoincash:qzfyvx77v2pmgc0vulwlfkl3uzjgh5gnmqk5hhyaa6>'


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

    def test_to_wif(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST)
        assert private_key.to_wif() == WALLET_FORMAT_TEST

        private_key = PrivateKeyTestnet(WALLET_FORMAT_COMPRESSED_TEST)
        assert private_key.to_wif() == WALLET_FORMAT_COMPRESSED_TEST

    def test_get_balance(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST)
        balance = int(private_key.get_balance())
        assert balance == private_key.balance

    def test_get_unspent(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST)
        unspent = private_key.get_unspents()
        assert unspent == private_key.unspents

    def test_get_transactions(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST)
        transactions = private_key.get_transactions()
        assert transactions == private_key.transactions

    @pytest.mark.skip
    def test_send_cashaddress(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_COMPRESSED_TEST)

        initial = private_key.get_balance()
        current = initial
        private_key.send([(BITCOIN_CASHADDRESS_TEST, 2000, 'satoshi')])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.get_balance()

        logging.debug('Current: {}, Initial: {}'.format(current, initial))
        assert current < initial

    @pytest.mark.skip
    def test_send(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_COMPRESSED_TEST)
        private_key.get_unspents()

        initial = private_key.balance
        current = initial
        private_key.send([('n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi', 1000, 'satoshi')])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.get_balance()

        logging.debug('Current: {}, Initial: {}'.format(current, initial))
        assert current < initial

    def test_send_pay2sh(self):
        """
        We don't yet support pay2sh, so we must throw an exception if we get one.
        Otherwise, we could send coins into an unrecoverable blackhole, needlessly.
        pay2sh addresses begin with 2 in testnet and 3 on mainnet.
        """

        private_key = PrivateKeyTestnet(WALLET_FORMAT_COMPRESSED_TEST)
        private_key.get_unspents()

        with pytest.raises(InvalidAddress):
            private_key.send([(BITCOIN_ADDRESS_TEST_PAY2SH, 1, 'mbch')])

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
        assert repr(PrivateKeyTestnet(WALLET_FORMAT_MAIN)) == '<PrivateKeyTestnet: bchtest:qzfyvx77v2pmgc0vulwlfkl3uzjgh5gnmqjxnsx26x>'


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
        private_key.send([(BITCOIN_CASHADDRESS_REGTEST, 2000, 'satoshi')])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.get_balance()

        logging.debug('Current: {}, Initial: {}'.format(current, initial))
        assert current < initial

    @pytest.mark.regtest
    def test_send(self):
        # This tests requires the local node to be continuously generating blocks
        # Local node user will need to ensure the address is funded
        # first in order for this test to pass
        private_key = PrivateKeyRegtest(WALLET_FORMAT_COMPRESSED_REGTEST)
        private_key.get_unspents()

        initial = private_key.balance
        current = initial
        # FIXME: Changed jpy to satoshi and 1 to 10,000 since we don't yet
        # have a rates API for BCH in place.
        private_key.send([('n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi', 2000, 'satoshi')])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.get_balance()

        logging.debug('Current: {}, Initial: {}'.format(current, initial))
        assert current < initial

    @pytest.mark.regtest
    def test_send_pay2sh(self):
        """
        This tests requires the local node to be continuously generating blocks
        Local node user will need to ensure the address is funded
        first in order for this test to pass
        We don't yet support pay2sh, so we must throw an exception if we get one.
        Otherwise, we could send coins into an unrecoverable blackhole, needlessly.
        pay2sh addresses begin with 2 in testnet and 3 on mainnet.
        """

        private_key = PrivateKeyRegtest(WALLET_FORMAT_COMPRESSED_REGTEST)
        private_key.get_unspents()

        with pytest.raises(InvalidAddress):
            private_key.send([('2NFKbBHzzh32q5DcZJNgZE9sF7gYmtPbawk', 1, 'mbch')])

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
        assert repr(PrivateKeyRegtest(WALLET_FORMAT_REGTEST)) == '<PrivateKeyRegtest: bchreg:qzfyvx77v2pmgc0vulwlfkl3uzjgh5gnmqg6939eeq>'