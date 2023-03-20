import decimal
from binascii import hexlify


class Decimal(decimal.Decimal):
    def __new__(cls, value):
        return super().__new__(cls, str(value))


def chunk_data(data, size):
    return (data[i : i + size] for i in range(0, len(data), size))


def int_to_unknown_bytes(num, byteorder="big"):
    """Converts an int to the least number of bytes as possible."""
    return num.to_bytes((num.bit_length() + 7) // 8 or 1, byteorder)


def bytes_to_hex(bytestr, upper=False):
    hexed = hexlify(bytestr).decode()
    return hexed.upper() if upper else hexed


def hex_to_bytes(hexed):
    if len(hexed) & 1:
        hexed = "0" + hexed

    return bytes.fromhex(hexed)


def int_to_hex(num, upper=False):
    hexed = hex(num)[2:]
    return hexed.upper() if upper else hexed


def hex_to_int(hexed):
    return int(hexed, 16)


def flip_hex_byte_order(string):
    return bytes_to_hex(hex_to_bytes(string)[::-1])


def int_to_varint(val):
    if val < 253:
        return val.to_bytes(1, "little")
    elif val <= 65535:
        return b"\xfd" + val.to_bytes(2, "little")
    elif val <= 4294967295:
        return b"\xfe" + val.to_bytes(4, "little")
    else:
        return b"\xff" + val.to_bytes(8, "little")


def varint_to_int(val):
    """
    Converts varint to int from incoming bytecode.
    Also returns the number of bytes used.

    :param val: the bytecode starting with varint
    :type val: ``bytes``
    :returns: tuple of (int, bytes_used)
    """
    if val.startswith(b"\xff"):
        return (int.from_bytes(val[1:9], "little"), 9)
    if val.startswith(b"\xfe"):
        return (int.from_bytes(val[1:5], "little"), 5)
    if val.startswith(b"\xfd"):
        return (int.from_bytes(val[1:3], "little"), 3)
    return (int.from_bytes(val[:1], "little"), 1)
