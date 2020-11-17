from coincurve import verify_signature as _vs

from bitcash.base58 import b58decode_check, b58encode_check
from bitcash.crypto import (
    ripemd160_sha256, convertbits, 
    calculate_checksum, verify_checksum,
    b32encode, b32decode
)
from bitcash.curve import x_to_y
from bitcash.exceptions import InvalidAddress

MAIN_PUBKEY_HASH = b'\x00'
MAIN_SCRIPT_HASH = b'\x05'
MAIN_PRIVATE_KEY = b'\x80'
MAIN_BIP32_PUBKEY = b'\x04\x88\xb2\x1e'
MAIN_BIP32_PRIVKEY = b'\x04\x88\xad\xe4'

TEST_PUBKEY_HASH = b'\x6f'
TEST_SCRIPT_HASH = b'\xc4'
TEST_PRIVATE_KEY = b'\xef'
TEST_BIP32_PUBKEY = b'\x045\x87\xcf'
TEST_BIP32_PRIVKEY = b'\x045\x83\x94'

REGTEST_PUBKEY_HASH = TEST_PUBKEY_HASH
REGTEST_SCRIPT_HASH = TEST_SCRIPT_HASH
REGTEST_PRIVATE_KEY = TEST_PRIVATE_KEY
REGTEST_BIP32_PUBKEY = TEST_BIP32_PUBKEY
REGTEST_BIP32_PRIVKEY = TEST_BIP32_PRIVKEY

PUBLIC_KEY_UNCOMPRESSED = b'\x04'
PUBLIC_KEY_COMPRESSED_EVEN_Y = b'\x02'
PUBLIC_KEY_COMPRESSED_ODD_Y = b'\x03'
PRIVATE_KEY_COMPRESSED_PUBKEY = b'\x01'


class Address:
    VERSIONS = {
        'P2SH': {
            'prefix': 'bitcoincash',
            'version_bit': 8,
            'network': 'mainnet'
        },
        'P2PKH': {
            'prefix': 'bitcoincash',
            'version_bit': 0,
            'network': 'mainnet'
        },
        'P2SH-TESTNET': {
            'prefix': 'bchtest',
            'version_bit': 8,
            'network': 'testnet'
        },
        'P2PKH-TESTNET': {
            'prefix': 'bchtest',
            'version_bit': 0,
            'network': 'testnet'
        },
        'P2SH-REGTEST': {
            'prefix': 'bchreg',
            'version_bit': 8,
            'network': 'regtest'
        },
        'P2PKH-REGTEST': {
            'prefix': 'bchreg',
            'version_bit': 0,
            'network': 'regtest'
        }
    }

    VERSION_SUFFIXES = {
        'bitcoincash': '',
        'bchtest': '-TESTNET',
        'bchreg': '-REGTEST'
    }

    ADDRESS_TYPES = {
        0: "P2PKH",
        8: "P2SH"
    }

    def __init__(self, version, payload):
        self.version = version
        self.payload = payload
        self.prefix = Address.VERSIONS[self.version]['prefix']

    def __str__(self):
        return 'version: {}\npayload: {}\nprefix: {}'.format(self.version, self.payload, self.prefix)

    def cash_address(self):
        version_bit = Address.VERSIONS[self.version]['version_bit']
        payload = [version_bit] + self.payload
        payload = convertbits(payload, 8, 5)
        checksum = calculate_checksum(self.prefix, payload)
        return self.prefix + ':' + b32encode(payload + checksum)

    @staticmethod
    def from_string(address):
        try:
            address = str(address)
        except Exception:
            raise InvalidAddress('Expected string as input')

        if address.upper() != address and address.lower() != address:
            raise InvalidAddress('Cash address contains uppercase and lowercase characters')

        address = address.lower()
        colon_count = address.count(':')
        if colon_count == 0:
            raise InvalidAddress('Cash address is missing prefix')
        elif colon_count > 1:
            raise InvalidAddress('Cash address contains more than one colon character')

        prefix, base32string = address.split(':')
        decoded = b32decode(base32string)

        if not verify_checksum(prefix, decoded):
            raise InvalidAddress('Bad cash address checksum for address {}'.format(address))
        converted = convertbits(decoded, 5, 8)

        try:
            version = Address.ADDRESS_TYPES[converted[0]]
        except:
            InvalidAddress('Could not determine address version')

        version += Address.VERSION_SUFFIXES[prefix]

        payload = converted[1:-6]
        return Address(version, payload)


def verify_sig(signature, data, public_key):
    """Verifies some data was signed by the owner of a public key.

    :param signature: The signature to verify.
    :type signature: ``bytes``
    :param data: The data that was supposedly signed.
    :type data: ``bytes``
    :param public_key: The public key.
    :type public_key: ``bytes``
    :returns: ``True`` if all checks pass, ``False`` otherwise.
    """
    return _vs(signature, data, public_key)


def address_to_public_key_hash(address):
    address = Address.from_string(address)

    if "P2PKH" not in address.version:
        # Bitcash currently only has support for P2PKH transaction types
        # P2SH and others will raise ValueError
        raise ValueError('Bitcash currently only supports P2PKH addresses')

    return bytes(address.payload)


def bytes_to_wif(private_key, version='main', compressed=False):

    if version == 'test':
        prefix = TEST_PRIVATE_KEY
    elif version == 'regtest':
        prefix = REGTEST_PRIVATE_KEY
    else:
        prefix = MAIN_PRIVATE_KEY

    if compressed:
        suffix = PRIVATE_KEY_COMPRESSED_PUBKEY
    else:
        suffix = b''

    private_key = prefix + private_key + suffix

    return b58encode_check(private_key)


def wif_to_bytes(wif, regtest=False):

    private_key = b58decode_check(wif)

    version = private_key[:1]

    if version == MAIN_PRIVATE_KEY:
        version = 'main'
    elif version == TEST_PRIVATE_KEY:
        # Regtest and testnet WIF formats are identical, so we
        # check the 'regtest' flag and manually set the version
        if regtest:
            version = 'regtest'
        else:
            version = 'test'
    else:
        raise ValueError('{} does not correspond to a mainnet, testnet nor '
                         'regtest address.'.format(version))

    # Remove version byte and, if present, compression flag.
    if len(wif) == 52 and private_key[-1] == 1:
        private_key, compressed = private_key[1:-1], True
    else:
        private_key, compressed = private_key[1:], False

    return private_key, compressed, version


def wif_checksum_check(wif):

    try:
        decoded = b58decode_check(wif)
    except ValueError:
        return False

    if decoded[:1] in (MAIN_PRIVATE_KEY, TEST_PRIVATE_KEY, REGTEST_PRIVATE_KEY):
        return True

    return False


def public_key_to_address(public_key, version='main'):
    # Currently Bitcash only support P2PKH (not P2SH)
    VERSIONS = {
        'main': "P2PKH",
        'test': "P2PKH-TESTNET",
        'regtest': "P2PKH-REGTEST"
    }

    try:
        version = VERSIONS[version]
    except:
        raise ValueError('Invalid version: {}'.format(version))
    # 33 bytes compressed, 65 uncompressed.
    length = len(public_key)
    if length not in (33, 65):
        raise ValueError('{} is an invalid length for a public key.'.format(length))

    payload = list(ripemd160_sha256(public_key))
    address = Address(payload=payload, version=version)
    return address.cash_address()


def public_key_to_coords(public_key):

    length = len(public_key)

    if length == 33:
        flag, x = int.from_bytes(public_key[:1], 'big'), int.from_bytes(public_key[1:], 'big')
        y = x_to_y(x, flag & 1)
    elif length == 65:
        x, y = int.from_bytes(public_key[1:33], 'big'), int.from_bytes(public_key[33:], 'big')
    else:
        raise ValueError('{} is an invalid length for a public key.'.format(length))

    return x, y


def coords_to_public_key(x, y, compressed=True):

    if compressed:
        y = PUBLIC_KEY_COMPRESSED_ODD_Y if y & 1 else PUBLIC_KEY_COMPRESSED_EVEN_Y
        return y + x.to_bytes(32, 'big')

    return PUBLIC_KEY_UNCOMPRESSED + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')


def point_to_public_key(point, compressed=True):
    return coords_to_public_key(point.x, point.y, compressed)
