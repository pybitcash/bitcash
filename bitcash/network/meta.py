from bitcash.op import OpCodes


TX_TRUST_LOW = 1
TX_TRUST_MEDIUM = 6
TX_TRUST_HIGH = 30


class Unspent:
    """
    Represents an unspent transaction output (UTXO) with CashToken
    """

    __slots__ = ("amount", "confirmations", "script", "txid",
                 "txindex", "catagory_id", "nft_capability", "nft_commitment",
                 "token_amount")

    NFT_CAPABILITY = ["immutable", "mutable", "minting"]

    def __init__(
        self,
        amount,
        confirmations,
        script,
        txid,
        txindex,
        catagory_id=None,
        nft_capability=None,
        nft_commitment=None,
        token_amount=None
    ):
        self.amount = amount
        self.confirmations = confirmations
        self.script = script
        self.txid = txid
        self.txindex = txindex
        self.catagory_id = catagory_id
        self.nft_capability = nft_capability
        self.nft_commitment = nft_commitment
        self.token_amount = token_amount

        # if API doesn't support CashToken implicitly
        if self.catagory_id is None:
            self.parse_script(script)

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in Unspent.__slots__}

    @classmethod
    def from_dict(cls, d):
        return Unspent(**{attr: d[attr] for attr in Unspent.__slots__})

    @property
    def has_nft(self):
        return self.nft_capability is not None

    @property
    def has_amount(self):
        return self.token_amount is not None

    @property
    def has_cashtoken(self):
        return self.has_amount or self.has_nft

    def parse_script(self, scriptcode):
        # Assumes valid scriptcode
        has_commitment_length = False
        has_nft = False
        has_amount = False

        if not scriptcode.startswith(OpCodes.OP_TOKENPREFIX.h):
            # no token info available
            return

        self.catagory_id = scriptcode[2:66]
        # OP_HASH256 byte order
        self.catagory_id = bytes.fromhex(self.catagory_id)[::-1].hex()

        token_bitfield = scriptcode[66:68]
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
        script_counter = 68
        if has_commitment_length:
            next_byte = scriptcode[script_counter:script_counter+2]
            if next_byte == "ff":
                start_counter, script_counter = (script_counter + 2,
                                                 script_counter + 18)
            elif next_byte == "fe":
                start_counter, script_counter = (script_counter + 2,
                                                 script_counter + 10)
            elif next_byte == "fd":
                start_counter, script_counter = (script_counter + 2,
                                                 script_counter + 6)
            else:
                start_counter, script_counter = (script_counter,
                                                 script_counter + 2)
            commitment_length = int.from_bytes(bytes.fromhex(
                scriptcode[start_counter:script_counter]
            ), "little") * 2  # hex

            _ = script_counter + commitment_length
            self.nft_commitment = bytes.fromhex(scriptcode[script_counter:_])
            script_counter += commitment_length

        if has_amount:
            next_byte = scriptcode[script_counter:script_counter+2]
            if next_byte == "ff":
                start_counter, script_counter = (script_counter + 2,
                                                 script_counter + 18)
            elif next_byte == "fe":
                start_counter, script_counter = (script_counter + 2,
                                                 script_counter + 10)
            elif next_byte == "fd":
                start_counter, script_counter = (script_counter + 2,
                                                 script_counter + 6)
            else:
                start_counter, script_counter = (script_counter,
                                                 script_counter + 2)
            self.token_amount = int.from_bytes(bytes.fromhex(
                scriptcode[start_counter:script_counter]
            ), "little")

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def __gt__(self, other):
        """
        Method to help sorting of Unspents during spending
        """
        if self.has_nft:
            if not other.has_nft:
                return True
            if (
                Unspent.NFT_CAPABILITY.index(self.nft_capability)
                > Unspent.NFT_CAPABILITY.index(other.nft_capability)
            ):
                return True
            if (
                Unspent.NFT_CAPABILITY.index(self.nft_capability)
                < Unspent.NFT_CAPABILITY.index(other.nft_capability)
            ):
                return False
        elif other.has_nft:
            return False
        if self.has_amount:
            if not other.has_amount:
                return True
            if (self.token_amount > other.token_amount):
                return True
            if (self.token_amount < other.token_amount):
                return False
        elif other.has_amount:
            return False
        return self.amount > other.amount

    def __repr__(self):

        var_list = [f"{key}={repr(value)}"
                    for key, value in self.to_dict().items()
                    if value is not None]
        return "Unspent({})".format(", ".join(var_list))
