import io

from bitcash.network.rates import currency_to_satoshi_cached
from bitcash.cashaddress import Address
from bitcash.network.meta import Unspent
from bitcash.utils import int_to_varint, varint_to_int
from bitcash.op import OpCodes
from bitcash.exceptions import InsufficientFunds, InvalidCashToken, InvalidAddress


COMMITMENT_LENGTH = 40
DUST_VALUE = 512


class CashTokenOutput:
    """
    Representation of a cashtoken output with verified token properties

    :param category_id: category of the cashtoken
    """

    __slots__ = (
        "category_id",
        "nft_commitment",
        "nft_capability",
        "token_amount",
        "amount",
    )

    def __init__(
        self,
        category_id=None,
        nft_capability=None,
        nft_commitment=None,
        token_amount=None,
        amount=0,
    ):
        if category_id is None:
            if nft_capability is not None or token_amount is not None:
                raise InvalidCashToken("category_id missing")
        else:
            if token_amount is None and nft_capability is None:
                raise InvalidCashToken(
                    "CashToken must have either amount or capability"
                )

        if nft_capability is not None and nft_capability not in Unspent.NFT_CAPABILITY:
            raise InvalidCashToken(f"nft capability not in {Unspent.NFT_CAPABILITY}")
        if nft_commitment is not None:
            if nft_capability is None:
                raise InvalidCashToken("nft commitment found without nft capability")
            if not isinstance(nft_commitment, bytes):
                raise ValueError("expected nft_commitment as bytes")
            if len(nft_commitment) > COMMITMENT_LENGTH or len(nft_commitment) == 0:
                raise InvalidCashToken(
                    f"0 < valid nft commitment length"
                    f" <= {COMMITMENT_LENGTH}, received"
                    f" length: {len(nft_commitment)}"
                )
        if token_amount is not None and (
            token_amount > 9223372036854775807 or token_amount < 1
        ):
            raise InvalidCashToken("1 <= valid token amount <= 9223372036854775807")

        self.amount = amount
        self.category_id = category_id
        self.nft_commitment = nft_commitment
        self.nft_capability = nft_capability
        self.token_amount = token_amount

    def to_dict(self):
        dict_ = {attr: getattr(self, attr) for attr in CashTokenOutput.__slots__}
        # save nft_commitment as hex
        if dict_["nft_commitment"] is not None:
            dict_["nft_commitment"] = dict_["nft_commitment"].hex()
        return dict_

    @classmethod
    def from_dict(cls, d):
        # convert nft_commitment to bytes
        if d["nft_commitment"] is not None:
            d["nft_commitment"] = bytes.fromhex(d["nft_commitment"])
        return CashTokenOutput(**{attr: d[attr] for attr in CashTokenOutput.__slots__})

    @classmethod
    def from_unspent(cls, unspent):
        return cls(
            unspent.category_id,
            unspent.nft_capability,
            unspent.nft_commitment,
            unspent.token_amount,
            unspent.amount,
        )

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

        # OP_HASH256 byte order
        script = OpCodes.OP_TOKENPREFIX.b + bytes.fromhex(self.category_id)[::-1]
        prefix_structure = 0
        if self.nft_commitment is not None:
            prefix_structure += 4
        if self.has_nft:
            prefix_structure += 2
        if self.has_amount:
            prefix_structure += 1
        nft_capability = (
            0
            if self.nft_capability is None
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
        self = cls()
        # Assumes valid script
        has_commitment_length = False
        has_nft = False
        has_amount = False

        # make bytestream
        stream = io.BytesIO(script)

        if stream.read(1) != OpCodes.OP_TOKENPREFIX.b:
            # no token info available
            return self

        # OP_HASH256 byte order
        self.category_id = stream.read(32)[::-1].hex()

        token_bitfield = stream.read(1).hex()
        # 4 bit prefix
        _ = bin(int(token_bitfield[0], 16))[2:]
        _ = "0" * (4 - len(_)) + _
        prefix_structure = [bit == "1" for bit in _]
        if prefix_structure[1]:
            has_commitment_length = True
        if prefix_structure[2]:
            has_nft = True
        if prefix_structure[3]:
            has_amount = True

        nft_capability_bit = int(token_bitfield[1], 16)
        if has_nft:
            self.nft_capability = Unspent.NFT_CAPABILITY[nft_capability_bit]
        if has_commitment_length:
            commitment_length = varint_to_int(stream)
            self.nft_commitment = stream.read(commitment_length)
        if has_amount:
            self.token_amount = varint_to_int(stream)
        return self

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def __repr__(self):
        var_list = [
            f"{key}={repr(value)}"
            for key, value in self.to_dict().items()
            if value is not None
        ]

        return "CashToken({})".format(", ".join(var_list))


def prepare_cashtoken_aware_output(output):
    if len(output) == 3:
        if isinstance(output[2], CashTokenOutput) or output[2] is None:
            # already cashtoken aware or is OP_RETURN message
            return output
        dest, amount, currency = output
        if not isinstance(dest, Address):
            dest = Address.from_string(dest)
        amount = currency_to_satoshi_cached(amount, currency)
        return (
            dest.scriptcode,
            amount,
            CashTokenOutput(amount=amount),
        )

    (
        dest,
        amount,
        currency,
        category_id,
        nft_capability,
        nft_commitment,
        token_amount,
    ) = output

    if not isinstance(dest, Address):
        dest = Address.from_string(dest)

    amount = currency_to_satoshi_cached(amount, currency)

    cashtoken = CashTokenOutput(
        amount=amount,
        category_id=category_id,
        nft_commitment=nft_commitment,
        nft_capability=nft_capability,
        token_amount=token_amount,
    )

    # check for CashToken signal
    if "CATKN" not in dest.version and cashtoken.has_cashtoken:
        raise InvalidAddress(
            f"{dest.cash_address()} does not signal CashToken support."
        )

    return (cashtoken.token_prefix + dest.scriptcode, amount, cashtoken)


class CashTokenUnspents:
    """
    Class to count CashToken Unspent
    Incoming data is assumed to be valid, tests are performed when making
    outputs

    >>> cashtoken.tokendata = {
            "category_id" : {           (string) token id hex
                "token_amount" : "xxx", (int) fungible amount
                "nft" : [{
                  "capability" : "xxx", (string) one of "none", "mutable",
                                        "minting"
                  "commitment" : b"xxx" (bytes) NFT commitment
                }]
            }
        }
    """

    def __init__(self, unspents=None):
        self.amount = 0
        self.tokendata = {}
        # unspent txid that are valid genesis unspent
        self.genesis_unspent_txid = []
        if unspents is not None:
            for unspent in unspents:
                self.add_unspent(unspent)

    def to_dict(self):
        return {"amount": self.amount, "tokendata": self.tokendata}

    @classmethod
    def from_dict(cls, dict_):
        instance = cls([])
        instance.amount = dict_["amount"]
        instance.tokendata = dict_["tokendata"]
        return instance

    def add_unspent(self, unspent):
        self.amount += unspent.amount
        if unspent.has_cashtoken:
            categorydata = self.tokendata.get(unspent.category_id, {})
            if unspent.has_amount:
                categorydata["token_amount"] = (
                    categorydata.get("token_amount", 0) + unspent.token_amount
                )
            if unspent.has_nft:
                nftdata = {"capability": unspent.nft_capability}
                if unspent.nft_commitment is not None:
                    nftdata["commitment"] = unspent.nft_commitment
                categorydata["nft"] = categorydata.get("nft", []) + [nftdata]
            self.tokendata.update({unspent.category_id: categorydata})

        # possible cashtoken genesis unspent
        if unspent.txindex == 0:
            self.genesis_unspent_txid.append(unspent.txid)

    def get_outputs(self, leftover):
        """
        Return sanitized outputs for the remaining cashtokens

        :param leftover: leftover address to add the outputs
        :type leftover: ``str``
        :rtype: tuple(``list``, ``int``)  # (outputs, leftover_amount)
        """
        outputs = []

        amount = self.amount

        for category_id, value in self.tokendata.items():
            token_amount = None
            if "token_amount" in value:
                token_amount = value["token_amount"]
            if "nft" in value:
                for i, nft in enumerate(value["nft"]):
                    nft_capability = nft["capability"]
                    nft_commitment = nft.get("commitment", None)
                    outputs.append(
                        prepare_cashtoken_aware_output(
                            (
                                leftover,
                                DUST_VALUE,
                                "satoshi",
                                category_id,
                                nft_capability,
                                nft_commitment,
                                token_amount,
                            )
                        )
                    )
                    # add token to first nft
                    token_amount = None
                    amount -= DUST_VALUE
            elif token_amount is not None:
                # token_amount but no nft
                outputs.append(
                    prepare_cashtoken_aware_output(
                        (
                            leftover,
                            DUST_VALUE,
                            "satoshi",
                            category_id,
                            None,
                            None,
                            token_amount,
                        )
                    )
                )
                amount -= DUST_VALUE

        if len(outputs) == 0:
            # no tokendata
            if amount > 0:
                # add leftover amount
                outputs.append(
                    prepare_cashtoken_aware_output((leftover, amount, "satoshi"))
                )
        else:
            if amount < 0:
                raise InsufficientFunds("Not enough sats")
            # add leftover amount to last out
            last_out = list(outputs[-1])
            last_out[1] += amount
            last_out[2].amount += amount
            outputs[-1] = tuple(last_out)

        return outputs, amount

    def subtract_output(self, ctoutput):
        if self.amount < ctoutput.amount:
            raise InsufficientFunds("Not enough amount")
        self.amount -= ctoutput.amount

        if ctoutput.has_cashtoken:
            category_id = ctoutput.category_id
            if category_id in self.genesis_unspent_txid:
                # new token generated
                return
            if category_id not in self.tokendata.keys():
                raise InsufficientFunds("unspent category_id does not exist")
            categorydata = self.tokendata[category_id]
            if ctoutput.has_amount:
                categorydata = _subtract_token_amount(
                    categorydata, ctoutput.token_amount
                )
            if ctoutput.has_nft:
                nft = [ctoutput.nft_capability, ctoutput.nft_commitment or "None"]
                categorydata = _subtract_nft(categorydata, nft)

            # update tokendata
            if categorydata == {}:
                self.tokendata.pop(category_id)
            else:
                self.tokendata.update({category_id: categorydata})


def _subtract_token_amount(categorydata, token_amount):
    if "token_amount" not in categorydata:
        raise InsufficientFunds("No token amount")
    if categorydata["token_amount"] < token_amount:
        raise InsufficientFunds("Not enough token amount")
    categorydata["token_amount"] -= token_amount

    if "token_amount" in categorydata and categorydata["token_amount"] == 0:
        categorydata.pop("token_amount")
    return categorydata


def _subtract_nft(categorydata, nft):
    """
    nft: [capability, commitment]
    """
    if "nft" not in categorydata:
        raise InsufficientFunds("No nft found")
    # if immutable nft is asked, then immutable nft is spent
    # then a mutable nft is made to immutable, then minting
    # mints new nft.
    # if mutable nft is asked, then mutable nft is spent, then
    # minting mints new nft.
    # if minting nft is asked, then minting nft mints new.

    if nft[0] in ["none"]:
        # immutable
        try:
            return _subtract_immutable_nft(categorydata, nft[1])
        except InsufficientFunds:
            pass

    if nft[0] in ["none", "mutable"]:
        try:
            return _subtract_mutable_nft(categorydata)
        except InsufficientFunds:
            pass

    if nft[0] in ["none", "mutable", "minting"]:
        try:
            return _subtract_minting_nft(categorydata)
        except InsufficientFunds:
            # none found
            raise InsufficientFunds("No capable nft found")


def _sanitize(categorydata):
    if "nft" in categorydata and len(categorydata["nft"]) == 0:
        categorydata.pop("nft")
    return categorydata


def _subtract_immutable_nft(categorydata, commitment):
    nft_capabilities = [_["capability"] for _ in categorydata["nft"]]
    nft_commitments = [_.get("commitment", "None") for _ in categorydata["nft"]]

    # find an immutable to send
    for i in range(len(categorydata["nft"])):
        if nft_capabilities[i] == "none" and nft_commitments[i] == commitment:
            # found immutable with same commitment
            categorydata["nft"].pop(i)
            return _sanitize(categorydata)

    raise InsufficientFunds("No immutable nft")


def _subtract_mutable_nft(categorydata):
    nft_capabilities = [_["capability"] for _ in categorydata["nft"]]
    # find a mutable to send
    for i in range(len(categorydata["nft"])):
        if nft_capabilities[i] == "mutable":
            # found mutable
            categorydata["nft"].pop(i)
            return _sanitize(categorydata)

    raise InsufficientFunds("No mutable nft")


def _subtract_minting_nft(categorydata):
    nft_capabilities = [_["capability"] for _ in categorydata["nft"]]
    # find a minting to mint
    for i in range(len(categorydata["nft"])):
        if nft_capabilities[i] == "minting":
            # found minting
            return categorydata

    raise InsufficientFunds("No minting nft")


def select_cashtoken_utxo(unspents, outputs):
    """
    Function to select unspents that cover cashtokens of sanitized outputs
    """
    unspents_used = []

    # if category id is txid of genesis unspent, then the unspent is mandatory
    mandatory_unspent_indices = set()
    genesis_unspent_txid = {
        unspent.txid: i for i, unspent in enumerate(unspents) if unspent.txindex == 0
    }

    # tokendata in outputs
    tokendata = {}

    # calculate needed cashtokens
    for output in outputs:
        cashtokenoutput = output[2]
        if cashtokenoutput is not None and cashtokenoutput.has_cashtoken:
            if cashtokenoutput.category_id in genesis_unspent_txid.keys():
                indx = genesis_unspent_txid[cashtokenoutput.category_id]
                mandatory_unspent_indices.add(indx)
                # not count cashtoken from genesis tx
                # the category id won't be in utxo
                continue
            categorydata = tokendata.get(cashtokenoutput.category_id, {})
            if cashtokenoutput.has_amount:
                categorydata["token_amount"] = (
                    categorydata.get("token_amount", 0) + cashtokenoutput.token_amount
                )
            if cashtokenoutput.has_nft:
                nftdata = {"capability": cashtokenoutput.nft_capability}
                if cashtokenoutput.nft_commitment is not None:
                    nftdata["commitment"] = cashtokenoutput.nft_commitment
                categorydata["nft"] = categorydata.get("nft", []) + [nftdata]
            tokendata.update({cashtokenoutput.category_id: categorydata})

    # add mandatory unspents, for genesis cashtoken
    for id_ in sorted(mandatory_unspent_indices)[::-1]:
        unspents_used.append(unspents.pop(id_))

    # add utxo that can fund the output tokendata
    # split unspent with cashtoken from rest
    unspents_cashtoken = []
    pop_ids = []
    for i, unspent in enumerate(unspents):
        if unspent.has_cashtoken:
            unspents_cashtoken.append(unspent)
            pop_ids.append(i)
    for id_ in sorted(pop_ids)[::-1]:
        unspents.pop(id_)

    # sort and use required cashtoken unspents
    # cashtokens are selected with the same criteria as utxo selection for BCH
    # small token_amount is spent first, and for nft the order is to spend an
    # immutable if possible, or then spend a mutable with mutation or then
    # finally use a minting token to mint the output nft.
    unspents_cashtoken = sorted(unspents_cashtoken)
    pop_ids = []
    for i, unspent in enumerate(unspents_cashtoken):
        unspent_used = False

        categorydata = tokendata.get(unspent.category_id, {})
        # check token_amount
        if unspent.has_amount and "token_amount" in categorydata:
            unspent_used = True
            categorydata["token_amount"] -= unspent.token_amount
            if categorydata["token_amount"] < 0:
                categorydata.pop("token_amount")

        # check nft
        if unspent.has_nft and "nft" in categorydata:
            categorydata, nft_used = _subtract_nft_output(unspent, categorydata)
            if nft_used:
                unspent_used = True

        if not unspent_used:
            continue

        # use unspent
        unspents_used.append(unspent)
        pop_ids.append(i)
        # update tokendata
        if categorydata == {}:
            tokendata.pop(unspent.category_id)
        else:
            tokendata.update({unspent.category_id: categorydata})
    for id_ in sorted(pop_ids)[::-1]:
        unspents_cashtoken.pop(id_)

    # sort the rest unspents and fund the bch amount
    # __gt__ and __eq__ will sort them with no cashtoken unspents first
    unspents = sorted(unspents + unspents_cashtoken)
    return unspents, unspents_used


def _subtract_nft_output(unspent, categorydata):
    if unspent.nft_capability == "minting":
        # minting pays all
        categorydata.pop("nft")
        return _sanitize(categorydata), True
    elif unspent.nft_capability == "mutable":
        # pays first mutable, or first immutable
        for i, nft in enumerate(categorydata["nft"]):
            if nft["capability"] == "mutable":
                categorydata["nft"].pop(i)
                return _sanitize(categorydata), True
        else:
            for i, nft in enumerate(categorydata["nft"]):
                if nft["capability"] == "none":
                    categorydata["nft"].pop(i)
                    return _sanitize(categorydata), True
    else:  # immutable
        nft_commitment = unspent.nft_commitment or "None"
        for i, nft in enumerate(categorydata["nft"]):
            if nft["capability"] == "none" and nft_commitment == nft.get(
                "commitment", "None"
            ):
                categorydata["nft"].pop(i)
                return _sanitize(categorydata), True
    return categorydata, False
