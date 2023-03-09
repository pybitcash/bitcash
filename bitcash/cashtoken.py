from bitcash.network import NetworkAPI
from bitcash.network.rates import currency_to_satoshi_cached
from bitcash.network.meta import Unspent
from bitcash.cashaddress import Address
from bitcash.utils import int_to_varint
from bitcash.op import OpCodes
from bitcash.exceptions import InsufficientFunds, InvalidCashToken


# block after 1684152000 MTP (2023-05-15T12:00:00.000Z)
# !FIXME
CASHTOKEN_ACTIVATION_BLOCKHEIGHT = 782467
COMMITMENT_LENGTH = 40
DUST_VALUE = 512


class CashTokenOutput:

    __slots__ = ("catagory_id", "nft_commitment", "nft_capability",
                 "token_amount", "amount", "_genesis")

    def __init__(
        self,
        catagory_id=None,
        nft_capability=None,
        nft_commitment=None,
        token_amount=None,
        amount=0,
        _genesis=False,
    ):
        if catagory_id is None:
            if (
                nft_capability is not None
                or token_amount is not None
            ):
                raise InvalidCashToken("catagory_id missing")
        else:
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

        self.amount = amount
        self.catagory_id = catagory_id
        self.nft_commitment = nft_commitment
        self.nft_capability = nft_capability
        self.token_amount = token_amount
        self._genesis = _genesis

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
        if isinstance(output[2], CashTokenOutput) or output[2] is None:
            # already cashtoken aware
            # usefull when genesis token output are made with _genesis=True
            # or is OP_RETURN message
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

    (dest, amount, currency, catagory_id, nft_capability, nft_commitment,
     token_amount) = output

    if not isinstance(dest, Address):
        dest = Address.from_string(dest)

    amount = currency_to_satoshi_cached(amount, currency)

    cashtoken = CashTokenOutput(
        amount=amount,
        catagory_id=catagory_id,
        nft_commitment=nft_commitment,
        nft_capability=nft_capability,
        token_amount=token_amount
    )

    return (
        cashtoken.token_prefix + dest.scriptcode,
        amount,
        cashtoken
    )


class CashTokenUnspents:
    """
    Class to count CashToken Unspent
    Incoming data is assumed to be valid, tests are performed when making
    outputs

    >>> cashtoken.tokendata = {
            "category_id" : {           (string) token id hex
                "token_amount" : "xxx", (int) fungible amount
                "nft" : [{
                  "capability" : "xxx", (string) one of "immutable", "mutable",
                                        "minting"
                  "commitment" : b"xxx" (bytes) NFT commitment
                }]
            }
        }
    """

    def __init__(self, unspents=None):
        self.amount = 0
        self.tokendata = {}
        if unspents is not None:
            for unspent in unspents:
                self.add_unspent(unspent)

    def to_dict(self):
        return {
            "amount": self.amount,
            "tokendata": self.tokendata
        }

    @classmethod
    def from_dict(cls, dict_):
        instance = cls([])
        instance.amount = dict_["amount"]
        instance.tokendata = dict_["tokendata"]
        return instance

    def add_unspent(self, unspent):
        self.amount += unspent.amount
        if unspent.has_cashtoken:
            catagorydata = self.tokendata.get(unspent.catagory_id, {})
            if unspent.has_amount:
                catagorydata["token_amount"] = (
                    catagorydata.get("token_amount", 0)
                    + unspent.token_amount
                )
            if unspent.has_nft:
                nftdata = {"capability": unspent.nft_capability}
                if unspent.nft_commitment is not None:
                    nftdata["commitment"] = unspent.nft_commitment
                catagorydata["nft"] = (
                    catagorydata.get("nft", [])
                    + [nftdata]
                )
            self.tokendata.update({unspent.catagory_id: catagorydata})

    def get_outputs(self, leftover):
        """
        Return sanitized outputs for the remaining cashtokens

        :param leftover: leftover address to add the outputs
        :type leftover: ``str``
        :rtype: tuple(``list``, ``int``)  # (outputs, leftover_amount)
        """
        outputs = []

        amount = self.amount

        for catagory_id, value in self.tokendata.items():
            token_amount = None
            if "token_amount" in value:
                token_amount = value["token_amount"]
            if "nft" in value:
                for i, nft in enumerate(value["nft"]):
                    nft_capability = nft["capability"]
                    nft_commitment = nft.get("commitment", None)
                    outputs.append(prepare_cashtoken_aware_output(
                        (leftover, DUST_VALUE, "satoshi", catagory_id,
                         nft_capability, nft_commitment, token_amount)
                    ))
                    # add token to first nft
                    token_amount = None
                    amount -= DUST_VALUE
            elif token_amount is not None:
                # token_amount but no nft
                outputs.append(prepare_cashtoken_aware_output(
                    (leftover, DUST_VALUE, "satoshi", catagory_id,
                     None, None, token_amount)
                ))
                amount -= DUST_VALUE

        if len(outputs) == 0:
            # no tokendata
            if amount > 0:
                # add leftover amount
                outputs.append(prepare_cashtoken_aware_output(
                    (leftover, amount, "satoshi")
                ))
        else:
            if amount < 0:
                raise InsufficientFunds("Not enough sats")
            # add leftover amount to last out
            last_out = list(outputs[-1])
            last_out[1] += amount
            outputs[-1] = tuple(last_out)

        return outputs, amount

    def subtract_output(self, ctoutput):
        if self.amount < ctoutput.amount:
            raise InsufficientFunds("Not enough amount")
        self.amount -= ctoutput.amount

        if ctoutput.has_cashtoken:
            if hasattr(ctoutput, "_genesis") and ctoutput._genesis:
                # new token generated
                return
            catagory_id = ctoutput.catagory_id
            if catagory_id not in self.tokendata.keys():
                raise InsufficientFunds("unspent catagory_id does not exist")
            catagorydata = self.tokendata[catagory_id]
            if ctoutput.has_amount:
                catagorydata = _subtract_token_amount(catagorydata,
                                                      ctoutput.token_amount)
            if ctoutput.has_nft:
                nft = [
                    ctoutput.nft_capability,
                    ctoutput.nft_commitment or "None"
                ]
                catagorydata = _subtract_nft(catagorydata, nft)

            # update tokendata
            if catagorydata == {}:
                self.tokendata.pop(catagory_id)
            else:
                self.tokendata.update({catagory_id: catagorydata})


def _subtract_token_amount(catagorydata, token_amount):
    if "token_amount" not in catagorydata:
        raise InsufficientFunds("No token amount")
    if catagorydata["token_amount"] < token_amount:
        raise InsufficientFunds("Not enough token amount")
    catagorydata["token_amount"] -= token_amount

    if (
        "token_amount" in catagorydata
        and catagorydata["token_amount"] == 0
    ):
        catagorydata.pop("token_amount")
    return catagorydata


def _subtract_nft(catagorydata, nft):
    """
    nft: [capability, commitment]
    """
    if "nft" not in catagorydata:
        raise InsufficientFunds("No nft found")
    # if immutable nft is asked, then immutable nft is spent
    # then a mutable nft is made to immutable, then minting
    # mints new nft.
    # if mutable nft is asked, then mutable nft is spent, then
    # minting mints new nft.
    # if minting nft is asked, then minting nft mints new.

    if nft[0] in ["immutable"]:
        try:
            return _subtract_immutable_nft(catagorydata, nft[1])
        except InsufficientFunds:
            pass

    if nft[0] in ["immutable", "mutable"]:
        try:
            return _subtract_mutable_nft(catagorydata)
        except InsufficientFunds:
            pass

    if nft[0] in ["immutable", "mutable", "minting"]:
        try:
            return _subtract_minting_nft(catagorydata)
        except InsufficientFunds:
            # none found
            raise InsufficientFunds("No capable nft found")


def _sanitize(catagorydata):
    if (
        "nft" in catagorydata
        and len(catagorydata["nft"]) == 0
    ):
        catagorydata.pop("nft")
    return catagorydata


def _subtract_immutable_nft(catagorydata, commitment):
    nft_capabilities = [_["capability"]
                        for _ in catagorydata["nft"]]
    nft_commitments = [_.get("commitment", "None")
                       for _ in catagorydata["nft"]]

    # find an immutable to send
    for i in range(len(catagorydata["nft"])):
        if (
            nft_capabilities[i] == "immutable"
            and nft_commitments[i] == commitment
        ):
            # found immutable with same commitment
            catagorydata["nft"].pop(i)
            return _sanitize(catagorydata)

    raise InsufficientFunds("No immutable nft")


def _subtract_mutable_nft(catagorydata):
    nft_capabilities = [_["capability"]
                        for _ in catagorydata["nft"]]
    # find a mutable to send
    for i in range(len(catagorydata["nft"])):
        if (
            nft_capabilities[i] == "mutable"
        ):
            # found mutable
            catagorydata["nft"].pop(i)
            return _sanitize(catagorydata)

    raise InsufficientFunds("No mutable nft")


def _subtract_minting_nft(catagorydata):
    nft_capabilities = [_["capability"]
                        for _ in catagorydata["nft"]]
    # find a minting to mint
    for i in range(len(catagorydata["nft"])):
        if (
            nft_capabilities[i] == "minting"
        ):
            # found minting
            return catagorydata

    raise InsufficientFunds("No minting nft")


class CashTokenOutputs:
    """
    class to count sanitized outputs and select unspents that cover them

    """
    def __init__(self, outputs):
        self.amount = 0
        self.tokendata = {}
        for output in outputs:
            self.add_output(output)

    def add_output(self, output):
        # sanitize
        prepare_cashtoken_aware_output(output)
        _, amount, cashtokenoutput = output
        if cashtokenoutput is None:
            # OP_RETURN or message output
            return
        if hasattr(cashtokenoutput, "_genesis") and cashtokenoutput._genesis:
            # genesis cashtoken, won't have equivalent unspent cashtoken
            self.amount += amount
            return

        if cashtokenoutput.has_cashtoken:
            catagorydata = self.tokendata.get(cashtokenoutput.catagory_id, {})
            if cashtokenoutput.has_amount:
                catagorydata["token_amount"] = (
                    catagorydata.get("token_amount", 0)
                    + cashtokenoutput.token_amount
                )
            if cashtokenoutput.has_nft:
                nftdata = {"capability": cashtokenoutput.nft_capability}
                if cashtokenoutput.nft_commitment is not None:
                    nftdata["commitment"] = cashtokenoutput.nft_commitment
                catagorydata["nft"] = (
                    catagorydata.get("nft", [])
                    + [nftdata]
                )
            self.tokendata.update({cashtokenoutput.catagory_id: catagorydata})

    def subtract_unspent(self, unspent):
        """
        subtract unspent that'll pay cashtoken part of the output
        """
        unspent_used = False

        catagorydata = self.tokendata.get(unspent.catagory_id, {})
        # check token_amount
        if unspent.has_amount and "token_amount" in catagorydata:
            unspent_used = True
            catagorydata["token_amount"] -= unspent.token_amount
            if catagorydata["token_amount"] < 0:
                catagorydata.pop("token_amount")

        # check nft
        if unspent.has_nft and "nft" in catagorydata:
            catagorydata, nft_used = _subtract_nft_output(unspent,
                                                          catagorydata)
            if nft_used:
                unspent_used = True

        if not unspent_used:
            raise ValueError("Unspent not used")

        # update self
        if catagorydata == {}:
            self.tokendata.pop(unspent.catagory_id)
        else:
            self.tokendata.update({unspent.catagory_id: catagorydata})
        # not used, but just for completeness
        # amount is added with individually adding unpents later
        self.amount -= unspent.amount
        if self.amount < 0:
            self.amount = 0


def _subtract_nft_output(unspent, catagorydata):
    if unspent.nft_capability == "minting":
        # minting pays all
        catagorydata.pop("nft")
        return _sanitize(catagorydata), True
    elif unspent.nft_capability == "mutable":
        # pays first mutable, or first immutable
        for i, nft in enumerate(catagorydata["nft"]):
            if nft["capability"] == "mutable":
                catagorydata["nft"].pop(i)
                return _sanitize(catagorydata), True
        else:
            for i, nft in enumerate(catagorydata["nft"]):
                if nft["capability"] == "immutable":
                    catagorydata["nft"].pop(i)
                    return _sanitize(catagorydata), True
    else:  # immutable
        nft_commitment = unspent.nft_commitment or "None"
        for i, nft in enumerate(catagorydata["nft"]):
            if (
                nft["capability"] == "immutable"
                and nft_commitment == nft.get("commitment", "None")
            ):
                catagorydata["nft"].pop(i)
                return _sanitize(catagorydata), True
    return catagorydata, False
