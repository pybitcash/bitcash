import pytest
import json
import pathlib

from bitcash.network.meta import Unspent
from ..samples import (
    CASHTOKEN_CATAGORY_ID,
    CASHTOKEN_CAPABILITY,
    CASHTOKEN_COMMITMENT,
    CASHTOKEN_AMOUNT,
    PREFIX_CAPABILITY,
    PREFIX_CAPABILITY_AMOUNT,
    PREFIX_CAPABILITY_COMMITMENT,
    PREFIX_CAPABILITY_COMMITMENT_AMOUNT,
    PREFIX_AMOUNT,
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


class TestUnspent:
    def test_init(self):
        unspent = Unspent(10000, 7, "script", "txid", 0, "catagory_id",
                          "none", "nft_commitment", 50)
        assert unspent.amount == 10000
        assert unspent.confirmations == 7
        assert unspent.script == "script"
        assert unspent.txid == "txid"
        assert unspent.txindex == 0
        assert unspent.catagory_id == "catagory_id"
        assert unspent.nft_commitment == "nft_commitment"
        assert unspent.nft_capability == "none"
        assert unspent.token_amount == 50
        # CashToken properties
        assert unspent.has_amount is True
        assert unspent.has_nft is True
        assert unspent.has_cashtoken is True

    def test_parse_script(self, test_vectors):
        script = PREFIX_CAPABILITY.hex()
        unspent = Unspent(10000, 7, script, "txid", 0, CASHTOKEN_CATAGORY_ID,
                          nft_capability=CASHTOKEN_CAPABILITY)
        assert unspent == Unspent(10000, 7, script, "txid", 0)

        script = PREFIX_CAPABILITY_AMOUNT.hex()
        unspent = Unspent(10000, 7, script, "txid", 0, CASHTOKEN_CATAGORY_ID,
                          nft_capability=CASHTOKEN_CAPABILITY,
                          token_amount=CASHTOKEN_AMOUNT)
        assert unspent == Unspent(10000, 7, script, "txid", 0)

        script = PREFIX_CAPABILITY_COMMITMENT.hex()
        unspent = Unspent(10000, 7, script, "txid", 0, CASHTOKEN_CATAGORY_ID,
                          nft_capability=CASHTOKEN_CAPABILITY,
                          nft_commitment=CASHTOKEN_COMMITMENT)
        assert unspent == Unspent(10000, 7, script, "txid", 0)

        script = PREFIX_CAPABILITY_COMMITMENT_AMOUNT.hex()
        unspent = Unspent(10000, 7, script, "txid", 0, CASHTOKEN_CATAGORY_ID,
                          nft_capability=CASHTOKEN_CAPABILITY,
                          nft_commitment=CASHTOKEN_COMMITMENT,
                          token_amount=CASHTOKEN_AMOUNT)
        assert unspent == Unspent(10000, 7, script, "txid", 0)

        script = PREFIX_AMOUNT.hex()
        unspent = Unspent(10000, 7, script, "txid", 0, CASHTOKEN_CATAGORY_ID,
                          token_amount=CASHTOKEN_AMOUNT)
        assert unspent == Unspent(10000, 7, script, "txid", 0)

        # test vectors from https://github.com/bitjson/cashtokens
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
            unspent = Unspent(100, 7, script, "txid", 0, catagory_id,
                              nft_capability, nft_commitment, token_amount)
            assert unspent == Unspent(100, 7, script, "txid", 0)

    def test_dict_conversion(self):
        unspent = Unspent(10000, 7, "script", "txid", 0)

        assert unspent == Unspent.from_dict(unspent.to_dict())

    def test_equality(self):
        unspent1 = Unspent(10000, 7, "script", "txid", 0)
        unspent2 = Unspent(10000, 7, "script", "txid", 0)
        unspent3 = Unspent(50000, 7, "script", "txid", 0)
        assert unspent1 == unspent2
        assert unspent1 != unspent3

    def test_repr(self):
        unspent = Unspent(10000, 7, "script", "txid", 0)

        assert repr(unspent) == (
            "Unspent(amount=10000, confirmations=7, "
            "script='script', txid='txid', txindex=0)"
        )

    def test_gt(self):
        unspent = Unspent(10000, 7, "script", "txid", 0)
        unspent1 = Unspent(20000, 7, "script", "txid", 0)
        unspent2 = Unspent(10000, 7, "script", "txid", 0, "catagory_id",
                           "none")
        unspent3 = Unspent(30000, 7, "script", "txid", 0, "catagory_id",
                           "none")
        unspent4 = Unspent(10000, 7, "script", "txid", 0, "catagory_id",
                           "mutable")
        unspent5 = Unspent(20000, 7, "script", "txid", 0, "catagory_id",
                           token_amount=50)
        unspent6 = Unspent(20000, 7, "script", "txid", 0, "catagory_id",
                           token_amount=20)
        unspent7 = Unspent(30000, 7, "script", "txid", 0, "catagory_id",
                           token_amount=20)

        assert unspent1 > unspent
        assert unspent2 > unspent
        assert unspent4 > unspent2
        assert not unspent2 > unspent4
        assert not unspent > unspent2
        assert unspent3 > unspent2
        assert unspent5 > unspent
        assert not unspent > unspent5
        assert unspent5 > unspent7
        assert not unspent6 > unspent5
        assert unspent7 > unspent6
