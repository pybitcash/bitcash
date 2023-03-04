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


class TestUnspent:
    def test_init(self):
        unspent = Unspent(10000, 7, "script", "txid", 0, "catagory_id",
                          "immutable", "nft_commitment", 50)
        assert unspent.amount == 10000
        assert unspent.confirmations == 7
        assert unspent.script == "script"
        assert unspent.txid == "txid"
        assert unspent.txindex == 0
        assert unspent.catagory_id == "catagory_id"
        assert unspent.nft_commitment == "nft_commitment"
        assert unspent.nft_capability == "immutable"
        assert unspent.token_amount == 50
        # CashToken properties
        assert unspent.has_amount is True
        assert unspent.has_nft is True
        assert unspent.has_cashtoken is True

    def test_parse_script(self):
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
