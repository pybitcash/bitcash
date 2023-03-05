import pytest


from bitcash import cashtoken as _cashtoken
from bitcash.network.meta import Unspent
from bitcash.cashtoken import (
    CashTokenOutput,
    CashTokenOutputs,
    InvalidCashToken,
    prepare_cashtoken_aware_output,
    CashTokenUnspents,
    generate_new_cashtoken_output,
    DUST_VALUE
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
            " nft_capability='immutable', token_amount=50, amount=0, "
            "_genesis=False)"
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
        assert output[2] == CashTokenOutput(amount=2000000000)

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


class TestCashTokenUnspents:
    def setup_method(self):
        self.monkeypatch = MonkeyPatch()
        self.monkeypatch.setattr(_cashtoken, "NetworkAPI", NetworkAPI)

    def test_empty(self):
        unspents = [Unspent(1000, 42, "script", "txid", 0)]
        cashtoken = CashTokenUnspents(unspents)
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
        cashtoken = CashTokenUnspents(unspents)
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
        cashtoken = CashTokenUnspents(unspents)
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
        cashtoken = CashTokenUnspents(unspents)
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
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0)
        )
        assert cashtoken.amount == 500
        assert cashtoken.tokendata == tokendata

        # New token
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
        cashtoken.subtract_output(
            CashTokenOutput("catagory_new", "immutable", token_amount=30,
                            amount=500, _genesis=True)
        )
        assert cashtoken.amount == 500
        assert cashtoken.tokendata == tokendata

        # raise errors
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
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

        # simple subtraction
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 500
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0)
        )
        assert cashtoken.amount == 0

        # fine tune subtraction
        tokendata = {
            "catagory": {
                "token_amount": 50,
                "nft": [{"capability": "immutable"}]
            }
        }
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
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
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    token_amount=50)
        )
        assert cashtoken.tokendata == {}

        tokendata = {"catagory": {"nft": [
            {"capability": "immutable"},
            {"capability": "immutable", "commitment": b"commitment"}
        ]}}
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
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
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
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
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
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
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
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
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
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
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
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

        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 3072
        cashtoken.tokendata = tokendata
        outputs, leftover_amount = cashtoken.get_outputs(BITCOIN_CASHADDRESS)

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
        assert leftover_amount == 0

        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 50
        outputs, leftover_amount = cashtoken.get_outputs(BITCOIN_CASHADDRESS)

        assert len(outputs) == 1
        assert outputs[0][1] == 50
        assert outputs[0][2] == CashTokenOutput(amount=50)
        assert leftover_amount == 50


class TestGenerateCashTokenOutput:
    def test_outputs(self):
        unspent = Unspent(500, 2345, "script", "ffdd", 0)
        cashtokenoutput = CashTokenOutput(
            catagory_id=unspent.txid,
            nft_capability="mutable",
            token_amount=50,
            amount=DUST_VALUE,
            _genesis=True
        )
        cashtokenoutput1 = CashTokenOutput(
            catagory_id=unspent.txid,
            token_amount=50,
            amount=DUST_VALUE,
            _genesis=True
        )
        cashtokenoutput2 = CashTokenOutput(
            catagory_id=unspent.txid,
            nft_capability="immutable",
            nft_commitment=b"commitment",
            amount=DUST_VALUE,
            _genesis=True
        )

        outputs = generate_new_cashtoken_output(
            unspent,
            ((BITCOIN_CASHADDRESS, "mutable", None, 50),
             (BITCOIN_CASHADDRESS, None, None, 50),
             (BITCOIN_CASHADDRESS, "immutable", b"commitment", None))
        )

        dest = Address.from_string(BITCOIN_CASHADDRESS)
        assert len(outputs) == 3
        assert outputs[0][0] == cashtokenoutput.token_prefix + dest.scriptcode
        assert outputs[0][1] == DUST_VALUE
        assert outputs[0][2] == cashtokenoutput
        assert outputs[1][2] == cashtokenoutput1
        assert outputs[2][2] == cashtokenoutput2
        # bad utxo
        unspent = Unspent(500, 2345, "script", "txid", 2)
        with pytest.raises(InvalidCashToken):
            generate_new_cashtoken_output(unspent,
                                          (BITCOIN_CASHADDRESS, None, None, 50)
                                          )


class TestCashTokenOutputs:
    def setup_method(self):
        self.monkeypatch = MonkeyPatch()
        self.monkeypatch.setattr(_cashtoken, "NetworkAPI", NetworkAPI)

    def test_add_output(self):
        # OP_RETURN
        cashtokenoutputs = CashTokenOutputs([[BITCOIN_CASHADDRESS, 50, None]])
        assert cashtokenoutputs.tokendata == {}

        # genesis cashtoken
        cashtokenoutputs = CashTokenOutputs([
            [
                BITCOIN_CASHADDRESS,
                50,
                CashTokenOutput(
                    "catagory_id",
                    token_amount=50,
                    amount=50,
                    _genesis=True
                )
            ]
        ])
        assert cashtokenoutputs.tokendata == {}

        # test token amount
        cashtokenoutputs = CashTokenOutputs([
            [
                BITCOIN_CASHADDRESS,
                50,
                CashTokenOutput(
                    "catagory_id",
                    token_amount=50,
                    amount=50
                )
            ]
        ])
        assert cashtokenoutputs.tokendata == {"catagory_id": {
            "token_amount": 50
        }}

        # test nft
        cashtokenoutputs = CashTokenOutputs([
            [
                BITCOIN_CASHADDRESS,
                50,
                CashTokenOutput(
                    "catagory_id",
                    nft_capability="immutable",
                    amount=50
                )
            ]
        ])
        assert cashtokenoutputs.tokendata == {"catagory_id": {
            "nft": [{"capability": "immutable"}]
        }}

        # test both
        cashtokenoutputs = CashTokenOutputs([
            [
                BITCOIN_CASHADDRESS,
                50,
                CashTokenOutput(
                    "catagory_id",
                    nft_capability="immutable",
                    token_amount=500,
                    amount=50
                )
            ]
        ])
        assert cashtokenoutputs.tokendata == {"catagory_id": {
            "token_amount": 500,
            "nft": [{"capability": "immutable"}]
        }}

    def test_subtract_unspent(self):
        cashtokenoutput1 = CashTokenOutput("c1", "mutable", None, None, 512)
        cashtokenoutput2 = CashTokenOutput("c1", "immutable",
                                           b"commitment", None, 512)
        cashtokenoutput3 = CashTokenOutput("c2", "minting", None, 50, 512)
        cashtokenoutput4 = CashTokenOutput("c2", None, None, 50, 512)
        outputs = [
            (BITCOIN_CASHADDRESS, 512, cashtokenoutput1),
            (BITCOIN_CASHADDRESS, 512, cashtokenoutput2),
            (BITCOIN_CASHADDRESS, 512, cashtokenoutput3),
            (BITCOIN_CASHADDRESS, 512, cashtokenoutput4),
        ]

        cashtokenoutputs = CashTokenOutputs(outputs)
        # errors
        with pytest.raises(ValueError):
            cashtokenoutputs.subtract_unspent(
                Unspent(50, 1234, "script", "txid", 0, "c1", "immutable")
            )
        with pytest.raises(ValueError):
            cashtokenoutputs.subtract_unspent(
                Unspent(50, 1234, "script", "txid", 0, "c1", token_amount=1)
            )
        with pytest.raises(ValueError):
            cashtokenoutputs.subtract_unspent(
                Unspent(50, 1234, "script", "txid", 0, "c2", "mutable")
            )
        # test minting
        cashtokenoutputs.subtract_unspent(
            Unspent(50, 1234, "script", "txid", 0, "c1", "minting")
        )
        assert cashtokenoutputs.tokendata == {"c2": {
            "token_amount": 100,
            "nft": [{"capability": "minting"}]
        }}

        # test mutable
        cashtokenoutputs = CashTokenOutputs(outputs)
        cashtokenoutputs.subtract_unspent(
            Unspent(50, 1234, "script", "txid", 0, "c1", "mutable")
        )
        assert cashtokenoutputs.tokendata == {
            "c1": {
                "nft": [{"capability": "immutable",
                         "commitment": b"commitment"}]
            },
            "c2": {
                "token_amount": 100,
                "nft": [{"capability": "minting"}]
            }
        }
        # another mutable will cover immutable
        cashtokenoutputs.subtract_unspent(
            Unspent(50, 1234, "script", "txid", 0, "c1", "mutable")
        )
        assert cashtokenoutputs.tokendata == {
            "c2": {
                "token_amount": 100,
                "nft": [{"capability": "minting"}]
            }
        }
        # another mutable will raise error
        with pytest.raises(ValueError):
            cashtokenoutputs.subtract_unspent(
                Unspent(50, 1234, "script", "txid", 0, "c1", "mutable")
            )

        # test immutable
        cashtokenoutputs = CashTokenOutputs(outputs)
        cashtokenoutputs.subtract_unspent(
            Unspent(50, 1234, "script", "txid", 0, "c1", "immutable",
                    b"commitment")
        )
        assert cashtokenoutputs.tokendata == {
            "c1": {
                "nft": [{"capability": "mutable"}]
            },
            "c2": {
                "token_amount": 100,
                "nft": [{"capability": "minting"}]
            }
        }

        # test amount
        cashtokenoutputs = CashTokenOutputs(outputs)
        cashtokenoutputs.subtract_unspent(
            Unspent(50, 1234, "script", "txid", 0, "c2", token_amount=20)
        )
        assert cashtokenoutputs.tokendata == {
            "c1": {
                "nft": [{"capability": "mutable"},
                        {"capability": "immutable",
                         "commitment": b"commitment"}]
            },
            "c2": {
                "token_amount": 80,
                "nft": [{"capability": "minting"}]
            }
        }
