from collections import namedtuple

###
# SLP message creation functions below.
###

lokad_id = b"SLP\x00"
TYPE_SCRIPT = 2


class ScriptOutput(namedtuple("ScriptAddressTuple", "script")):
    @classmethod
    def from_string(self, string):
        """Instantiate from a mixture of opcodes and raw data."""
        script = bytearray()
        for word in string.split():
            if word.startswith("OP_"):
                try:
                    opcode = OpCodes[word]
                except KeyError:
                    raise AddressError("unknown opcode {}".format(word))
                script.append(opcode)
            elif word.lower().startswith("<empty>"):
                script.extend([OpCodes.OP_PUSHDATA1, OpCodes.OP_0])
            else:
                import binascii

                script.extend(Script.push_data(binascii.unhexlify(word)))
        return ScriptOutput(bytes(script))

    def to_ui_string(self, hex_only=False):
        """Convert to user-readable OP-codes (plus text), eg OP_RETURN (12) "Hello there!"
        Or, to a hexadecimal string if that fails.
        Note that this function is the inverse of from_string() only if called with hex_only = True!"""
        if self.script and not hex_only:
            try:
                ret = ""
                ops = Script.get_ops(self.script)

                def lookup(x):
                    try:
                        return OpCodes(x).name
                    except ValueError:
                        return "(" + str(x) + ")"

                for op in ops:
                    if ret:
                        ret += ", "
                    if isinstance(op, tuple):
                        if op[1] is None:
                            ret += "<EMPTY>"
                        else:
                            if hex_only:
                                friendlystring = None
                            else:
                                # Attempt to make a friendly string, or fail to hex
                                try:
                                    # Ascii only
                                    friendlystring = op[1].decode(
                                        "ascii"
                                    )  # raises UnicodeDecodeError with bytes > 127.

                                    # Count ugly characters (that need escaping in python strings' repr())
                                    uglies = 0
                                    for b in op[1]:
                                        if b < 0x20 or b == 0x7F:
                                            uglies += 1
                                    # Less than half of characters may be ugly.
                                    if 2 * uglies >= len(op[1]):
                                        friendlystring = None
                                except UnicodeDecodeError:
                                    friendlystring = None

                            if friendlystring is None:
                                ret += lookup(op[0]) + " " + op[1].hex()
                            else:
                                ret += lookup(op[0]) + " " + repr(friendlystring)
                    elif isinstance(op, int):
                        ret += lookup(op)
                    else:
                        ret += (
                            "[" + (op.hex() if isinstance(op, bytes) else str(op)) + "]"
                        )
                return ret
            except ScriptError:
                # Truncated script -- so just default to normal 'hex' encoding below.
                pass
        return self.script.hex()

    def to_script(self):
        return self.script

    def __str__(self):
        return self.to_ui_string(True)

    def __repr__(self):
        return "<ScriptOutput {}>".format(self.__str__())


class OPReturnTooLarge(Exception):
    pass


class ScriptError(Exception):
    pass


# utility for creation: use smallest push except not any of: op_0, op_1negate, op_1 to op_16
def __pushChunk__(chunk: bytes) -> bytes:  # allow_op_0 = False, allow_op_number = False
    length = len(chunk)
    if length == 0:
        return b"\x4c\x00" + chunk
    elif length < 76:
        return bytes((length,)) + chunk
    elif length < 256:
        return (
            bytes(
                (
                    0x4C,
                    length,
                )
            )
            + chunk
        )
    elif length < 65536:  # shouldn't happen but eh
        return b"\x4d" + length.to_bytes(2, "little") + chunk
    elif length < 4294967296:  # shouldn't happen but eh
        return b"\x4e" + length.to_bytes(4, "little") + chunk
    else:
        raise ValueError()


# utility for creation
def __chunksToOpreturnOutput__(chunks: [bytes]) -> tuple:
    script = bytearray(
        [
            0x6A,
        ]
    )  # start with OP_RETURN
    for c in chunks:
        script.extend(__pushChunk__(c))

    if len(script) > 223:
        raise OPReturnTooLarge(
            "OP_RETURN message too large, cannot be larger than 223 bytes"
        )

    return ScriptOutput(bytes(script)).to_ui_string(hex_only=True)


# SLP GENESIS Message
def buildGenesisOpReturn(
    ticker: str,
    token_name: str,
    token_document_url: str,
    token_document_hash_hex: str,
    decimals: int,
    baton_vout: int,
    initial_token_mint_quantity: int,
    token_type: int = 1,
) -> tuple:
    chunks = []
    script = bytearray((0x6A,))  # OP_RETURN

    # lokad id
    chunks.append(lokad_id)

    # token version/type
    if token_type in [1, "SLP1"]:
        chunks.append(b"\x01")
    elif token_type in [65, "SLP65"]:
        chunks.append(b"\x41")
    elif token_type in [129, "SLP129"]:
        chunks.append(b"\x81")
    else:
        raise Exception("Unsupported token type")

    # transaction type
    chunks.append(b"GENESIS")

    # ticker (can be None)
    if ticker is None:
        tickerb = b""
    else:
        tickerb = ticker.encode("utf-8")
    chunks.append(tickerb)

    # name (can be None)
    if token_name is None:
        chunks.append(b"")
    else:
        chunks.append(token_name.encode("utf-8"))

    # doc_url (can be None)
    if token_document_url is None:
        chunks.append(b"")
    else:
        chunks.append(token_document_url.encode("ascii"))

    # doc_hash (can be None)
    if token_document_hash_hex is None:
        chunks.append(b"")
    else:
        dochash = bytes.fromhex(token_document_hash_hex)
        if len(dochash) not in (0, 32):
            raise SlpSerializingError()
        chunks.append(dochash)

    # decimals
    decimals = int(decimals)
    if decimals > 9 or decimals < 0:
        raise SlpSerializingError()
    chunks.append(bytes((decimals,)))

    # baton vout
    if baton_vout is None:
        chunks.append(b"")
    else:
        if baton_vout < 2:
            raise SlpSerializingError()
        chunks.append(bytes((baton_vout,)))

    # init quantity
    qb = int(initial_token_mint_quantity).to_bytes(8, "big")
    chunks.append(qb)

    return __chunksToOpreturnOutput__(chunks)


# SLP MINT Message
def buildMintOpReturn(
    token_id_hex: str, baton_vout: int, token_mint_quantity: int, token_type: int = 1
) -> tuple:
    chunks = []

    # lokad id
    chunks.append(lokad_id)

    # token version/type
    if token_type in [1, "SLP1"]:
        chunks.append(b"\x01")
    elif token_type in [129, "SLP129"]:
        chunks.append(b"\x81")
    else:
        raise Exception("Unsupported token type")

    # transaction type
    chunks.append(b"MINT")

    # token id
    tokenId = bytes.fromhex(token_id_hex)
    if len(tokenId) != 32:
        raise SlpSerializingError()
    chunks.append(tokenId)

    # baton vout
    if baton_vout is None:
        chunks.append(b"")
    else:
        if baton_vout < 2:
            raise SlpSerializingError()
        chunks.append(bytes((baton_vout,)))

    # init quantity
    qb = int(token_mint_quantity).to_bytes(8, "big")
    chunks.append(qb)

    return __chunksToOpreturnOutput__(chunks)


# SLP SEND Message
def buildSendOpReturn(
    token_id_hex: str, output_qty_array: [int], token_type: int = 1
) -> tuple:
    chunks = []

    # lokad id
    chunks.append(lokad_id)

    # token version/type
    if token_type in [1, "SLP1"]:
        chunks.append(b"\x01")
    elif token_type in [65, "SLP65"]:
        chunks.append(b"\x41")
    elif token_type in [129, "SLP129"]:
        chunks.append(b"\x81")
    else:
        raise Exception("Unsupported token type")

    # transaction type
    chunks.append(b"SEND")

    # token id
    tokenId = bytes.fromhex(token_id_hex)
    if len(tokenId) != 32:
        raise SlpSerializingError()
    chunks.append(tokenId)

    # output quantities
    if len(output_qty_array) < 1:
        raise SlpSerializingError("Cannot have less than 1 SLP Token output.")
    if len(output_qty_array) > 19:
        raise SlpSerializingError("Cannot have more than 19 SLP Token outputs.")
    for qty in output_qty_array:
        qb = int(qty).to_bytes(8, "big")
        chunks.append(qb)

    return __chunksToOpreturnOutput__(chunks)
