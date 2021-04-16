from bitcash.exceptions import InvalidAddress

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def polymod(values):
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


def calculate_checksum(prefix, payload):
    poly = polymod(prefix_expand(prefix) + payload + [0, 0, 0, 0, 0, 0, 0, 0])
    out = list()
    for i in range(8):
        out.append((poly >> 5 * (7 - i)) & 0x1F)
    return out


def verify_checksum(prefix, payload):
    return polymod(prefix_expand(prefix) + payload) == 0


def b32decode(inputs):
    out = list()
    for letter in inputs:
        out.append(CHARSET.find(letter))
    return out


def b32encode(inputs):
    out = ""
    for char_code in inputs:
        out += CHARSET[char_code]
    return out


def convertbits(data, frombits, tobits, pad=True):
    acc = 0
    bits = 0
    ret = []
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


def prefix_expand(prefix):
    return [ord(x) & 0x1F for x in prefix] + [0]


class Address:
    VERSIONS = {
        "P2SH": {"prefix": "bitcoincash", "version_bit": 8, "network": "mainnet"},
        "P2PKH": {"prefix": "bitcoincash", "version_bit": 0, "network": "mainnet"},
        "P2SH-TESTNET": {"prefix": "bchtest", "version_bit": 8, "network": "testnet"},
        "P2PKH-TESTNET": {"prefix": "bchtest", "version_bit": 0, "network": "testnet"},
        "P2SH-REGTEST": {"prefix": "bchreg", "version_bit": 8, "network": "regtest"},
        "P2PKH-REGTEST": {"prefix": "bchreg", "version_bit": 0, "network": "regtest"},
    }

    VERSION_SUFFIXES = {"bitcoincash": "", "bchtest": "-TESTNET", "bchreg": "-REGTEST"}

    ADDRESS_TYPES = {0: "P2PKH", 8: "P2SH"}

    def __init__(self, version, payload):
        if not version in Address.VERSIONS:
            raise ValueError("Invalid address version provided")

        self.version = version
        self.payload = payload
        self.prefix = Address.VERSIONS[self.version]["prefix"]

    def __str__(self):
        return (
            f"version: {self.version}\npayload: {self.payload}\nprefix: {self.prefix}"
        )

    def cash_address(self):
        version_bit = Address.VERSIONS[self.version]["version_bit"]
        payload = [version_bit] + self.payload
        payload = convertbits(payload, 8, 5)
        checksum = calculate_checksum(self.prefix, payload)
        return self.prefix + ":" + b32encode(payload + checksum)

    @staticmethod
    def from_string(address):
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
            version = Address.ADDRESS_TYPES[converted[0]]
        except Exception:
            raise InvalidAddress("Could not determine address version")

        version += Address.VERSION_SUFFIXES[prefix]

        payload = converted[1:-6]
        return Address(version, payload)
