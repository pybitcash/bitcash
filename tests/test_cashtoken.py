import pytest


from bitcash import cashtoken as _cashtoken
from bitcash.network.meta import Unspent
from bitcash.cashtoken import (
    CashTokenOutput,
    InvalidCashToken,
    prepare_cashtoken_aware_output,
    CashToken
)
from bitcash.exceptions import InsufficientFunds
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


class TestCashTokenOutput:
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
            " nft_capability='immutable', token_amount=50, amount=0)"
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
                                    CASHTOKEN_AMOUNT, 2000000000)
        script = (cashtoken.token_prefix
                  + Address.from_string(BITCOIN_CASHADDRESS).scriptcode)
        assert output[0] == script
        assert output[1] == 2000000000
        assert output[2] == cashtoken


class TestCashToken:
    def setup_method(self):
        self.monkeypatch = MonkeyPatch()
        self.monkeypatch.setattr(_cashtoken, "NetworkAPI", NetworkAPI)

    def test_empty(self):
        unspents = [Unspent(1000, 42, "script", "txid", 0)]
        cashtoken = CashToken.from_unspents(unspents)
        assert cashtoken.tokendata == {}
        assert cashtoken.amount == 1000

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
        cashtoken = CashToken.from_unspents(unspents)
        assert tokendata == cashtoken.tokendata
        assert cashtoken.amount == 3000

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
        cashtoken = CashToken.from_unspents(unspents)
        assert tokendata == cashtoken.tokendata
        assert cashtoken.amount == 3000

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
        cashtoken = CashToken.from_unspents(unspents)
        assert tokendata == cashtoken.tokendata
        assert cashtoken.amount == 5000

    def test_subtract(self):
        tokendata = {
            "catagory1": {"nft": [
                {"capability": "mutable"},
                {"capability": "immutable", "commitment": b"commitment"}
            ]},
            "catagory2": {
                "token_amount": 50,
                "nft": [{"capability": "minting"}, {"capability": "minting"}]
            },
            "catagory3": {"token_amount": 50},
            "catagory4": {"nft": [{"capability": "immutable"}]}
        }

        # No token
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0)
        )
        assert cashtoken.amount == 500
        assert cashtoken.tokendata == tokendata

        # New token
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, None, "mutable")
        )
        assert cashtoken.amount == 500
        assert cashtoken.tokendata == tokendata

        # raise errors
        cashtoken = CashToken(1000, tokendata)
        # catagory does not exist
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                Unspent(500, 42, "script", "txid", 0, "catagory0", "mutable")
            )
        # bad token amount
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                Unspent(500, 42, "script", "txid", 0, "catagory1",
                        token_amount=50)
            )
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                Unspent(500, 42, "script", "txid", 0, "catagory2",
                        token_amount=500)
            )
        # bad nft
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                Unspent(500, 42, "script", "txid", 0, "catagory3", "mutable")
            )
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                Unspent(500, 42, "script", "txid", 0, "catagory4",
                        "immutable", b"commitment")
            )
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                Unspent(500, 42, "script", "txid", 0, "catagory4",
                        "mutable", b"commitment")
            )
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                Unspent(500, 42, "script", "txid", 0, "catagory4",
                        "minting", b"commitment")
            )

        # fine tune subtraction
        tokendata = {
            "catagory": {
                "token_amount": 50,
                "nft": [{"capability": "immutable"}]
            }
        }
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    token_amount=50)
        )
        assert cashtoken.tokendata == {"catagory": {"nft": [{
            "capability": "immutable"
        }]}}
        cashtoken.subtract_output(
            Unspent(50, 42, "script", "txid", 0, "catagory",
                    "immutable")
        )
        assert cashtoken.tokendata == {}

        tokendata = {"catagory": {"token_amount": 50}}
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    token_amount=50)
        )
        assert cashtoken.tokendata == {}

        tokendata = {"catagory": {"nft": [
            {"capability": "immutable"},
            {"capability": "immutable", "commitment": b"commitment"}
        ]}}
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    "immutable", b"commitment")
        )
        assert cashtoken.tokendata == {"catagory": {"nft": [{
            "capability": "immutable"
        }]}}

        tokendata = {
            "catagory": {
                "nft": [{"capability": "mutable"}]
            }
        }
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    "immutable", b"commitment")
        )
        assert cashtoken.tokendata == {}

        tokendata = {
            "catagory": {
                "nft": [{"capability": "minting"}]
            }
        }
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    "immutable", b"commitment")
        )
        assert cashtoken.tokendata == tokendata

        tokendata = {
            "catagory": {
                "nft": [{"capability": "mutable"}]
            }
        }
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    "mutable", b"commitment")
        )
        assert cashtoken.tokendata == {}

        tokendata = {
            "catagory": {
                "nft": [{"capability": "minting"}]
            }
        }
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    "mutable", b"commitment")
        )
        assert cashtoken.tokendata == tokendata

        tokendata = {
            "catagory": {
                "nft": [{"capability": "minting"}]
            }
        }
        cashtoken = CashToken(1000, tokendata)
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    "minting", b"commitment")
        )
        assert cashtoken.tokendata == tokendata

    def test_get_outputs(self):
        tokendata = {
            "c1": {"nft": [
                {"capability": "mutable"},
                {"capability": "immutable", "commitment": b"commitment"}
            ]},
            "c2": {
                "token_amount": 50,
                "nft": [{"capability": "minting"}, {"capability": "minting"}]
            },
            "c3": {"token_amount": 50},
            "c4": {"nft": [{"capability": "immutable"}]}
        }

        cashtokenoutput_10 = CashTokenOutput("c1", "mutable", None, None, 512)
        cashtokenoutput_11 = CashTokenOutput("c1", "immutable",
                                             b"commitment", None, 512)
        cashtokenoutput_20 = CashTokenOutput("c2", "minting", None, 50, 512)
        cashtokenoutput_21 = CashTokenOutput("c2", "minting", None, None, 512)
        cashtokenoutput_30 = CashTokenOutput("c3", None, None, 50, 512)
        cashtokenoutput_40 = CashTokenOutput("c4", "immutable", None, None,
                                             512)

        cashtoken = CashToken(3072, tokendata)
        outputs = cashtoken.get_outputs(BITCOIN_CASHADDRESS)

        assert len(outputs) == 6
        assert outputs[0][1] == 512
        assert outputs[0][2] == cashtokenoutput_10
        assert outputs[1][1] == 512
        assert outputs[1][2] == cashtokenoutput_11
        assert outputs[2][1] == 512
        assert outputs[2][2] == cashtokenoutput_20
        assert outputs[3][1] == 512
        assert outputs[3][2] == cashtokenoutput_21
        assert outputs[4][1] == 512
        assert outputs[4][2] == cashtokenoutput_30
        assert outputs[5][1] == 512
        assert outputs[5][2] == cashtokenoutput_40

        cashtoken = CashToken(50)
        outputs = cashtoken.get_outputs(BITCOIN_CASHADDRESS)

        assert len(outputs) == 1
        assert outputs[0][1] == 50
        assert outputs[0][2] == CashTokenOutput()
