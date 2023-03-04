import pytest


from bitcash import cashtoken as _cashtoken
from bitcash.network.meta import Unspent
from bitcash.cashtoken import (
    CashTokenOutput,
    InvalidCashToken,
    prepare_cashtoken_aware_output,
    cashtoken_balance_from_unspents
)
from bitcash.cashaddress import Address
from _pytest.monkeypatch import MonkeyPatch
from .samples import (
    CASHTOKEN_CATAGORY_ID,
    CASHTOKEN_CAPABILITY,
    CASHTOKEN_COMMITMENT,
    CASHTOKEN_AMOUNT,
    PREFIX_CAPABILITY,
    PREFIX_CAPABILITY_AMOUNT,
    PREFIX_CAPABILITY_COMMITMENT,
    PREFIX_CAPABILITY_COMMITMENT_AMOUNT,
    PREFIX_AMOUNT,
    BITCOIN_CASHADDRESS
)


# Monkeypatch NETWORKAPI
class DummyTX:
    def __init__(self, block):
        self.block = block


class NetworkAPI_badheight:
    def get_transaction(catagory_id):
        return DummyTX(0)


class NetworkAPI:
    def get_transaction(catagory_id):
        # tx block height 1e6 much later than cashtoken activation
        return DummyTX(1e6)


class TestCashToken:
    def setup_method(self):
        self.monkeypatch = MonkeyPatch()
        self.monkeypatch.setattr(_cashtoken, "NetworkAPI", NetworkAPI)

    def test_init(self):
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "immutable",
                                    CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)
        assert cashtoken.catagory_id == CASHTOKEN_CATAGORY_ID
        assert cashtoken.nft_commitment == CASHTOKEN_COMMITMENT
        assert cashtoken.nft_capability == "immutable"
        assert cashtoken.token_amount == CASHTOKEN_AMOUNT
        # CashToken properties
        assert cashtoken.has_amount is True
        assert cashtoken.has_nft is True
        assert cashtoken.has_cashtoken is True

        # test bad inputs
        # bad catagory id
        with MonkeyPatch.context() as mct:
            mct.setattr(_cashtoken, "NetworkAPI", NetworkAPI_badheight)
            with pytest.raises(InvalidCashToken):
                CashTokenOutput(CASHTOKEN_CATAGORY_ID, CASHTOKEN_AMOUNT)
        with pytest.raises(InvalidCashToken):
            CashTokenOutput(CASHTOKEN_CATAGORY_ID)
        # bad capability
        with pytest.raises(InvalidCashToken):
            CashTokenOutput(CASHTOKEN_CATAGORY_ID, "bad_capability")
        # bad commitment
        with pytest.raises(InvalidCashToken):
            CashTokenOutput(CASHTOKEN_CATAGORY_ID,
                            nft_commitment=b"no capability")
        with pytest.raises(ValueError):
            CashTokenOutput(CASHTOKEN_CATAGORY_ID, CASHTOKEN_CAPABILITY,
                            "str_commitment")
        with pytest.raises(InvalidCashToken):
            CashTokenOutput(CASHTOKEN_CATAGORY_ID, CASHTOKEN_CAPABILITY,
                            b"bad_length"*40)
        with pytest.raises(InvalidCashToken):
            CashTokenOutput(CASHTOKEN_CATAGORY_ID, CASHTOKEN_CAPABILITY,
                            b"")
        # bad token_amount
        with pytest.raises(InvalidCashToken):
            CashTokenOutput(CASHTOKEN_CATAGORY_ID, token_amount=0)
        with pytest.raises(InvalidCashToken):
            CashTokenOutput(CASHTOKEN_CATAGORY_ID,
                            token_amount=9223372036854775808)

    def test_prefix_script(self):
        script = PREFIX_CAPABILITY
        cashtoken = CashTokenOutput.from_script(script)
        assert script == cashtoken.token_prefix

        script = PREFIX_CAPABILITY_AMOUNT
        cashtoken = CashTokenOutput.from_script(script)
        assert script == cashtoken.token_prefix

        script = PREFIX_CAPABILITY_COMMITMENT
        cashtoken = CashTokenOutput.from_script(script)
        assert script == cashtoken.token_prefix

        script = PREFIX_CAPABILITY_COMMITMENT_AMOUNT
        cashtoken = CashTokenOutput.from_script(script)
        assert script == cashtoken.token_prefix

        script = PREFIX_AMOUNT
        cashtoken = CashTokenOutput.from_script(script)
        assert script == cashtoken.token_prefix

        script = b""
        cashtoken = CashTokenOutput.from_script(script)
        assert script == cashtoken.token_prefix

    def test_dict_conversion(self):
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "immutable",
                                    CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)

        assert cashtoken == CashTokenOutput.from_dict(cashtoken.to_dict())

    def test_equality(self):
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "immutable",
                                    CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)
        cashtoken1 = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "immutable",
                                     CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)
        cashtoken2 = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "immutable",
                                     CASHTOKEN_COMMITMENT, 51)
        assert cashtoken == cashtoken1
        assert cashtoken != cashtoken2

    def test_repr(self):
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "immutable",
                                    CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)

        assert repr(cashtoken) == (
            "CashToken(catagory_id='b770119192864ac47ac7753df4f31c702bdd0d39"
            "cc3858594eae2a562e0bb100', nft_commitment=b'commitment',"
            " nft_capability='immutable', token_amount=50)"
        )


class TestPrepareCashtokenAwareOutput:
    def setup_method(self):
        self.monkeypatch = MonkeyPatch()
        self.monkeypatch.setattr(_cashtoken, "NetworkAPI", NetworkAPI)

    def test_output(self):
        output = (BITCOIN_CASHADDRESS, 20, "bch")
        output = prepare_cashtoken_aware_output(output)
        assert output[0] == Address.from_string(BITCOIN_CASHADDRESS).scriptcode
        assert output[1] == 2000000000
        assert output[2] == CashTokenOutput()

        output = (BITCOIN_CASHADDRESS, 20, "bch", CASHTOKEN_CATAGORY_ID,
                  CASHTOKEN_CAPABILITY, CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)
        output = prepare_cashtoken_aware_output(output)
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID,
                                    CASHTOKEN_CAPABILITY, CASHTOKEN_COMMITMENT,
                                    CASHTOKEN_AMOUNT)
        script = (cashtoken.token_prefix
                  + Address.from_string(BITCOIN_CASHADDRESS).scriptcode)
        assert output[0] == script
        assert output[1] == 2000000000
        assert output[2] == cashtoken


class TestCashTokenBalanceUnspents:
    def test_empty(self):
        unspents = [Unspent(1000, 42, "script", "txid", 0)]
        assert {} == cashtoken_balance_from_unspents(unspents)

    def test_multi_amounts(self):
        tokendata = {"catagory1": {"token_amount": 50},
                     "catagory2": {"token_amount": 30}}
        unspents = [
            Unspent(1000, 42, "script", "txid", 0, "catagory1",
                    token_amount=25),
            Unspent(1000, 42, "script", "txid", 0, "catagory1",
                    token_amount=25),
            Unspent(1000, 42, "script", "txid", 0, "catagory2",
                    token_amount=30),
        ]
        assert tokendata == cashtoken_balance_from_unspents(unspents)

    def test_multi_nfts(self):
        tokendata = {
            "catagory1": {"nft": [
                {"capability": "mutable"},
                {"capability": "immutable", "commitment": b"commitment"}
            ]},
            "catagory2": {"nft": [{"capability": "minting"}]}
        }
        unspents = [
            Unspent(1000, 42, "script", "txid", 0, "catagory1",
                    nft_capability="mutable"),
            Unspent(1000, 42, "script", "txid", 0, "catagory1",
                    nft_capability="immutable", nft_commitment=b"commitment"),
            Unspent(1000, 42, "script", "txid", 0, "catagory2",
                    nft_capability="minting"),
        ]
        assert tokendata == cashtoken_balance_from_unspents(unspents)

    def test_all(self):
        tokendata = {
            "catagory1": {"nft": [
                {"capability": "mutable"},
                {"capability": "immutable", "commitment": b"commitment"}
            ]},
            "catagory2": {
                "token_amount": 50,
                "nft": [{"capability": "minting"}, {"capability": "minting"}]
            }
        }
        unspents = [
            Unspent(1000, 42, "script", "txid", 0, "catagory1",
                    nft_capability="mutable"),
            Unspent(1000, 42, "script", "txid", 0, "catagory1",
                    nft_capability="immutable", nft_commitment=b"commitment"),
            Unspent(1000, 42, "script", "txid", 0, "catagory2",
                    nft_capability="minting"),
            Unspent(1000, 42, "script", "txid", 0, "catagory2",
                    token_amount=25),
            Unspent(1000, 42, "script", "txid", 0, "catagory2",
                    nft_capability="minting", token_amount=25),
        ]
        assert tokendata == cashtoken_balance_from_unspents(unspents)
