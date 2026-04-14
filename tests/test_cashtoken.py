import json
import pathlib
import typing
import pytest


from bitcash import types as _types
from bitcash.cashaddress import Address
from bitcash.cashtoken import (
    Unspents,
    _calculate_dust_value,
    generate_cashtoken_prefix,
    parse_cashtoken_prefix,
    prepare_output,
    select_cashtoken_utxo,
)
from bitcash.exceptions import InsufficientFunds, InvalidAddress, InvalidCashToken
from bitcash.network.meta import Unspent
from bitcash.types import CashTokens, NFTCapability, PreparedOutput

from .samples import (
    BITCOIN_CASHADDRESS,
    BITCOIN_CASHADDRESS_CATKN,
    CASHTOKEN_AMOUNT,
    CASHTOKEN_CAPABILITY,
    CASHTOKEN_CATAGORY_ID,
    CASHTOKEN_COMMITMENT,
    PREFIX_AMOUNT,
    PREFIX_CAPABILITY,
    PREFIX_CAPABILITY_AMOUNT,
    PREFIX_CAPABILITY_COMMITMENT,
    PREFIX_CAPABILITY_COMMITMENT_AMOUNT,
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


def test_verify_cashtoken_output_data():
    # test bad inputs
    # missing cashtoken fields
    with pytest.raises(InvalidCashToken):
        CashTokens(CASHTOKEN_CATAGORY_ID, None, None, None).verify()
    # bad capability
    with pytest.raises(InvalidCashToken):
        CashTokens(
            CASHTOKEN_CATAGORY_ID,
            typing.cast(NFTCapability, "str capability"),
            None,
            None,
        ).verify()
    # bad commitment
    with pytest.raises(InvalidCashToken):
        CashTokens(CASHTOKEN_CATAGORY_ID, None, b"no capability", None).verify()
    with pytest.raises(InvalidCashToken):
        CashTokens(
            CASHTOKEN_CATAGORY_ID, None, typing.cast(bytes, "str capability"), None
        ).verify()
    with pytest.raises(InvalidCashToken):
        CashTokens(
            CASHTOKEN_CATAGORY_ID,
            NFTCapability[CASHTOKEN_CAPABILITY],
            b"bad_length" * 40,
            None,
        ).verify()
    with pytest.raises(InvalidCashToken):
        CashTokens(
            CASHTOKEN_CATAGORY_ID, NFTCapability[CASHTOKEN_CAPABILITY], b"", None
        ).verify()
    # bad token_amount
    with pytest.raises(InvalidCashToken):
        CashTokens(CASHTOKEN_CATAGORY_ID, None, None, 0).verify()
    with pytest.raises(InvalidCashToken):
        CashTokens(CASHTOKEN_CATAGORY_ID, None, None, 9223372036854775808).verify()


def test_cashtoken_prefix_script(test_vectors, monkeypatch):
    for script in [
        PREFIX_CAPABILITY,
        PREFIX_CAPABILITY_AMOUNT,
        PREFIX_CAPABILITY_COMMITMENT,
        PREFIX_CAPABILITY_COMMITMENT_AMOUNT,
        PREFIX_AMOUNT,
        b"",
    ]:
        cashtoken = parse_cashtoken_prefix(script)
        assert script == generate_cashtoken_prefix(cashtoken)

    # test vectors from https://github.com/bitjson/cashtokens
    # change COMMITMENT_LENGTH
    COMMITMENT_LENGTH = 1500
    monkeypatch.setattr(_types, "COMMITMENT_LENGTH", COMMITMENT_LENGTH)
    for test_vector in test_vectors:
        script = bytes.fromhex(test_vector["prefix"])
        category_id = test_vector["data"]["category"]
        token_amount = int(test_vector["data"]["amount"])
        nft = test_vector["data"].get("nft", None)
        if nft is None:
            nft_capability = None
            nft_commitment = None
        else:
            nft_capability = typing.cast(str, test_vector["data"]["nft"]["capability"])
            nft_commitment = test_vector["data"]["nft"]["commitment"]
            nft_commitment = bytes.fromhex(nft_commitment)
            if nft_commitment == b"":
                nft_commitment = None
        if token_amount == 0:
            token_amount = None
        assert parse_cashtoken_prefix(script) == CashTokens(
            category_id,
            NFTCapability[nft_capability] if nft_capability else None,
            nft_commitment,
            token_amount,
        )


class TestPrepareOutput:
    def test_output(self):
        output = (BITCOIN_CASHADDRESS, 20, "bch")
        output = prepare_output(output)
        script = Address.from_string(BITCOIN_CASHADDRESS_CATKN).scriptcode
        assert output == PreparedOutput(
            script, 2000000000, CashTokens(None, None, None, None)
        )

        cashtoken = CashTokens(
            CASHTOKEN_CATAGORY_ID,
            NFTCapability[CASHTOKEN_CAPABILITY],
            CASHTOKEN_COMMITMENT,
            CASHTOKEN_AMOUNT,
        )
        output = (
            BITCOIN_CASHADDRESS_CATKN,
            20,
            "bch",
            CASHTOKEN_CATAGORY_ID,
            CASHTOKEN_CAPABILITY,
            CASHTOKEN_COMMITMENT,
            CASHTOKEN_AMOUNT,
        )
        prepared_output = prepare_output(output)
        assert prepared_output == PreparedOutput(
            (
                generate_cashtoken_prefix(cashtoken)
                + Address.from_string(BITCOIN_CASHADDRESS_CATKN).scriptcode
            ),
            2000000000,
            cashtoken,
        )

        # bad length
        with pytest.raises(RuntimeError):
            output = prepare_output(typing.cast(tuple[str, int, str], output[1:]))
        # bad prepared out
        with pytest.raises(InvalidAddress):
            output = typing.cast(tuple[str, int, str], ("", *output[1:]))
            output = prepare_output(output)

    def test_token_signal(self):
        output = (BITCOIN_CASHADDRESS, 20, "bch", "341234", "none", None, None)
        with pytest.raises(InvalidAddress):
            prepare_output(output)

    def test_dust_limit(self):
        output = (BITCOIN_CASHADDRESS, 20, "satoshi")
        with pytest.raises(InsufficientFunds):
            prepare_output(output)


class TestUnspents:
    def test_dict(self):
        tokendata = {
            "category1": {
                "nft": [
                    {"capability": "mutable"},
                    {"capability": "none", "commitment": b"commitment"},
                ]
            },
            "category2": {
                "token_amount": 50,
                "nft": [{"capability": "minting"}, {"capability": "minting"}],
            },
            "category3": {"token_amount": 50},
            "category4": {"nft": [{"capability": "none"}]},
        }
        unspent_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        unspents = Unspents.from_dict(unspent_dict)
        assert unspents.to_dict() == unspent_dict

    def test_empty(self):
        unspents = [Unspent(1000, 42, "script", "txid", 0)]
        cashtoken = Unspents(unspents)
        assert cashtoken.tokendata == {}
        assert cashtoken.amount == 1000

    def test_multi_amounts(self):
        tokendata = {
            "category1": {"token_amount": 50},
            "category2": {"token_amount": 30},
        }
        unspents = [
            Unspent(1000, 42, "script", "txid", 0, "category1", token_amount=25),
            Unspent(1000, 42, "script", "txid", 0, "category1", token_amount=25),
            Unspent(1000, 42, "script", "txid", 0, "category2", token_amount=30),
        ]
        cashtoken = Unspents(unspents)
        unspents_dict = cashtoken.to_dict()
        assert tokendata == unspents_dict["tokendata"]
        assert cashtoken.amount == 3000

    def test_multi_nfts(self):
        tokendata = {
            "category1": {
                "nft": [
                    {"capability": "mutable"},
                    {"capability": "none", "commitment": b"commitment"},
                ]
            },
            "category2": {"nft": [{"capability": "minting"}]},
        }
        unspents = [
            Unspent(
                1000, 42, "script", "txid", 0, "category1", nft_capability="mutable"
            ),
            Unspent(
                1000,
                42,
                "script",
                "txid",
                0,
                "category1",
                nft_capability="none",
                nft_commitment=b"commitment",
            ),
            Unspent(
                1000, 42, "script", "txid", 0, "category2", nft_capability="minting"
            ),
        ]
        cashtoken = Unspents(unspents)
        unspents_dict = cashtoken.to_dict()
        assert tokendata == unspents_dict["tokendata"]
        assert cashtoken.amount == 3000

    def test_all(self):
        tokendata = {
            "category1": {
                "nft": [
                    {"capability": "mutable"},
                    {"capability": "none", "commitment": b"commitment"},
                ]
            },
            "category2": {
                "token_amount": 50,
                "nft": [{"capability": "minting"}, {"capability": "minting"}],
            },
        }
        unspents = [
            Unspent(
                1000, 42, "script", "txid", 0, "category1", nft_capability="mutable"
            ),
            Unspent(
                1000,
                42,
                "script",
                "txid",
                0,
                "category1",
                nft_capability="none",
                nft_commitment=b"commitment",
            ),
            Unspent(
                1000, 42, "script", "txid", 0, "category2", nft_capability="minting"
            ),
            Unspent(1000, 42, "script", "txid", 0, "category2", token_amount=25),
            Unspent(
                1000,
                42,
                "script",
                "txid",
                0,
                "category2",
                nft_capability="minting",
                token_amount=25,
            ),
        ]
        cashtoken = Unspents(unspents)
        assert tokendata == cashtoken.to_dict()["tokendata"]
        assert cashtoken.amount == 5000

    def test_subtract(self):
        tokendata: dict = {
            "category1": {
                "nft": [
                    {"capability": "mutable"},
                    {"capability": "none", "commitment": b"commitment"},
                ]
            },
            "category2": {
                "token_amount": 50,
                "nft": [{"capability": "minting"}, {"capability": "minting"}],
            },
            "category3": {"token_amount": 50},
            "category4": {"nft": [{"capability": "none"}]},
        }

        # No token
        unspents_data = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_data)
        cashtoken.subtract_output(
            PreparedOutput(b"", 500, CashTokens(None, None, None, None))
        )
        assert cashtoken.amount == 500
        assert cashtoken.to_dict()["tokendata"] == tokendata

        # New token
        cashtoken = Unspents(
            [
                Unspent(500, 12, "script", "category_new", 0),
                Unspent(500, 12, "script", "txid", 2, "category1", "minting"),
            ]
        )
        cashtoken.subtract_output(
            PreparedOutput(
                b"", 500, CashTokens("category_new", NFTCapability["none"], None, 30)
            )
        )
        assert cashtoken.amount == 500
        assert cashtoken.to_dict()["tokendata"] == {
            "category1": {"nft": [{"capability": "minting"}]}
        }

        # raise errors
        # bad genesis
        with pytest.raises(InsufficientFunds):
            cashtoken = Unspents(
                [
                    Unspent(500, 12, "script", "category_new", 1),
                ]
            )
            cashtoken.subtract_output(
                PreparedOutput(
                    b"",
                    500,
                    CashTokens("category_new", NFTCapability["none"], None, 30),
                )
            )
        unspents_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        # category does not exist
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                PreparedOutput(
                    b"",
                    500,
                    CashTokens("category0", NFTCapability["mutable"], None, None),
                )
            )
        # bad token amount
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                PreparedOutput(b"", 500, CashTokens("category1", None, None, 50))
            )
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                PreparedOutput(b"", 500, CashTokens("category2", None, None, 500))
            )
        # bad nft
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                PreparedOutput(
                    b"",
                    500,
                    CashTokens("category3", NFTCapability["mutable"], None, None),
                )
            )
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                PreparedOutput(
                    b"",
                    500,
                    CashTokens("category4", NFTCapability["none"], b"commitment", None),
                )
            )
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                PreparedOutput(
                    b"",
                    500,
                    CashTokens(
                        "category4", NFTCapability["mutable"], b"commitment", None
                    ),
                )
            )
        with pytest.raises(InsufficientFunds):
            cashtoken.subtract_output(
                PreparedOutput(
                    b"",
                    500,
                    CashTokens(
                        "category4", NFTCapability["minting"], b"commitment", None
                    ),
                )
            )

        # simple subtraction
        cashtoken = Unspents([])
        cashtoken.amount = 500
        cashtoken.subtract_output(
            PreparedOutput(b"", 500, CashTokens(None, None, None, None))
        )
        assert cashtoken.amount == 0

        # fine tune subtraction
        tokendata = {"category": {"token_amount": 50, "nft": [{"capability": "none"}]}}
        unspents_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        cashtoken.subtract_output(
            PreparedOutput(b"", 500, CashTokens("category", None, None, 50))
        )
        assert cashtoken.to_dict()["tokendata"] == {
            "category": {"nft": [{"capability": "none"}]}
        }
        cashtoken.subtract_output(
            PreparedOutput(
                b"", 50, CashTokens("category", NFTCapability["none"], None, None)
            )
        )
        assert cashtoken.tokendata == {}

        tokendata = {"category": {"token_amount": 50}}
        unspents_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        cashtoken.subtract_output(
            PreparedOutput(b"", 500, CashTokens("category", None, None, 50))
        )
        assert cashtoken.tokendata == {}

        tokendata = {
            "category": {
                "nft": [
                    {"capability": "none"},
                    {"capability": "none", "commitment": b"commitment"},
                ]
            }
        }
        unspents_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        cashtoken.subtract_output(
            PreparedOutput(
                b"",
                500,
                CashTokens("category", NFTCapability["none"], b"commitment", None),
            )
        )
        assert cashtoken.to_dict()["tokendata"] == {
            "category": {"nft": [{"capability": "none"}]}
        }

        tokendata = {"category": {"nft": [{"capability": "mutable"}]}}
        unspents_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        cashtoken.subtract_output(
            PreparedOutput(
                b"",
                500,
                CashTokens("category", NFTCapability["none"], b"commitment", None),
            )
        )
        assert cashtoken.tokendata == {}

        tokendata = {"category": {"nft": [{"capability": "minting"}]}}
        unspents_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        cashtoken.subtract_output(
            PreparedOutput(
                b"",
                500,
                CashTokens("category", NFTCapability["none"], b"commitment", None),
            )
        )
        assert cashtoken.to_dict()["tokendata"] == tokendata

        tokendata = {"category": {"nft": [{"capability": "mutable"}]}}
        unspents_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        cashtoken.subtract_output(
            PreparedOutput(
                b"",
                500,
                CashTokens("category", NFTCapability["mutable"], b"commitment", None),
            )
        )
        assert cashtoken.tokendata == {}

        tokendata = {"category": {"nft": [{"capability": "minting"}]}}
        unspents_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        cashtoken.subtract_output(
            PreparedOutput(
                b"",
                500,
                CashTokens("category", NFTCapability["mutable"], b"commitment", None),
            )
        )
        assert cashtoken.to_dict()["tokendata"] == tokendata

        tokendata = {"category": {"nft": [{"capability": "minting"}]}}
        unspents_dict = {
            "amount": 1000,
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        cashtoken.subtract_output(
            PreparedOutput(
                b"",
                500,
                CashTokens("category", NFTCapability["minting"], b"commitment", None),
            )
        )
        assert cashtoken.to_dict()["tokendata"] == tokendata

    def test_get_outputs(self):
        tokendata = {
            "c1": {
                "nft": [
                    {"capability": "mutable"},
                    {"capability": "none", "commitment": b"commitment"},
                ]
            },
            "c2": {
                "token_amount": 50,
                "nft": [{"capability": "minting"}, {"capability": "minting"}],
            },
            "c3": {"token_amount": 50},
            "c4": {"nft": [{"capability": "none"}]},
        }

        cashtokenoutput = []
        cashtokenoutput.append(
            (546, CashTokens("c1", NFTCapability.mutable, None, None))
        )
        cashtokenoutput.append(
            (546, CashTokens("c1", NFTCapability.none, b"commitment", None))
        )
        cashtokenoutput.append((546, CashTokens("c2", NFTCapability.minting, None, 50)))
        cashtokenoutput.append(
            (546, CashTokens("c2", NFTCapability.minting, None, None))
        )
        cashtokenoutput.append((546, CashTokens("c3", None, None, 50)))
        cashtokenoutput.append((546, CashTokens("c4", NFTCapability.none, None, None)))
        for i in range(6):
            dust = _calculate_dust_value(
                Address.from_string(BITCOIN_CASHADDRESS_CATKN), *cashtokenoutput[i][1:]
            )
            _ = list(cashtokenoutput[i])
            _[0] = dust
            cashtokenoutput[i] = tuple(_)

        unspents_dict = {
            "amount": sum([_[0] for _ in cashtokenoutput]),
            "tokendata": tokendata,
        }
        cashtoken = Unspents.from_dict(unspents_dict)
        outputs, leftover_amount = cashtoken.get_outputs(
            Address.from_string(BITCOIN_CASHADDRESS_CATKN)
        )

        assert len(outputs) == 6
        assert outputs[0][1:] == cashtokenoutput[0]
        assert outputs[1][1:] == cashtokenoutput[1]
        assert outputs[2][1:] == cashtokenoutput[2]
        assert outputs[3][1:] == cashtokenoutput[3]
        assert outputs[4][1:] == cashtokenoutput[4]
        assert outputs[5][1:] == cashtokenoutput[5]
        assert leftover_amount == 0

        cashtoken = Unspents([])
        cashtoken.amount = 546
        outputs, leftover_amount = cashtoken.get_outputs(
            Address.from_string(BITCOIN_CASHADDRESS_CATKN)
        )

        assert len(outputs) == 1
        assert outputs[0][1:] == (546, CashTokens(None, None, None, None))
        assert leftover_amount == 546


def test_select_cashtoken_utxo():
    unspent1 = Unspent(50, 1234, "script", "txid", 1, "c1", "minting")
    unspent2 = Unspent(50, 1234, "script", "txid", 1, "c1", "none")
    unspent3 = Unspent(50, 1234, "script", "txid", 1, "c1", "mutable")
    unspent4 = Unspent(50, 1234, "script", "c2", 1)
    unspent41 = Unspent(50, 1234, "script", "c2", 0)  # genesis
    unspent5 = Unspent(50, 1234, "script", "txid", 1, "c2", "mutable")
    unspent6 = Unspent(50, 1234, "script", "txid", 1, "c1", "none", b"commitment")
    unspent7 = Unspent(50, 1234, "script", "txid", 1, "c1", None, None, 10)
    unspent8 = Unspent(50, 1234, "script", "txid", 1, "c1", "mutable", None, 10)
    unspent9 = Unspent(50, 1234, "script", "txid", 1, "c1", None, None, 60)

    output1 = PreparedOutput(
        b"", 512, CashTokens("c1", NFTCapability["mutable"], None, None)
    )
    output2 = PreparedOutput(
        b"", 512, CashTokens("c1", NFTCapability["none"], b"commitment", None)
    )
    output3 = PreparedOutput(
        b"", 512, CashTokens("c2", NFTCapability["minting"], None, 50)
    )
    output4 = PreparedOutput(b"", 512, CashTokens("c2", None, None, 50))
    output5 = PreparedOutput(b"", 512, CashTokens("c1", None, None, 50))
    outputs = [output1, output2, output3, output4]

    # unused unspents
    # no immutable commitment
    unspents, unspents_used = select_cashtoken_utxo([unspent2], outputs)
    assert len(unspents) == 1 and len(unspents_used) == 0
    # no tokens in nft
    unspents, unspents_used = select_cashtoken_utxo(
        [Unspent(50, 1234, "script", "txid", 1, "c1", token_amount=1)], outputs
    )
    assert len(unspents) == 1 and len(unspents_used) == 0
    # no nft in token amount
    unspents, unspents_used = select_cashtoken_utxo(
        [Unspent(50, 1234, "script", "txid", 1, "c1", "minting")], [output5]
    )
    assert len(unspents) == 1 and len(unspents_used) == 0
    # no nft
    unspents, unspents_used = select_cashtoken_utxo([unspent5], outputs)
    assert len(unspents) == 1 and len(unspents_used) == 0
    # no genesis
    unspents, unspents_used = select_cashtoken_utxo([unspent4], outputs)
    assert len(unspents) == 1 and len(unspents_used) == 0

    # test minting
    unspents, unspents_used = select_cashtoken_utxo([unspent1], outputs)
    assert unspents == [] and unspents_used == [unspent1]
    unspents, unspents_used = select_cashtoken_utxo([unspent1], [output2])
    assert unspents == [] and unspents_used == [unspent1]

    # test mutable
    unspents, unspents_used = select_cashtoken_utxo([unspent1, unspent3], [output1])
    assert unspents == [unspent1] and unspents_used == [unspent3]
    unspents, unspents_used = select_cashtoken_utxo([unspent1, unspent3], [output2])
    assert unspents == [unspent1] and unspents_used == [unspent3]

    # test immutable
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1, unspent2, unspent3], [output2]
    )
    assert unspents == [unspent2, unspent1] and unspents_used == [unspent3]
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1, unspent2, unspent3], [output2]
    )
    assert unspents == [unspent2, unspent1] and unspents_used == [unspent3]
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent1, unspent6, unspent3], [output2]
    )
    assert unspents == [unspent3, unspent1] and unspents_used == [unspent6]

    # test genesis
    unspents, unspents_used = select_cashtoken_utxo([unspent41], outputs)
    assert unspents == [] and unspents_used == [unspent41]

    # test token amount
    # under funded
    unspents, unspents_used = select_cashtoken_utxo([unspent7], [output5])
    assert unspents == [] and unspents_used == [unspent7]
    # over funded
    unspents, unspents_used = select_cashtoken_utxo([unspent7, unspent9], [output5])
    assert unspents == [] and unspents_used == [unspent7, unspent9]
    # over funded
    unspents, unspents_used = select_cashtoken_utxo([unspent8, unspent9], [output5])
    # unspent8 has an nft too, sorted last
    assert unspents == [unspent8] and unspents_used == [unspent9]
    # over over funded
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent9, unspent8, unspent7], [output5]
    )
    # unspent8 has an nft too, sorted last
    # unspent7 is considered first due to sorting mechanism, hence both are
    # spent
    assert unspents == [unspent8] and unspents_used == [unspent7, unspent9]
    # over over over funded
    unspents, unspents_used = select_cashtoken_utxo(
        [unspent9, unspent8, unspent7],
        [PreparedOutput(b"", 512, CashTokens("c1", None, None, 75))],
    )
    assert unspents == [] and unspents_used == [unspent7, unspent9, unspent8]


def test_calculate_dust_value():
    for script in [
        PREFIX_CAPABILITY,
        PREFIX_CAPABILITY_AMOUNT,
        PREFIX_CAPABILITY_COMMITMENT,
        PREFIX_CAPABILITY_COMMITMENT_AMOUNT,
        PREFIX_AMOUNT,
        b"",
    ]:
        cashtoken = parse_cashtoken_prefix(script)
        dust = _calculate_dust_value(
            Address.from_string(BITCOIN_CASHADDRESS_CATKN), cashtoken
        )
        assert dust == 546 + len(script) * 3
