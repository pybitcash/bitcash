import logging
from collections import namedtuple

from cashaddress import convert as cashaddress

from bitcash.crypto import double_sha256, sha256
from bitcash.exceptions import InsufficientFunds
from bitcash.format import address_to_public_key_hash
from bitcash.network.rates import currency_to_satoshi_cached
from bitcash.utils import (
    bytes_to_hex, chunk_data, hex_to_bytes, int_to_unknown_bytes, int_to_varint
)

VERSION_1 = 0x01.to_bytes(4, byteorder='little')
SEQUENCE = 0xffffffff.to_bytes(4, byteorder='little')
LOCK_TIME = 0x00.to_bytes(4, byteorder='little')

##
# Python 3 doesn't allow bitwise operators on byte objects...
HASH_TYPE = 0x01.to_bytes(4, byteorder='little')
# BitcoinCash fork ID.
SIGHASH_FORKID = 0x40.to_bytes(4, byteorder='little')
# So we just do this for now. FIXME
HASH_TYPE = 0x41.to_bytes(4, byteorder='little')
##

OP_0 = b'\x00'
OP_CHECKLOCKTIMEVERIFY = b'\xb1'
OP_CHECKSIG = b'\xac'
OP_DUP = b'v'
OP_EQUALVERIFY = b'\x88'
OP_HASH160 = b'\xa9'
OP_PUSH_20 = b'\x14'
OP_RETURN = b'\x6a'
OP_PUSHDATA1 = b'\x4c'
OP_PUSHDATA2 = b'\x4d'
OP_PUSHDATA4 = b'\x4e'

MESSAGE_LIMIT = 220


class TxIn:
    __slots__ = ('script', 'script_len', 'txid', 'txindex', 'amount')

    def __init__(self, script, script_len, txid, txindex, amount):
        self.script = script
        self.script_len = script_len
        self.txid = txid
        self.txindex = txindex
        self.amount = amount

    def __eq__(self, other):
        return (self.script == other.script and
                self.script_len == other.script_len and
                self.txid == other.txid and
                self.txindex == other.txindex and
                self.amount == other.amount)

    def __repr__(self):
        return 'TxIn({}, {}, {}, {}, {})'.format(
            repr(self.script),
            repr(self.script_len),
            repr(self.txid),
            repr(self.txindex),
            repr(self.amount)
        )


Output = namedtuple('Output', ('address', 'amount', 'currency'))


def calc_txid(tx_hex):
    return bytes_to_hex(double_sha256(hex_to_bytes(tx_hex))[::-1])


def estimate_tx_fee(n_in, n_out, satoshis, compressed, op_return_size=0):

    if not satoshis:
        return 0

    estimated_size = (
        4 +  # version
        n_in * (148 if compressed else 180)
        + len(int_to_unknown_bytes(n_in, byteorder='little'))
        + n_out * 34  # excluding op_return outputs, dealt with separately
        + len(int_to_unknown_bytes(n_out, byteorder='little'))
        + op_return_size  # grand total size of op_return outputs(s) and related field(s)
        + 4  # time lock
    )

    estimated_fee = estimated_size * satoshis

    logging.debug('Estimated fee: {} satoshis for {} bytes'.format(estimated_fee, estimated_size))

    return estimated_fee


def get_op_return_size(message, custom_pushdata=False):
    # calculate op_return size for each individual message
    if custom_pushdata is False:
        op_return_size = (
            8  # int64_t amount 0x00000000
            + len(OP_RETURN)  # 1 byte
            + len(get_op_pushdata_code(message))  # 1 byte if <75 bytes, 2 bytes if OP_PUSHDATA1...
            + len(message)  # Max 220 bytes at present
        )

    if custom_pushdata is True:
        op_return_size = (
            8  # int64_t amount 0x00000000
            + len(OP_RETURN)  # 1 byte
            + len(message)  # Unsure if Max size will be >220 bytes due to extra OP_PUSHDATA codes...
        )

    # "Var_Int" that preceeds OP_RETURN - 0xdf is max value with current 220 byte limit (so only adds 1 byte)
    op_return_size += len(int_to_varint(op_return_size))
    return op_return_size


def get_op_pushdata_code(dest):
    length_data = len(dest)
    if length_data <= 0x4c:  # (https://en.bitcoin.it/wiki/Script)
        return length_data.to_bytes(1, byteorder='little')
    elif length_data <= 0xff:
        return OP_PUSHDATA1 + length_data.to_bytes(1, byteorder='little')  # OP_PUSHDATA1 format
    elif length_data <= 0xffff:
        return OP_PUSHDATA2 + length_data.to_bytes(2, byteorder='little')  # OP_PUSHDATA2 format
    else:
        return OP_PUSHDATA4 + length_data.to_bytes(4, byteorder='little')  # OP_PUSHDATA4 format


def sanitize_tx_data(unspents, outputs, fee, leftover, combine=True, message=None, compressed=True, custom_pushdata=False):
    """
    sanitize_tx_data()

    fee is in satoshis per byte.
    """

    outputs = outputs.copy()

    for i, output in enumerate(outputs):
        dest, amount, currency = output
        # LEGACYADDRESSDEPRECATION
        # FIXME: Will be removed in an upcoming release, breaking compatibility with legacy addresses.
        dest = cashaddress.to_cash_address(dest)
        outputs[i] = (dest, currency_to_satoshi_cached(amount, currency))

    if not unspents:
        raise ValueError('Transactions must have at least one unspent.')

    # Temporary storage so all outputs precede messages.
    messages = []
    total_op_return_size = 0

    if message and (custom_pushdata is False):
        try:
            message = message.encode('utf-8')
        except AttributeError:
            pass # assume message is already a bytes-like object

        message_chunks = chunk_data(message, MESSAGE_LIMIT)

        for message in message_chunks:
            messages.append((message, 0))
            total_op_return_size += get_op_return_size(message, custom_pushdata=False)

    elif message and (custom_pushdata is True):
        if (len(message) >= 220):
            # FIXME add capability for >220 bytes for custom pushdata elements
            raise ValueError("Currently cannot exceed 220 bytes with custom_pushdata.")
        else:
            messages.append((message, 0))
            total_op_return_size += get_op_return_size(message, custom_pushdata=True)


    # Include return address in fee estimate.
    total_in = 0
    num_outputs = len(outputs) + 1
    sum_outputs = sum(out[1] for out in outputs)

    if combine:
        # calculated_fee is in total satoshis.
        calculated_fee = estimate_tx_fee(len(unspents), num_outputs, fee, compressed, total_op_return_size)
        total_out = sum_outputs + calculated_fee
        unspents = unspents.copy()
        total_in += sum(unspent.amount for unspent in unspents)

    else:
        unspents = sorted(unspents, key=lambda x: x.amount)

        index = 0

        for index, unspent in enumerate(unspents):
            total_in += unspent.amount
            calculated_fee = estimate_tx_fee(len(unspents[:index + 1]), num_outputs, fee, compressed, total_op_return_size)
            total_out = sum_outputs + calculated_fee

            if total_in >= total_out:
                break

        unspents[:] = unspents[:index + 1]

    remaining = total_in - total_out

    if remaining > 0:
        outputs.append((leftover, remaining))
    elif remaining < 0:
        raise InsufficientFunds('Balance {} is less than {} (including '
                                'fee).'.format(total_in, total_out))

    outputs.extend(messages)

    return unspents, outputs


def construct_output_block(outputs, custom_pushdata=False):

    output_block = b''

    for data in outputs:
        dest, amount = data

        # Real recipient
        if amount:
            script = (OP_DUP + OP_HASH160 + OP_PUSH_20 +
                      address_to_public_key_hash(dest) +
                      OP_EQUALVERIFY + OP_CHECKSIG)

            output_block += amount.to_bytes(8, byteorder='little')

        # Blockchain storage
        else:
            if custom_pushdata is False:
                script = OP_RETURN + get_op_pushdata_code(dest) + dest

                output_block += b'\x00\x00\x00\x00\x00\x00\x00\x00'

            elif custom_pushdata is True:
                # manual control over number of bytes in each batch of pushdata
                if type(dest) != bytes:
                    raise TypeError("custom pushdata must be of type: bytes")
                else:
                    script = (OP_RETURN + dest)

                output_block += b'\x00\x00\x00\x00\x00\x00\x00\x00'

        # Script length in wiki is "Var_int" but there's a note of "modern BitcoinQT" using a more compact "CVarInt"
        # CVarInt is what I believe we have here - No changes made. If incorrect - only breaks if 220 byte limit is increased.
        output_block += int_to_unknown_bytes(len(script), byteorder='little')
        output_block += script

    return output_block


def construct_input_block(inputs):

    input_block = b''
    sequence = SEQUENCE

    for txin in inputs:
        input_block += (
            txin.txid +
            txin.txindex +
            txin.script_len +
            txin.script +
            sequence
        )

    return input_block


def create_p2pkh_transaction(private_key, unspents, outputs, custom_pushdata=False):

    public_key = private_key.public_key
    public_key_len = len(public_key).to_bytes(1, byteorder='little')

    scriptCode = private_key.scriptcode
    scriptCode_len = int_to_varint(len(scriptCode))

    version = VERSION_1
    lock_time = LOCK_TIME
    # sequence = SEQUENCE
    hash_type = HASH_TYPE
    input_count = int_to_unknown_bytes(len(unspents), byteorder='little')
    output_count = int_to_unknown_bytes(len(outputs), byteorder='little')

    output_block = construct_output_block(outputs, custom_pushdata=custom_pushdata)

    # Optimize for speed, not memory, by pre-computing values.
    inputs = []
    for unspent in unspents:
        script = hex_to_bytes(unspent.script)
        script_len = int_to_unknown_bytes(len(script), byteorder='little')
        txid = hex_to_bytes(unspent.txid)[::-1]
        txindex = unspent.txindex.to_bytes(4, byteorder='little')
        amount = unspent.amount.to_bytes(8, byteorder='little')

        inputs.append(TxIn(script, script_len, txid, txindex, amount))

    hashPrevouts = double_sha256(b''.join([i.txid+i.txindex for i in inputs]))
    hashSequence = double_sha256(b''.join([SEQUENCE for i in inputs]))
    hashOutputs = double_sha256(output_block)

    # scriptCode_len is part of the script.
    for i, txin in enumerate(inputs):
        to_be_hashed = (
            version +
            hashPrevouts +
            hashSequence +
            txin.txid +
            txin.txindex +
            scriptCode_len +
            scriptCode +
            txin.amount +
            SEQUENCE +
            hashOutputs +
            lock_time +
            hash_type
        )
        hashed = sha256(to_be_hashed)  # BIP-143: Used for Bitcoin Cash

        # signature = private_key.sign(hashed) + b'\x01'
        signature = private_key.sign(hashed) + b'\x41'

        script_sig = (
            len(signature).to_bytes(1, byteorder='little') +
            signature +
            public_key_len +
            public_key
        )

        inputs[i].script = script_sig
        inputs[i].script_len = int_to_unknown_bytes(len(script_sig), byteorder='little')

    return bytes_to_hex(
        version +
        input_count +
        construct_input_block(inputs) +
        output_count +
        output_block +
        lock_time
    )
