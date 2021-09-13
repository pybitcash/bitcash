import os
import time
import logging

import pytest
from unittest import mock
import json

from bitcash.crypto import ECPrivateKey
from bitcash.curve import Point
from bitcash.format import verify_sig
from bitcash.network.meta import Unspent
from bitcash.wallet import (
    BaseKey,
    Key,
    PrivateKey,
    PrivateKeyTestnet,
    PrivateKeyRegtest,
    wif_to_key,
)
from bitcash.exceptions import InvalidAddress, InvalidNetwork
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
    BITCOIN_CASHADDRESS_REGTEST,
    BITCOIN_ADDRESS_TEST_PAY2SH,
    BITCOIN_ADDRESS_REGTEST_PAY2SH,
    BITCOIN_SLP_ADDRESS,
    BITCOIN_SLP_ADDRESS_REGTEST,
    BITCOIN_SLP_ADDRESS_TEST,
    WALLET_FORMAT_TEST_SLP,
    TESTNET_TESTCOIN_TOKENID,
    TESTNET_GET_BALANCE_BY_TOKEN_URL,
    TESTNET_GET_BALANCE_BY_TOKEN_RESPONSE,
    SLP_TESTS_ADDRESS_TEST,
    MINT_TEST_TOKEN_DETAILS_TESTNET_URL,
    MINT_TEST_TOKEN_DETAILS_TESTNET_RESPONSE,
    MINT_TEST_BATON_UTXO_TESTNET_URL,
    MINT_TEST_BATON_UTXO_TESTNET_RESPONSE,
    SLP_TESTS_SEND_SLP_URL,
    SLP_TESTS_SEND_SLP_RESPONSE,
    SLP_TESTS_SEND_SLP_TOKEN_DETAILS_URL,
    SLP_TESTS_SEND_SLP_TOKEN_DETAILS_RESPONSE,
    SLP_TESTS_FAN_GROUP_UTXO_URL,
    SLP_TESTS_FAN_GROUP_UTXO_RESPONSE,
    SLP_TESTS_FAN_GROUP_TOKEN_INFO_URL,
    SLP_TESTS_FAN_GROUP_TOKEN_INFO_RESPONSE,
    SLP_TESTS_CHILD_NFT_TOKEN_UTXOS_URL,
    SLP_TESTS_CHILD_NFT_TOKEN_UTXOS_RESPONSE,
    SLP_TESTS_CHILD_NFT_UNCONFIRMED_TYPE_65_INPUTS_URL,
    SLP_TESTS_CHILD_NFT_UNCONFIRMED_TYPE_65_INPUTS_RESPONSE,
    SLP_TESTS_CHILD_NFT_TOKEN_DETAILS_URL,
    SLP_TESTS_CHILD_NFT_TOKEN_DETAILS_RESPONSE,
    SLP_TESTS_CHILD_NFT_NOT_ENOUGH_FANNED_RESPONSE,
    SLP_TESTS_CHILD_NFT_NO_FANNED_RESPONSE,
)

test_child_nft_unspent_a = [
    Unspent(
        amount=199980510,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="76b24444f80a3168ee928df9927b1ddec8eee8a1d091b1aef0954ce926a20040",
        txindex=2,
    )
]
test_child_nft_unspent_b = [
    Unspent(
        amount=199979314,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="c5af38e873c48bac2df107657d5f57821d7f004ceb320478483d17d03c998adf",
        txindex=2,
    )
]
test_child_nft_unspent_c = []

TRAVIS = "TRAVIS" in os.environ

# Hard coded for consistent testing of function returns.
# TODO move to different file
SLP_TESTS_UNSPENTS = [
    Unspent(
        amount=992980,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="c1613a5224fb3dc489817b81ef8c0179e8fcf9d016d00799fc60591ec305001f",
        txindex=2,
    )
]
SLP_TESTS_SLP_UNSPENTS = [
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="c1613a5224fb3dc489817b81ef8c0179e8fcf9d016d00799fc60591ec305001f",
        txindex=1,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ebe4d53b26bdef8ddea7a55609c99cda5aaaa2c2909baefaa2bd295479c740ef",
        txindex=2,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb",
        txindex=1,
    ),
]
SLP_TESTS_BATON_UNSPENTS = [
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="15cd6253c8ac838a4b9f9918fc84b0484a45b661a78ccc597a7653a0fc175d1f",
        txindex=2,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb",
        txindex=2,
    ),
]
SLP_TESTS_SEND_UNSPENTS = [
    Unspent(
        amount=992018,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4",
        txindex=3,
    )
]
SLP_TESTS_SEND_SLP_UNSPENTS = [
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4",
        txindex=1,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ff7febe4abaf15771c9e5f402fdb3508810084d951f896d2470f42f57def07b4",
        txindex=2,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="c1613a5224fb3dc489817b81ef8c0179e8fcf9d016d00799fc60591ec305001f",
        txindex=1,
    ),
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="ebe4d53b26bdef8ddea7a55609c99cda5aaaa2c2909baefaa2bd295479c740ef",
        txindex=2,
    ),
]
SLP_TESTS_SEND_BATONS = [
    Unspent(
        amount=546,
        confirmations=-1,
        script="76a9148a4f72432f31d605b023a64b0cd3fb1b0a4dc61588ac",
        txid="89ef48fb7d0d39be9ad748827f191d6197eba342c044185dad58295f75f8b8eb",
        txindex=2,
    )
]

SLP_TESTS_FAN_GROUP_UNSPENTS = [
    Unspent(
        amount=100000000,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="54f72f9895fd4c5f954f6184e297085d8aae07612a2bcc28bbc2b5b82a0918f4",
        txindex=1,
    ),
    Unspent(
        amount=99998814,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="ee19efbe5058d4f97e87800f8c629945416dfbb5326bcf8880ec64129117ba5d",
        txindex=2,
    ),
]
SLP_TESTS_FAN_GROUP_SLP_UNSPENTS = [
    Unspent(
        amount=546,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="ee19efbe5058d4f97e87800f8c629945416dfbb5326bcf8880ec64129117ba5d",
        txindex=1,
    )
]

SLP_TESTS_CHILD_NFT_GENESIS_UNSPENTS = [
    Unspent(
        amount=199994650,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="78687838d6819993f9f80276c209b1b69d711b8f90c12dd5227c50454889f351",
        txindex=7,
    )
]
SLP_TESTS_CHILD_NFT_GENESIS_SLP_UNSPENTS = [
    Unspent(
        amount=546,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="78687838d6819993f9f80276c209b1b69d711b8f90c12dd5227c50454889f351",
        txindex=1,
    ),
    Unspent(
        amount=546,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="78687838d6819993f9f80276c209b1b69d711b8f90c12dd5227c50454889f351",
        txindex=2,
    ),
    Unspent(
        amount=546,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="78687838d6819993f9f80276c209b1b69d711b8f90c12dd5227c50454889f351",
        txindex=4,
    ),
    Unspent(
        amount=546,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="78687838d6819993f9f80276c209b1b69d711b8f90c12dd5227c50454889f351",
        txindex=3,
    ),
    Unspent(
        amount=546,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="78687838d6819993f9f80276c209b1b69d711b8f90c12dd5227c50454889f351",
        txindex=5,
    ),
    Unspent(
        amount=546,
        confirmations=0,
        script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
        txid="78687838d6819993f9f80276c209b1b69d711b8f90c12dd5227c50454889f351",
        txindex=6,
    ),
]


def mockedAPI(txhex, network):
    # Skip broadcast
    return


def mocked_get_balance(key, i):
    # key.unspents = unspents
    key.unspents = [i]
    return



def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data
    
    case = {
        "mint_test_token_details": MockResponse(json.loads(MINT_TEST_TOKEN_DETAILS_TESTNET_RESPONSE), 200),
        "mint_test_baton_utxo": MockResponse(json.loads(MINT_TEST_BATON_UTXO_TESTNET_RESPONSE), 200),
        "send_slp": MockResponse(json.loads(SLP_TESTS_SEND_SLP_RESPONSE), 200),
        "send_slp_token_details": MockResponse(json.loads(SLP_TESTS_SEND_SLP_TOKEN_DETAILS_RESPONSE), 200),
        "fan_group_utxo": MockResponse(json.loads(SLP_TESTS_FAN_GROUP_UTXO_RESPONSE), 200),
        "fan_group_token_info": MockResponse(json.loads(SLP_TESTS_FAN_GROUP_TOKEN_INFO_RESPONSE), 200),
        "child_nft_token_utxos": MockResponse(json.loads(SLP_TESTS_CHILD_NFT_TOKEN_UTXOS_RESPONSE), 200),
        "child_nft_unconfirmed_inputs": MockResponse(json.loads(SLP_TESTS_CHILD_NFT_UNCONFIRMED_TYPE_65_INPUTS_RESPONSE), 200),
        "child_nft_token_details": MockResponse(json.loads(SLP_TESTS_CHILD_NFT_TOKEN_DETAILS_RESPONSE), 200),
        "nft_fanned": MockResponse(json.loads(SLP_TESTS_CHILD_NFT_TOKEN_UTXOS_RESPONSE), 200),
        "exception": Exception,
        "not_enough_fanned": MockResponse(json.loads(SLP_TESTS_CHILD_NFT_NOT_ENOUGH_FANNED_RESPONSE), 200),
        "no_enough_fanned": MockResponse(json.loads(SLP_TESTS_CHILD_NFT_NO_FANNED_RESPONSE), 200),
        }

    return case.get(kwargs.get("key"))

# def mocked_requests_get(*args, **kwargs):
    # class MockResponse:
    #     def __init__(self, json_data, status_code):
    #         self.json_data = json_data
    #         self.status_code = status_code

    #     def json(self):
    #         return self.json_data

    #     def raise_for_status(self):
    #         return

    # # Mocked call to Testnet get_unspents for consistency
    # if kwargs["url"] == MINT_TEST_TOKEN_DETAILS_TESTNET_URL:
    #     return MockResponse(json.loads(MINT_TEST_TOKEN_DETAILS_TESTNET_RESPONSE), 200)
    # elif kwargs["url"] == MINT_TEST_BATON_UTXO_TESTNET_URL:
    #     return MockResponse(json.loads(MINT_TEST_BATON_UTXO_TESTNET_RESPONSE), 200)
    # elif kwargs["url"] == SLP_TESTS_SEND_SLP_URL:
    #     return MockResponse(json.loads(SLP_TESTS_SEND_SLP_RESPONSE), 200)
    # elif kwargs["url"] == SLP_TESTS_SEND_SLP_TOKEN_DETAILS_URL:
    #     return MockResponse(json.loads(SLP_TESTS_SEND_SLP_TOKEN_DETAILS_RESPONSE), 200)
    # elif kwargs["url"] == SLP_TESTS_FAN_GROUP_UTXO_URL:
    #     return MockResponse(json.loads(SLP_TESTS_FAN_GROUP_UTXO_RESPONSE), 200)
    # elif kwargs["url"] == SLP_TESTS_FAN_GROUP_TOKEN_INFO_URL:
    #     return MockResponse(json.loads(SLP_TESTS_FAN_GROUP_TOKEN_INFO_RESPONSE), 200)
    # elif kwargs["url"] == SLP_TESTS_CHILD_NFT_TOKEN_UTXOS_URL:
    #     return MockResponse(json.loads(SLP_TESTS_CHILD_NFT_TOKEN_UTXOS_RESPONSE), 200)
    # elif kwargs["url"] == SLP_TESTS_CHILD_NFT_UNCONFIRMED_TYPE_65_INPUTS_URL:
    #     return MockResponse(
    #         json.loads(SLP_TESTS_CHILD_NFT_UNCONFIRMED_TYPE_65_INPUTS_RESPONSE), 200
    #     )
    # elif kwargs["url"] == SLP_TESTS_CHILD_NFT_TOKEN_DETAILS_URL:
    #     return MockResponse(json.loads(SLP_TESTS_CHILD_NFT_TOKEN_DETAILS_RESPONSE), 200)

    # return MockResponse(None, 404)


def mocked_requests_get_additional(*args, **kwargs):
    class MockResponse:
        # Need to reuse some API paths with different responses
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            return

    if kwargs["url"] == SLP_TESTS_CHILD_NFT_TOKEN_UTXOS_URL:
        return MockResponse(json.loads(SLP_TESTS_CHILD_NFT_TOKEN_UTXOS_RESPONSE), 200)


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
            BaseKey(b"\x00")

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

    def test_init_network(self):
        private_key = PrivateKey(network="main")
        assert private_key._network == "main"

    def test_init_invalid_network(self):
        with pytest.raises(InvalidNetwork):
            private_key = PrivateKey(network="invalid")

    def test_address(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        assert private_key.address == BITCOIN_CASHADDRESS

    def test_slp_address(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        assert private_key.slp_address == BITCOIN_SLP_ADDRESS

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

    @pytest.mark.skip
    def test_get_slp_balance(self):
        private_key = PrivateKey(WALLET_FORMAT_MAIN)
        slp_balance = private_key.get_slp_balance()
        assert slp_balance == private_key.slp_balance

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
            == "<PrivateKey: bitcoincash:qzfyvx77v2pmgc0vulwlfkl3uzjgh5gnmqk5hhyaa6>"
        )


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

    def test_slp_address(self):
        private_key = PrivateKey(WALLET_FORMAT_TEST)
        assert private_key.slp_address == BITCOIN_SLP_ADDRESS

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

    def test_get_slp_balance(self):
        private_key = PrivateKey(WALLET_FORMAT_TEST_SLP)
        slp_balance = private_key.get_slp_balance()
        assert slp_balance == private_key.slp_balance

    def test_get_slp_balance_token(self):
        private_key = PrivateKey(WALLET_FORMAT_TEST_SLP)
        slp_balance = private_key.get_slp_balance(tokenId="12345")
        assert slp_balance == private_key.slp_balance

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

        initial = private_key.get_balance()
        current = initial
        tries = 0
        private_key.send([(BITCOIN_CASHADDRESS_TEST, 2000, "satoshi")])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.get_balance()

        logging.debug(f"Current: {current}, Initial: {initial}")
        assert current < initial

    @pytest.mark.skip
    def test_send(self):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_COMPRESSED_TEST)
        private_key.get_unspents()

        initial = private_key.balance
        current = initial
        tries = 0
        private_key.send([("n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi", 1000, "satoshi")])

        time.sleep(3)  # give some time to the indexer to update the balance
        current = private_key.get_balance()

        logging.debug(f"Current: {current}, Initial: {initial}")
        assert current < initial

    @mock.patch("bitcash.wallet.NetworkAPI.broadcast_tx", side_effect=mockedAPI)
    @mock.patch("requests.get")
    def test_send_slp(self, mock1, mock2):
        mock1.side_effect = [
            mocked_requests_get(key="send_slp"),
            mocked_requests_get(key="send_slp_token_details"),
        ]
        # Broadcasting is mocked out
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST_SLP)
        private_key.unspents[:] = SLP_TESTS_SEND_UNSPENTS
        private_key.slp_unspents = SLP_TESTS_SEND_SLP_UNSPENTS
        private_key.batons = SLP_TESTS_SEND_BATONS
        txid = private_key.send_slp(
            [(BITCOIN_SLP_ADDRESS_TEST, 1)],
            tokenId=TESTNET_TESTCOIN_TOKENID,
            combine=True,
        )

        assert (
            txid == "65a77c1963ece4a0f2a043d9499f2539d32fd056f681bddbae6e1ffed1ac4086"
        )

    @mock.patch("bitcash.wallet.NetworkAPI.broadcast_tx", side_effect=mockedAPI)
    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_send_slp_no_combine(self, mock1, mock2):
        # Broadcasting is mocked out
        # Not combining results in different txid due to unspents
        mock1.side_effect = [
            mocked_requests_get(key="send_slp"),
            mocked_requests_get(key="send_slp_token_details"),
        ]
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST_SLP)
        private_key.unspents[:] = SLP_TESTS_SEND_UNSPENTS
        private_key.slp_unspents = SLP_TESTS_SEND_SLP_UNSPENTS
        private_key.batons = SLP_TESTS_SEND_BATONS
        txid = private_key.send_slp(
            [(BITCOIN_SLP_ADDRESS_TEST, 1)],
            tokenId=TESTNET_TESTCOIN_TOKENID,
            combine=False,
        )

        assert (
            txid == "ab4fdf333c9ba130cab1acd88d298c03ccf9b312eb9449f5aa8f114f34f2dc54"
        )

    @mock.patch("bitcash.wallet.NetworkAPI.broadcast_tx", side_effect=mockedAPI)
    def test_create_slp(self, mock_get):
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST_SLP)
        private_key.unspents[:] = SLP_TESTS_UNSPENTS
        private_key.slp_unspents[:] = SLP_TESTS_SLP_UNSPENTS

        ticker = "ttt"
        token_name = "test"
        document_url = "www.test.com"
        document_hash = ""
        decimals = 0
        token_quant = 1000

        txid = private_key.create_slp_token(
            ticker, token_name, document_url, document_hash, decimals, token_quant
        )

        assert (
            txid == "faae15d31c71131f65a7b6430c4b7ab5db761a6ce752252974e399ea248b23b3"
        )

    @mock.patch("bitcash.wallet.NetworkAPI.broadcast_tx", side_effect=mockedAPI)
    @mock.patch("requests.get")
    def test_mint_slp(self, mock1, mock2):
        mock1.side_effect = [
            mocked_requests_get(key="mint_test_token_details"),
            mocked_requests_get(key="mint_test_baton_utxo"),
        ]
        private_key = PrivateKeyTestnet(WALLET_FORMAT_TEST_SLP)
        private_key.unspents[:] = SLP_TESTS_UNSPENTS
        private_key.slp_unspents[:] = SLP_TESTS_SLP_UNSPENTS
        private_key.batons[:] = SLP_TESTS_BATON_UNSPENTS

        tokenId = TESTNET_TESTCOIN_TOKENID
        amount = 1000

        txid = private_key.mint_slp(tokenId, amount, keepBaton=True)

        assert (
            txid == "4fd43d88b984aca92d40b1b145a039bdbc99771cdccbdfd02c96ccf52cb58d46"
        )

    @pytest.mark.skip
    def test_send_pay2sh(self):
        # Marking as skip because BitcoinCom Testnet is currently unreliable
        # TODO: Remove once a new Testnet endpoint is added
        """
        We don't yet support pay2sh, so we must throw an exception if we get one.
        Otherwise, we could send coins into an unrecoverable blackhole, needlessly.
        pay2sh addresses begin with 2 in testnet and 3 on mainnet.
        """

        private_key = PrivateKeyTestnet(WALLET_FORMAT_COMPRESSED_TEST)
        private_key.get_unspents()

        with pytest.raises(InvalidAddress):
            private_key.send([(BITCOIN_ADDRESS_TEST_PAY2SH, 1, "mbch")])

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
            == "<PrivateKeyTestnet: bchtest:qzfyvx77v2pmgc0vulwlfkl3uzjgh5gnmqjxnsx26x>"
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
        tries = 0
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
        current = private_key.get_balance()

        logging.debug(f"Current: {current}, Initial: {initial}")
        assert current < initial

    @mock.patch("bitcash.wallet.NetworkAPI.broadcast_tx", side_effect=mockedAPI)
    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_fan_group_nft(
        self,
        mock1,
        mock2,
    ):
        mock1.side_effect = [
            mocked_requests_get(key="fan_group_utxo"),
            mocked_requests_get(key="fan_group_token_info")
        ]
        
        private_key = PrivateKeyRegtest(WALLET_FORMAT_TEST)
        private_key.unspents = SLP_TESTS_FAN_GROUP_UNSPENTS
        private_key.slp_unspents = SLP_TESTS_FAN_GROUP_SLP_UNSPENTS

        tokenId = "ee19efbe5058d4f97e87800f8c629945416dfbb5326bcf8880ec64129117ba5d"

        results = private_key.fan_group_token(tokenId=tokenId, amount=5)

        assert (
            results
            == "bf90bf9533843ce422a61b623190d0e672ba1e40da808c8925bb2c7624cfc269"
        )

    @mock.patch("bitcash.wallet.NetworkAPI.broadcast_tx", side_effect=mockedAPI)
    @mock.patch("requests.get")
    @mock.patch.object(PrivateKey, "get_balance", autospec=True)
    def test_child_nft(self, mock1, mock2, mock3):
        private_key = PrivateKeyRegtest(WALLET_FORMAT_TEST)
        mock1.side_effect = [
            mocked_get_balance(private_key, test_child_nft_unspent_a),
            mocked_get_balance(private_key, test_child_nft_unspent_b),
            mocked_get_balance(private_key, test_child_nft_unspent_c),
        ]
        mock2.side_effect = [
            mocked_requests_get(key="nft_fanned"),
            mocked_requests_get(key="child_nft_unconfirmed_inputs"),
            mocked_requests_get(key="child_nft_token_details")
        ]

        private_key.unspents = [
            Unspent(
                amount=199981706,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=12,
            )
        ]
        private_key.slp_unspents = [
            Unspent(
                amount=546,
                confirmations=2,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="da9f49f9c271e10c9e021b9701df237d38dd2152e52c8e3100b0235cb04eca27",
                txindex=1,
            ),
            Unspent(
                amount=546,
                confirmations=2,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="f607097b4ff2a58a27bb48297838b8b03972ba5ddc53d69fd1c85b3ff1e53057",
                txindex=1,
            ),
            Unspent(
                amount=546,
                confirmations=1,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="096b79ce5c6f3dd566f5ee4c7e312992e1ac9721945a46c799bac2180fe1ba1e",
                txindex=1,
            ),
            Unspent(
                amount=546,
                confirmations=1,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ef20153307834d8cb101e2610e91a53e954e3a1d8d079d583adacb39409da925",
                txindex=1,
            ),
            Unspent(
                amount=546,
                confirmations=1,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="83cc2b563f61d7bfa09628b8a8db6c277ec747b7cf1e271352f9b7ff98a46570",
                txindex=1,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=2,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=5,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=1,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=4,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=10,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=11,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=6,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=9,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=8,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=3,
            ),
            Unspent(
                amount=546,
                confirmations=0,
                script="76a91492461bde6283b461ece7ddf4dbf1e0a48bd113d888ac",
                txid="ba54a43ff51beabfc935a7a8237e0c34e9543339231a79d7f13b4e4d6350345d",
                txindex=7,
            ),
        ]

        results = private_key.create_child_nft(
            "ee19efbe5058d4f97e87800f8c629945416dfbb5326bcf8880ec64129117ba5d", 3
        )

        assert (
            results[0]
            == "dcf86307eda27f6265d19e0cffa29f026839103fb20868edfca68594c7a42c1b"
        )
        assert (
            results[1]
            == "d8b7837429e20bd2f94e221887793a636aa9f8e8ed3b444c525e39cad0cebae0"
        )
        assert (
            results[2]
            == "1d7c9076c30053e665e1768ae1b9795600e825bbb2e87334196f2418b4228ab7"
        )


    @mock.patch("requests.get")
    def test_child_nft_not_enough_fanned(self, mock1):
        mock1.side_effect = [
            mocked_requests_get(key="not_enough_fanned"),
            mocked_requests_get(key="child_nft_unconfirmed_inputs"),
            mocked_requests_get(key="child_nft_token_details"),
        ]
        private_key = PrivateKeyRegtest(WALLET_FORMAT_TEST)

        with pytest.raises(Exception) as exec:
            result = private_key.create_child_nft(
                "ee19efbe5058d4f97e87800f8c629945416dfbb5326bcf8880ec64129117ba5d", 4
            )

            assert exec.value.message == "Not enough fanned group utxos."


    @mock.patch("requests.get")
    def test_child_nft_no_fanned(self, mock1):
        mock1.side_effect = [
            mocked_requests_get(key="no_enough_fanned"),
            mocked_requests_get(key="child_nft_unconfirmed_inputs"),
            mocked_requests_get(key="child_nft_token_details"),
        ]
        private_key = PrivateKeyRegtest(WALLET_FORMAT_TEST)

        with pytest.raises(Exception) as exec:
            result = private_key.create_child_nft(
                "ee19efbe5058d4f97e87800f8c629945416dfbb5326bcf8880ec64129117ba5d", 4
            )

            assert exec.value.message == "There are not any fanned group utxos."

    @pytest.mark.regtest
    def test_send_pay2sh(self):
        # This tests requires the local node to be continuously generating blocks
        # marking 'skip' until auto-block generation is functional

        # Local node user will need to ensure the address is funded
        # first in order for this test to pass

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
            private_key.send([("2NFKbBHzzh32q5DcZJNgZE9sF7gYmtPbawk", 1, "mbch")])

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
            == "<PrivateKeyRegtest: bchreg:qzfyvx77v2pmgc0vulwlfkl3uzjgh5gnmqg6939eeq>"
        )
