from bitcash.network import NetworkAPI
from bitcash.network.rates import currency_to_satoshi_cached
from bitcash.network.meta import Unspent
from bitcash.cashaddress import Address
from bitcash.utils import int_to_varint
from bitcash.op import OpCodes


# block after 1684152000 MTP (2023-05-15T12:00:00.000Z)
CASHTOKEN_ACTIVATION_BLOCKHEIGHT = 782467
COMMITMENT_LENGTH = 40


class InvalidCashToken(ValueError):
    pass


class CashTokenOutput:

    __slots__ = ("catagory_id", "nft_commitment", "nft_capability",
                 "token_amount")

    def __init__(
        self,
        catagory_id=None,
        nft_capability=None,
        nft_commitment=None,
        token_amount=None
    ):
        if catagory_id is not None:
            # checking for Pre-activation token-forgery outputs (PATFOs)
            tx = NetworkAPI.get_transaction(catagory_id)
            if tx.block < CASHTOKEN_ACTIVATION_BLOCKHEIGHT:
                raise InvalidCashToken("Pre-activation token-forgery output")
            if token_amount is None and nft_capability is None:
                raise InvalidCashToken("CashToken must have either amount or"
                                       " capability")

        if (
            nft_capability is not None
            and nft_capability not in Unspent.NFT_CAPABILITY
        ):
            raise InvalidCashToken(f"nft capability not in "
                                   f"{Unspent.NFT_CAPABILITY}")
        if nft_commitment is not None:
            if nft_capability is None:
                raise InvalidCashToken("nft commitment found without"
                                       " nft capability")
            if not isinstance(nft_commitment, bytes):
                raise ValueError("expected nft_commitment as bytes")
            if len(nft_commitment) > 40 or len(nft_commitment) == 0:
                raise InvalidCashToken("0 < valid nft commitment length <= 40")
        if (
            token_amount is not None
            and (token_amount > 9223372036854775807 or token_amount < 1)
        ):
            raise InvalidCashToken("1 <= valid token amount <= "
                                   "9223372036854775807")

        self.catagory_id = catagory_id
        self.nft_commitment = nft_commitment
        self.nft_capability = nft_capability
        self.token_amount = token_amount

    def to_dict(self):
        return {attr: getattr(self, attr)
                for attr in CashTokenOutput.__slots__}

    @classmethod
    def from_dict(cls, d):
        return CashTokenOutput(**{attr: d[attr]
                                  for attr in CashTokenOutput.__slots__})

    @property
    def has_nft(self):
        return self.nft_capability is not None

    @property
    def has_amount(self):
        return self.token_amount is not None

    @property
    def has_cashtoken(self):
        return self.has_amount or self.has_nft

    @property
    def token_prefix(self):
        if not self.has_cashtoken:
            return b""

        script = OpCodes.OP_TOKENPREFIX.b + bytes.fromhex(self.catagory_id)
        prefix_structure = 0
        if self.nft_commitment is not None:
            prefix_structure += 4
        if self.has_nft:
            prefix_structure += 2
        if self.has_amount:
            prefix_structure += 1
        nft_capability = (
            0 if self.nft_capability is None
            else Unspent.NFT_CAPABILITY.index(self.nft_capability)
        )
        # token bitfield
        token_bitfield = hex(prefix_structure)[2:] + hex(nft_capability)[2:]
        script += bytes.fromhex(token_bitfield)
        if self.nft_commitment is not None:
            script += int_to_varint(len(self.nft_commitment))
            script += self.nft_commitment
        if self.has_amount:
            script += int_to_varint(self.token_amount)

        return script

    @classmethod
    def from_script(cls, script):
        instance = cls()
        Unspent.parse_script(instance, script.hex())
        return instance

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def __repr__(self):

        var_list = [f"{key}={repr(value)}"
                    for key, value in self.to_dict().items()
                    if value is not None]

        return "CashToken({})".format(", ".join(var_list))


def prepare_cashtoken_aware_output(output):
    if len(output) == 3:
        dest, amount, currency = output
        dest = Address.from_string(dest)
        return (
            dest.scriptcode,
            currency_to_satoshi_cached(amount, currency),
            None,
            None,
            None,
            None
        )
    (dest, amount, currency, catagory_id, nft_capability, nft_commitment,
     token_amount) = output
    dest = Address.from_string(dest)

    cashtoken = CashTokenOutput(
        catagory_id=catagory_id,
        nft_commitment=nft_commitment,
        nft_capability=nft_capability,
        token_amount=token_amount
    )

    return (
        cashtoken.token_prefix + dest.scriptcode,
        currency_to_satoshi_cached(amount, currency),
        cashtoken.catagory_id,
        cashtoken.nft_capability,
        cashtoken.nft_commitment,
        cashtoken.token_amount
    )
