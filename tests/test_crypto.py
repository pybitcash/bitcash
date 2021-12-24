import pytest

from bitcash.crypto import (
    aes_encrypt_with_iv,
    aes_decrypt_with_iv,
    ecies_encrypt,
    ecies_decrypt
)


KEY_AES = b'$\x99\xd7-\x10\x1aY\xa4"\xd6\x9c\x7f\x0f\xd7\x0aT'

KEY_AES2 = b'$\x99\xd7-\x10\x1aY\xa4"\xd6\x9c\x7f\x0f\xd7\x0bT'

IV = b'\\\xdf\x8c\xdd\xebA\xa6\x7f\xfa\xbfq\x0cn\xccr\xc8'

PUBKEY = (
    b"\x03=\\(u\xc9\xbd\x11hu\xa7\x1a]\xb6L\xff\xcb\x139k\x16=\x03\x9b"
    + b"\x1d\x93'\x82H\x91\x80C4"
)

SECRET = (
    b'\xc2\x8a\x9f\x80s\x8fw\rRx\x03\xa5f\xcfo\xc3\xed\xf6\xce\xa5\x86'
    + b'\xc4\xfcJR#\xa5\xady~\x1a\xc3'
)

SECRET2 = (
    b'\xc2\x8a\x9f\x80s\x8fw\rRx\x03\xa5f\xcfo\xc3\xed\xf6\xce\xa5\x86'
    + b'\xc4\xfcJR#\xa5\xady~\x1a\xc4'
)


class TestAes:
    def test_aes_success(self):
        message = b'test'
        encrypted_message = aes_encrypt_with_iv(KEY_AES, IV, message)
        decrypted_message = aes_decrypt_with_iv(KEY_AES, IV, encrypted_message)
        assert message == decrypted_message

    def test_aes_fail(self):
        message = b'test'
        encrypted_message = aes_encrypt_with_iv(KEY_AES, IV, message)
        with pytest.raises(ValueError):
            decrypted_message = aes_decrypt_with_iv(KEY_AES2,
                                                    IV,
                                                    encrypted_message)


class TestEcies:
    def test_ecies_success(self):
        message = b'test'
        encrypted_message = ecies_encrypt(message, PUBKEY)
        decrypted_message = ecies_decrypt(encrypted_message, SECRET)
        assert message == decrypted_message

    def test_ecies_fail(self):
        message = b'test'
        encrypted_message = ecies_encrypt(message, PUBKEY)
        with pytest.raises(ValueError):
            decrypted_message = ecies_decrypt(encrypted_message, SECRET2)
