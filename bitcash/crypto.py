from hashlib import new, sha256 as _sha256, sha512 as _sha512
import base64
import hmac

import pyaes
from coincurve import PrivateKey as ECPrivateKey, PublicKey as ECPublicKey


def sha256(bytestr):
    return _sha256(bytestr).digest()


def double_sha256(bytestr):
    return _sha256(_sha256(bytestr).digest()).digest()


def double_sha256_checksum(bytestr):
    return double_sha256(bytestr)[:4]


def ripemd160_sha256(bytestr):
    return new("ripemd160", sha256(bytestr)).digest()


hash160 = ripemd160_sha256


def sha512(bytestr):
    return _sha512(bytestr).digest()


# ECIES encryption/decryption methods; AES-128-CBC with PKCS7 is used
# as the cipher; hmac-sha256 is used as the mac
# Implementation follows the Electron-Cash implementaion of the same
def aes_encrypt_with_iv(key, iv, data):
    """Provides AES-CBC encryption of data with key and iv

    :param key: key for the encryption
    :type key: ``bytes``
    :param iv: Initialisation vector for the encryption
    :type iv: ``bytes``
    :param data: the data to be encrypted
    :type data: ``bytes``
    """
    aes_cbc = pyaes.AESModeOfOperationCBC(key, iv=iv)
    aes = pyaes.Encrypter(aes_cbc)
    # empty aes.feed() flushes buffer
    return aes.feed(data) + aes.feed()


def aes_decrypt_with_iv(key, iv, data):
    """Provides AES-CBC decryption of data with key and iv

    :param key: key for the decryption
    :type key: ``bytes``
    :param iv: Initialisation vector for the decryption
    :type iv: ``bytes``
    :param data: the data to be decrypted
    :type data: ``bytes``
    :raises ValueError: if incorrect ``key`` or ``iv`` give a padding error
                        during decryption
    """
    # assert_bytes(key, iv, data)
    aes_cbc = pyaes.AESModeOfOperationCBC(key, iv=iv)
    aes = pyaes.Decrypter(aes_cbc)
    try:
        # empty aes.feed() flushes buffer
        return aes.feed(data) + aes.feed()
    except ValueError:
        raise ValueError('Invalid key or iv')


def ecies_encrypt(message, pubkey):
    """Encrypt message with the given pubkey

    :param message: the message to be encrypted
    :type message: ``bytes``
    :param pubkey: the public key to be used
    :type pubkey: ``bytes``
    """
    pk = ECPublicKey(pubkey)

    # random key
    ephemeral = ECPrivateKey()
    ecdh_key = pk.multiply(ephemeral.secret).format()
    key = sha512(ecdh_key)

    # aes key and iv, and hmac key
    iv, key_e, key_m = key[0:16], key[16:32], key[32:]
    ciphertext = aes_encrypt_with_iv(key_e, iv, message)
    encrypted = (
        b'BIE1'
        + ephemeral.public_key.format()
        + ciphertext
    )
    mac = hmac.new(key_m, encrypted, _sha256).digest()

    return base64.b64encode(encrypted + mac)


def ecies_decrypt(encrypted, secret):
    """Decrypt the encrypted message with the given private-key secret

    :param encrypted: the message to be decrypted
    :type encrypted: ``bytes``
    :param secret: the private key secret to be used
    :type secret: ``bytes``
    :raises ValueError: if magic bytes or HMAC bytes are invalid
    """
    encrypted = base64.b64decode(encrypted)
    if len(encrypted) < 85:
        raise ValueError('Invalid cipher length')

    # splitting data
    magic = encrypted[:4]
    ephemeral_pubkey = ECPublicKey(encrypted[4:37])
    ciphertext = encrypted[37:-32]
    mac = encrypted[-32:]
    if magic != b'BIE1':
        raise ValueError('Invalid magic bytes')

    # retrieving keys
    ecdh_key = ephemeral_pubkey.multiply(secret).format()
    key = sha512(ecdh_key)
    iv, key_e, key_m = key[0:16], key[16:32], key[32:]

    # validating hmac
    if mac != hmac.new(key_m, encrypted[:-32], _sha256).digest():
        raise ValueError("Invalid HMAC bytes")

    # decrypting
    return aes_decrypt_with_iv(key_e, iv, ciphertext)
