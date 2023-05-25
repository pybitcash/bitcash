import pytest
import json
import pathlib


from _pytest.monkeypatch import MonkeyPatch
from bitcash import cashtoken as _cashtoken
from bitcash.network.meta import Unspent
from bitcash.cashtoken import (
    CashTokenOutput,
    prepare_cashtoken_aware_output,
    CashTokenUnspents,
    select_cashtoken_utxo
)
from bitcash.exceptions import (
    InsufficientFunds,
    InvalidCashToken,
    InvalidAddress
)
from bitcash.cashaddress import Address
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
    BITCOIN_CASHADDRESS,
    BITCOIN_CASHADDRESS_CATKN
)


# read token-prefix-valid.json
# test vectors from https://github.com/bitjson/cashtokens
@pytest.fixture
def test_vectors(request):
    file = pathlib.Path(request.node.fspath.strpath)
    config = file.with_name("token-prefix-valid.json")
    with config.open() as fio:
        data = json.load(fio)
    return data


class TestCashTokenOutput:
    def test_init(self):
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "none",
                                    CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)
        assert cashtoken.catagory_id == CASHTOKEN_CATAGORY_ID
        assert cashtoken.nft_commitment == CASHTOKEN_COMMITMENT
        assert cashtoken.nft_capability == "none"
        assert cashtoken.token_amount == CASHTOKEN_AMOUNT
        # CashToken properties
        assert cashtoken.has_amount is True
        assert cashtoken.has_nft is True
        assert cashtoken.has_cashtoken is True

        # test bad inputs
        # missing cashtoken fields
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

    def test_prefix_script(self, test_vectors):
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

        # test vectors from https://github.com/bitjson/cashtokens
        # change COMMITMENT_LENGTH
        COMMITMENT_LENGTH = 1500
        monkeypatch = MonkeyPatch()
        monkeypatch.setattr(_cashtoken, "COMMITMENT_LENGTH", COMMITMENT_LENGTH)
        for test_vector in test_vectors:
            script = test_vector["prefix"]
            catagory_id = test_vector["data"]["category"]
            token_amount = int(test_vector["data"]["amount"])
            nft = test_vector["data"].get("nft", None)
            if nft is None:
                nft_capability = None
                nft_commitment = None
            else:
                nft_capability = test_vector["data"]["nft"]["capability"]
                nft_commitment = test_vector["data"]["nft"]["commitment"]
                nft_commitment = bytes.fromhex(nft_commitment)
                if nft_commitment == b"":
                    nft_commitment = None
            if token_amount == 0:
                token_amount = None
            cashtoken = CashTokenOutput(catagory_id, nft_capability,
                                        nft_commitment, token_amount)
            assert cashtoken == CashTokenOutput.from_script(script)

    def test_dict_conversion(self):
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "none",
                                    CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)

        assert cashtoken == CashTokenOutput.from_dict(cashtoken.to_dict())

    def test_equality(self):
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "none",
                                    CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)
        cashtoken1 = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "none",
                                     CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)
        cashtoken2 = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "none",
                                     CASHTOKEN_COMMITMENT, 51)
        assert cashtoken == cashtoken1
        assert cashtoken != cashtoken2

    def test_repr(self):
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID, "none",
                                    CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)

        assert repr(cashtoken) == (
            "CashToken(catagory_id='00fb7b8704f843caf33c436e3386a469e1d00"
            "4403c388a8b054282d02034f598', nft_commitment=b'commitment',"
            " nft_capability='none', token_amount=50, amount=0)"
        )


class TestPrepareCashtokenAwareOutput:
    def test_output(self):
        output = (BITCOIN_CASHADDRESS, 20, "bch")
        output = prepare_cashtoken_aware_output(output)
        _ = Address.from_string(BITCOIN_CASHADDRESS_CATKN).scriptcode
        assert output[0] == _
        assert output[1] == 2000000000
        assert output[2] == CashTokenOutput(amount=2000000000)

        output = (BITCOIN_CASHADDRESS_CATKN, 20, "bch", CASHTOKEN_CATAGORY_ID,
                  CASHTOKEN_CAPABILITY, CASHTOKEN_COMMITMENT, CASHTOKEN_AMOUNT)
        output = prepare_cashtoken_aware_output(output)
        cashtoken = CashTokenOutput(CASHTOKEN_CATAGORY_ID,
                                    CASHTOKEN_CAPABILITY, CASHTOKEN_COMMITMENT,
                                    CASHTOKEN_AMOUNT, 2000000000)
        script = (cashtoken.token_prefix
                  + Address.from_string(BITCOIN_CASHADDRESS_CATKN).scriptcode)
        assert output[0] == script
        assert output[1] == 2000000000
        assert output[2] == cashtoken

    def test_token_signal(self):
        output = (BITCOIN_CASHADDRESS, 20, "bch", "catagory_id", "none",
                  None, None)
        with pytest.raises(InvalidAddress):
            prepare_cashtoken_aware_output(output)


class TestCashTokenUnspents:
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
                {"capability": "none", "commitment": b"commitment"}
            ]},
            "catagory2": {"nft": [{"capability": "minting"}]}
        }
        unspents = [
            Unspent(1000, 42, "script", "txid", 0, "catagory1",
                    nft_capability="mutable"),
            Unspent(1000, 42, "script", "txid", 0, "catagory1",
                    nft_capability="none", nft_commitment=b"commitment"),
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
                {"capability": "none", "commitment": b"commitment"}
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
                    nft_capability="none", nft_commitment=b"commitment"),
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
                {"capability": "none", "commitment": b"commitment"}
            ]},
            "catagory2": {
                "token_amount": 50,
                "nft": [{"capability": "minting"}, {"capability": "minting"}]
            },
            "catagory3": {"token_amount": 50},
            "catagory4": {"nft": [{"capability": "none"}]}
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
        cashtoken = CashTokenUnspents([
            Unspent(500, 12, "script", "catagory_new", 0),
            Unspent(500, 12, "script", "txid", 2, "catagory1", "minting")
        ])
        cashtoken.subtract_output(
            CashTokenOutput("catagory_new", "none", token_amount=30,
                            amount=500)
        )
        assert cashtoken.amount == 500
        assert cashtoken.tokendata == {"catagory1": {"nft": [{"capability":
                                                             "minting"}]}}

        # raise errors
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
        # bad genesis
        with pytest.raises(InsufficientFunds):
            cashtoken = CashTokenUnspents([
                Unspent(500, 12, "script", "catagory_new", 1),
            ])
            cashtoken.subtract_output(
                CashTokenOutput("catagory_new", "none", token_amount=30,
                                amount=500)
            )
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
                        "none", b"commitment")
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
                "nft": [{"capability": "none"}]
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
            "capability": "none"
        }]}}
        cashtoken.subtract_output(
            Unspent(50, 42, "script", "txid", 0, "catagory",
                    "none")
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
            {"capability": "none"},
            {"capability": "none", "commitment": b"commitment"}
        ]}}
        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 1000
        cashtoken.tokendata = tokendata
        cashtoken.subtract_output(
            Unspent(500, 42, "script", "txid", 0, "catagory",
                    "none", b"commitment")
        )
        assert cashtoken.tokendata == {"catagory": {"nft": [{
            "capability": "none"
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
                    "none", b"commitment")
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
                    "none", b"commitment")
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
                {"capability": "none", "commitment": b"commitment"}
            ]},
            "c2": {
                "token_amount": 50,
                "nft": [{"capability": "minting"}, {"capability": "minting"}]
            },
            "c3": {"token_amount": 50},
            "c4": {"nft": [{"capability": "none"}]}
        }

        cashtokenoutput_10 = CashTokenOutput("c1", "mutable", None, None, 512)
        cashtokenoutput_11 = CashTokenOutput("c1", "none",
                                             b"commitment", None, 512)
        cashtokenoutput_20 = CashTokenOutput("c2", "minting", None, 50, 512)
        cashtokenoutput_21 = CashTokenOutput("c2", "minting", None, None, 512)
        cashtokenoutput_30 = CashTokenOutput("c3", None, None, 50, 512)
        cashtokenoutput_40 = CashTokenOutput("c4", "none", None, None,
                                             512)

        cashtoken = CashTokenUnspents([])
        cashtoken.amount = 3072
        cashtoken.tokendata = tokendata
        (outputs,
         leftover_amount) = cashtoken.get_outputs(BITCOIN_CASHADDRESS_CATKN)

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
        (outputs,
         leftover_amount) = cashtoken.get_outputs(BITCOIN_CASHADDRESS_CATKN)

        assert len(outputs) == 1
        assert outputs[0][1] == 50
        assert outputs[0][2] == CashTokenOutput(amount=50)
        assert leftover_amount == 50


def test_select_cashtoken_utxo():
    unspent1 = Unspent(50, 1234, "script", "txid", 1, "c1", "minting")
    unspent2 = Unspent(50, 1234, "script", "txid", 1, "c1", "none")
    unspent3 = Unspent(50, 1234, "script", "txid", 1, "c1", "mutable")
    unspent4 = Unspent(50, 1234, "script", "c2", 1)
    unspent41 = Unspent(50, 1234, "script", "c2", 0)  # genesis
    unspent5 = Unspent(50, 1234, "script", "txid", 1, "c2", "mutable")
    unspent6 = Unspent(50, 1234, "script", "txid", 1, "c1", "none",
                       b"commitment")
    unspent7 = Unspent(50, 1234, "script", "txid", 1, "c1", None, None, 10)
    unspent8 = Unspent(50, 1234, "script", "txid", 1, "c1", "mutable", None,
                       10)
    unspent9 = Unspent(50, 1234, "script", "txid", 1, "c1", None, None, 60)

    output1 = (
        BITCOIN_CASHADDRESS_CATKN,
        512,
        CashTokenOutput("c1", "mutable", None, None, 512)
    )
    output2 = (
        BITCOIN_CASHADDRESS_CATKN,
        512,
        CashTokenOutput("c1", "none",
                        b"commitment", None, 512)
    )
    output3 = (
        BITCOIN_CASHADDRESS_CATKN,
        512,
        CashTokenOutput("c2", "minting", None, 50, 512)
    )
    output4 = (
        BITCOIN_CASHADDRESS_CATKN,
        512,
        CashTokenOutput("c2", None, None, 50, 512)
    )
    output5 = (
        BITCOIN_CASHADDRESS_CATKN,
        512,
        CashTokenOutput("c1", None, None, 50, 512)
    )
    outputs = [output1, output2, output3, output4]

    # unused unspents
    # no immutable commitment
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent2],
        outputs
    )
    assert len(unspents) == 1 and len(unspents_used) == 0
    # no tokens in nft
    unspents, unspents_used = select_cashtoken_utxo(
        [Unspent(50, 1234, "script", "txid", 1, "c1", token_amount=1)],
        outputs
    )
    assert len(unspents) == 1 and len(unspents_used) == 0
    # no nft in token amount
    unspents, unspents_used = select_cashtoken_utxo(
        [Unspent(50, 1234, "script", "txid", 1, "c1", "minting")],
        [output5]
    )
    assert len(unspents) == 1 and len(unspents_used) == 0
    # no nft
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent5],
        outputs
    )
    assert len(unspents) == 1 and len(unspents_used) == 0
    # no genesis
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent4],
        outputs
    )
    assert len(unspents) == 1 and len(unspents_used) == 0

    # test minting
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1],
        outputs
    )
    assert unspents == [] and unspents_used == [unspent1]
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1],
        [output2]
    )
    assert unspents == [] and unspents_used == [unspent1]

    # test mutable
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1, unspent3],
        [output1]
    )
    assert unspents == [unspent1] and unspents_used == [unspent3]
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1, unspent3],
        [output2]
    )
    assert unspents == [unspent1] and unspents_used == [unspent3]

    # test immutable
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1, unspent2, unspent3],
        [output2]
    )
    assert unspents == [unspent2, unspent1] and unspents_used == [unspent3]
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1, unspent2, unspent3],
        [output2]
    )
    assert unspents == [unspent2, unspent1] and unspents_used == [unspent3]
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1, unspent6, unspent3],
        [output2]
    )
    assert unspents == [unspent3, unspent1] and unspents_used == [unspent6]

    # test genesis
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent41],
        outputs
    )
    assert unspents == [] and unspents_used == [unspent41]

    # test token amount
    # under funded
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent7],
        [output5]
    )
    assert unspents == [] and unspents_used == [unspent7]
    # over funded
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent7, unspent9],
        [output5]
    )
    assert unspents == [] and unspents_used == [unspent7, unspent9]
    # over funded
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent8, unspent9],
        [output5]
    )
    # unspent8 has an nft too, sorted last
    assert unspents == [unspent8] and unspents_used == [unspent9]
    # over over funded
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent9, unspent8, unspent7],
        [output5]
    )
    # unspent8 has an nft too, sorted last
    # unspent7 is considered first due to sorting mechanism, hence both are
    # spent
    assert unspents == [unspent8] and unspents_used == [unspent7, unspent9]
    # over over over funded
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent9, unspent8, unspent7],
        [(BITCOIN_CASHADDRESS_CATKN, 512,
          CashTokenOutput("c1", None, None, 75, 512))]
    )
    assert unspents == [] and unspents_used == [unspent7, unspent9, unspent8]
