from __future__ import annotations

import io
from typing import Any, Optional

from bitcash.exceptions import InvalidAddress
from bitcash.op import OpCodes
from bitcash.types import CashAddressVersion, Network
from bitcash.utils import varint_to_int

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def polymod(values: list[int]) -> int:
    chk = 1
    generator = [
        (0x01, 0x98F2BC8E61),
        (0x02, 0x79B76D99E2),
        (0x04, 0xF33E5FB3C4),
        (0x08, 0xAE2EABE2A8),
        (0x10, 0x1E4F43E470),
    ]
    for value in values:
        top = chk >> 35
        chk = ((chk & 0x07FFFFFFFF) << 5) ^ value
        for i in generator:
            if top & i[0] != 0:
                chk ^= i[1]
    return chk ^ 1


def calculate_checksum(prefix: str, payload: list[int]) -> list[int]:
    poly = polymod(prefix_expand(prefix) + payload + [0, 0, 0, 0, 0, 0, 0, 0])
    out: list[int] = list()
    for i in range(8):
        out.append((poly >> 5 * (7 - i)) & 0x1F)
    return out


def verify_checksum(prefix: str, payload: list[int]) -> bool:
    return polymod(prefix_expand(prefix) + payload) == 0


def b32decode(inputs: str) -> list[int]:
    out: list[int] = []
    for letter in inputs:
        out.append(CHARSET.find(letter))
    return out


def b32encode(inputs: list[int]) -> str:
    out = ""
    for char_code in inputs:
        out += CHARSET[char_code]
    return out


def convertbits(
    data: list[int], frombits: int, tobits: int, pad: bool = True
) -> Optional[list[int]]:
    acc = 0
    bits = 0
    ret: list[int] = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


def prefix_expand(prefix: str) -> list[int]:
    return [ord(x) & 0x1F for x in prefix] + [0]


class Address:
    """
    Class to handle CashAddr.

    :param version: Version of CashAddr
    :param payload: Payload of CashAddr as int list of the bytearray
    """

    VERSIONS: dict[str, CashAddressVersion] = {
        "P2SH20": CashAddressVersion("bitcoincash", 8, Network.main),
        "P2SH32": CashAddressVersion("bitcoincash", 11, Network.main),
        "P2PKH": CashAddressVersion("bitcoincash", 0, Network.main),
        "P2SH20-TESTNET": CashAddressVersion("bchtest", 8, Network.test),
        "P2SH32-TESTNET": CashAddressVersion("bchtest", 11, Network.test),
        "P2PKH-TESTNET": CashAddressVersion("bchtest", 0, Network.test),
        "P2SH20-REGTEST": CashAddressVersion("bchreg", 8, Network.regtest),
        "P2SH32-REGTEST": CashAddressVersion("bchreg", 11, Network.regtest),
        "P2PKH-REGTEST": CashAddressVersion("bchreg", 0, Network.regtest),
        "P2SH20-CATKN": CashAddressVersion("bitcoincash", 24, Network.main),
        "P2SH32-CATKN": CashAddressVersion("bitcoincash", 27, Network.main),
        "P2PKH-CATKN": CashAddressVersion("bitcoincash", 16, Network.main),
        "P2SH20-CATKN-TESTNET": CashAddressVersion("bchtest", 24, Network.test),
        "P2SH32-CATKN-TESTNET": CashAddressVersion("bchtest", 27, Network.test),
        "P2PKH-CATKN-TESTNET": CashAddressVersion("bchtest", 16, Network.test),
        "P2SH20-CATKN-REGTEST": CashAddressVersion("bchreg", 24, Network.regtest),
        "P2SH32-CATKN-REGTEST": CashAddressVersion("bchreg", 27, Network.regtest),
        "P2PKH-CATKN-REGTEST": CashAddressVersion("bchreg", 16, Network.regtest),
    }

    VERSION_SUFFIXES: dict[str, str] = {
        "bitcoincash": "",
        "bchtest": "-TESTNET",
        "bchreg": "-REGTEST",
    }

    ADDRESS_TYPES: dict[int, str] = {
        0: "P2PKH",
        8: "P2SH20",
        11: "P2SH32",
        16: "P2PKH-CATKN",
        24: "P2SH20-CATKN",
        27: "P2SH32-CATKN",
    }

    def __init__(self, version: str, payload: list[int]):
        if version not in Address.VERSIONS:
            raise ValueError("Invalid address version provided")

        self.version = version
        self.payload = payload
        self.prefix = Address.VERSIONS[self.version].prefix

    def __str__(self):
        return (
            f"version: {self.version}\npayload: {self.payload}\nprefix: {self.prefix}"
        )

    def __repr__(self):
        return f"Address('{self.cash_address()}')"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.cash_address() == other
        elif isinstance(other, Address):
            return self.cash_address() == other.cash_address()
        else:
            raise ValueError(
                "Address can be compared to a string address or an instance of Address"
            )

    def cash_address(self) -> str:
        """
        Generate CashAddr of the Address
        """
        version_bit = Address.VERSIONS[self.version].version_bit
        payload = [version_bit] + self.payload
        payload = convertbits(payload, 8, 5)
        assert payload is not None, "Error converting payload"
        checksum = calculate_checksum(self.prefix, payload)
        return self.prefix + ":" + b32encode(payload + checksum)

    @property
    def scriptcode(self) -> bytes:
        """
        Generate the locking script of the Address
        """
        if "P2PKH" in self.version:
            return (
                OpCodes.OP_DUP.binary
                + OpCodes.OP_HASH160.binary
                + OpCodes.OP_DATA_20.binary
                + bytes(self.payload)
                + OpCodes.OP_EQUALVERIFY.binary
                + OpCodes.OP_CHECKSIG.binary
            )
        if "P2SH20" in self.version:
            return (
                OpCodes.OP_HASH160.binary
                + OpCodes.OP_DATA_20.binary
                + bytes(self.payload)
                + OpCodes.OP_EQUAL.binary
            )
        if "P2SH32" in self.version:
            return (
                OpCodes.OP_HASH256.binary
                + OpCodes.OP_DATA_32.binary
                + bytes(self.payload)
                + OpCodes.OP_EQUAL.binary
            )
        raise ValueError("Locking script not implemented for this address type")

    @classmethod
    def from_script(cls, scriptcode: bytes, network: Network = Network.main) -> Address:
        """
        Generate Address from a locking script

        :param scriptcode: The locking script
        :param network: Network — :attr:`~bitcash.types.Network.main`,
            :attr:`~bitcash.types.Network.test`, or :attr:`~bitcash.types.Network.regtest`
        :returns: Instance of :class:~bitcash.cashaddress.Address
        """
        net_suffix = (
            "-TESTNET" if network == Network.test else
            "-REGTEST" if network == Network.regtest else
            ""
        )
        # cashtoken suffix
        catkn = ""
        if scriptcode.startswith(OpCodes.OP_TOKENPREFIX.binary):
            catkn = "-CATKN"
            stream = io.BytesIO(scriptcode[33:])

            token_bitfield = stream.read(1).hex()
            # 4 bit prefix
            _ = bin(int(token_bitfield[0], 16))[2:]
            _ = "0" * (4 - len(_)) + _
            prefix_structure = [bit == "1" for bit in _]
            if prefix_structure[1]:
                # has commitment length
                length = varint_to_int(stream)
                _ = stream.read(length)
            if prefix_structure[3]:
                # has amount
                _ = varint_to_int(stream)
            # only use locking script for the rest
            scriptcode = stream.read()

        # P2PKH
        if len(scriptcode) == 25:
            if scriptcode.startswith(
                OpCodes.OP_DUP.binary
                + OpCodes.OP_HASH160.binary
                + OpCodes.OP_DATA_20.binary
            ) and scriptcode.endswith(
                OpCodes.OP_EQUALVERIFY.binary + OpCodes.OP_CHECKSIG.binary
            ):
                return cls("P2PKH" + catkn + net_suffix, list(scriptcode[3:23]))
        # P2SH20
        if len(scriptcode) == 23:
            if scriptcode.startswith(
                OpCodes.OP_HASH160.binary + OpCodes.OP_DATA_20.binary
            ) and scriptcode.endswith(OpCodes.OP_EQUAL.binary):
                return cls("P2SH20" + catkn + net_suffix, list(scriptcode[2:22]))
        # P2SH32
        if len(scriptcode) == 35:
            if scriptcode.startswith(
                OpCodes.OP_HASH256.binary + OpCodes.OP_DATA_32.binary
            ) and scriptcode.endswith(OpCodes.OP_EQUAL.binary):
                return cls("P2SH32" + catkn + net_suffix, list(scriptcode[2:34]))
        raise ValueError("Unknown script")

    @classmethod
    def from_string(cls, address: str) -> Address:
        """
        Generate Address from a cashadress string

        :param scriptcode: The cashaddress string
        :returns: Instance of :class:~bitcash.cashaddress.Address
        """
        try:
            address = str(address)
        except Exception:
            raise InvalidAddress("Expected string as input")

        if address.upper() != address and address.lower() != address:
            raise InvalidAddress(
                "Cash address contains uppercase and lowercase characters"
            )

        address = address.lower()
        colon_count = address.count(":")
        if colon_count == 0:
            raise InvalidAddress("Cash address is missing prefix")
        if colon_count > 1:
            raise InvalidAddress("Cash address contains more than one colon character")

        prefix, base32string = address.split(":")
        decoded = b32decode(base32string)

        if not verify_checksum(prefix, decoded):
            raise InvalidAddress(
                "Bad cash address checksum for address {}".format(address)
            )
        converted = convertbits(decoded, 5, 8)

        try:
            assert converted is not None, "Error converting payload bits"
            version = cls.ADDRESS_TYPES[converted[0]]
        except (KeyError, AssertionError) as e:
            raise InvalidAddress(f"Could not determine address version: {e}")

        version += cls.VERSION_SUFFIXES[prefix]

        payload = converted[1:-6]
        return cls(version, payload)


def parse_cashaddress(data: str) -> tuple[Optional[Address], dict[str, Any]]:
    """Parse CashAddress address URI, with params attached

    :param data: Cashaddress uri to be parsed
    :returns: cashaddress address, and parameters

    >>> parse_cashaddress(
            'bchtest:qzvsaasdvw6mt9j2rs3gyps673gj86flev3z0s40ln?'
            'amount=0.1337&label=Satoshi-Nakamoto&message=Donation%20xyz'
        )
    (<bitcash.cashaddress.Address>,
     {'amount': '0.1337',
      'label': 'Satoshi-Nakamoto',
      'message': 'Donation xyz'
     }
    )
    >>> parse_cashaddress(
            'bchtest:?label=Satoshi-Nakamoto&message=Donation%20xyz'
        )
    (None,
     {'label': 'Satoshi-Nakamoto',
      'message': 'Donation xyz'
     }
    )
    """
    from urllib import parse

    uri = parse.urlparse(data)
    if uri.scheme not in Address.VERSION_SUFFIXES:
        raise InvalidAddress("Invalid address scheme")

    if uri.path == "":
        address = None
    else:
        address = Address.from_string(f"{uri.scheme}:{uri.path}")
    query: dict[str, Any] = parse.parse_qs(uri.query)

    for key, values in query.items():
        if len(values) == 1:
            query[key] = values[0]

    return address, query


def generate_cashaddress(address: str, params: Optional[dict[str, Any]] = None) -> str:
    """Generates cashaddress uri from address and params

    :param address: cashaddress
    :param params: dictionary of parameters to be attached
    :returns: cashaddress uri

    >>> generate_cashaddress(
            "bitcoincash:qzfyvx77v2pmgc0vulwlfkl3uzjgh5gnmqk5hhyaa6",
            {
                "amount": 0.1,
            }
    )
    "bitcoincash:qzfyvx77v2pmgc0vulwlfkl3uzjgh5gnmqk5hhyaa6?amount=0.1"
    >>> generate_cashaddress(
            "bitcoincash:",
            {"message": "Satoshi Nakamoto"}
    )
    "bitcoincash:?message=Satoshi%20Nakamoto"
    """
    from urllib import parse

    uri = parse.urlparse(address)
    if uri.path != "":
        # testing address
        _ = Address.from_string(f"{uri.scheme}:{uri.path}")
    elif uri.scheme not in Address.VERSION_SUFFIXES:
        raise InvalidAddress("Invalid address scheme")

    if params is None:
        return uri.geturl()

    param_list: list[tuple[str, Any]] = []
    for key, values in params.items():
        if isinstance(values, str) or not hasattr(values, "__iter__"):
            values = [values]
        for value in values:
            param_list.append((key, value))

    query = parse.urlencode(param_list)
    uri = uri._replace(query=query)

    return uri.geturl()
