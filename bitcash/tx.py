# Hello, world.

from bitcash.format import *
from bitcash.utils import (
    int_to_unknown_bytes,
    hex_to_bytes
)

class FunctionalityNotYetImplemented(Exception):
    pass


SEQUENCE = 0xFFFFFFFF .to_bytes(4, byteorder="little")

OP_0 = b"\x00"
OP_CHECKLOCKTIMEVERIFY = b"\xb1"
OP_CHECKSIG = b"\xac"
OP_DUP = b"v"
OP_EQUALVERIFY = b"\x88"
OP_HASH160 = b"\xa9"
OP_PUSH_20 = b"\x14"
OP_RETURN = b"\x6a"
OP_PUSHDATA1 = b"\x4c"
OP_PUSHDATA2 = b"\x4d"
OP_PUSHDATA4 = b"\x4e"

MESSAGE_LIMIT = 220


class Transaction:

    def __init__(
        self,
        txid=None,
        inputs=None,
        outputs=None,
        blockheight=None,
        valueIn=None,
        valueOut=None,
        message=None,
        fees=None
        ):
        self._txid = txid
        self._inputs = inputs
        self._outputs = outputs
        self._blockheight = blockheight
        self._valueIn = valueIn
        self._valueOut = valueOut
        self._message = message
        self._fees = fees
        # self._slp = False
    
    # @classmethod
    # def from_outputs(self, unspents, outputs):
    #     return Transaction(outputs)

    @classmethod
    def create(outputs):
        return Transaction(outputs)

    # @property
    # def isSLPTransaction(self):
    #     return self._slp

    @property
    def txInputCount(self):
        return len(self._inputs)

    @property
    def txOutputCount(self):
        return len(self._outputs)
    
    def get_inputs(self):
        # TODO: finish
        raise FunctionalityNotYetImplemented(
            "This function still needs to be implemented."
        )

    def get_outputs(self):
        # TODO: finish
        raise FunctionalityNotYetImplemented(
            "This function still needs to be implemented."
        )

    def estimate_fee(self):
        # TODO: finish
        raise FunctionalityNotYetImplemented(
            "This function still needs to be implemented."
        )

    def calc_txid(self):
        # TODO: finish
        raise FunctionalityNotYetImplemented(
            "This function still needs to be implemented."
        )

    def to_hex(self):
        # TODO: finish
        raise FunctionalityNotYetImplemented(
            "This function still needs to be implemented."
        )


class TransactionInput:

    def __init__(
        self,
        previousTransactionID,
        previousTransactionVout,
        previousTransactionAmount,
        toCashAddress, # This may not be useful.
        unlockingScript,
        sequence,
        ):
        self._previousTransactionID = previousTransactionID
        self._previousTransactionVout = previousTransactionVout
        self._previousTransactionAmount = previousTransactionAmount
        self._toCashAddress = toCashAddress
        self._unlockingScript = unlockingScript
        self._slp = False
        self._slp_amount = None
        self._is_slp_minting_baton = False
        self._sequence = sequence

        self._coinbase = None # Not currently functional
    
    @property
    def isCoinbase(self):
        # Coinbase doesn't currently work, but leaving
        # this function/property here for future use
        return False if self._coinbase is None else True

    @property
    def scriptLength(self):
        if not self._unlockingScript:
            return None
        return int_to_unknown_bytes(len(self._unlockingScript), byteorder="little")
        return len(self._unlockingScript)

    def to_hex(self):
        hex_block = b""
        sequence = SEQUENCE

        hex_block += (
            self._previousTransactionID +
            self._previousTransactionVout +
            self.scriptLength +
            self._unlockingScript +
            sequence
        )
        return hex_block

    @classmethod
    def from_coinbase(cls, coinbase, sequence):
        # Coinbase doesn't currently work, but leaving
        # this function/property here for future use
        t = TransactionInput(
            previousTransactionID = None,
            previousTransactionVout = None,
            previousTransactionAmount = None,
            toCashAddress = None,
            unlockingScript = None,
            sequence=sequence,
        )
        t._coinbase = coinbase
        return t

    def from_unspent(cls, private_key, unspent):

        script = hex_to_bytes(unspent.script)
        script_len = int_to_unknown_bytes(len(script), byteorder="little")
        txid = hex_to_bytes(unspent.txid)[::-1]
        txindex = unspent.txindex.to_bytes(4, byteorder="little")
        amount = unspent.amount.to_bytes(8, byteorder="little")


        return TransactionInput(
            previousTransactionID,
            previousTransactionVout,
            previousTransactionAmount,
            toCashAddress, # This may not be useful.
            unlockingScript,
            sequence,
        )


class TransactionOutput:
    def __init__(
        self,
        address=None,
        amount=None,
        lockingScript=None
        ):

        self._amount: int = amount
        self._address: str = address
        self._lockingScript: str = lockingScript

        self._op_return: str = None
        if address is None and lockingScript is not None:
            if lockingScript.startswith("OP_RETURN "):
                self._op_return = asm[10:]


    def message(self):
        """Attempt to decode the op_return value (if there is one) as a UTF-8 string."""

        if self._op_return is None:
            return None

        return bytearray.fromhex(self._op_return).decode("utf-8")
    
    def to_hex(self):
        block_hex = b""

        if self._amount:
            script = (
                OP_DUP
                + OP_HASH160
                + OP_PUSH_20
                + address_to_public_key_hash(self._address)
                + OP_EQUALVERIFY
                + OP_CHECKSIG
            )
            block_hex += self._amount.to_bytes(8, byteorder="little")

        else:
            # Handling OP_RETURNs goes here
            raise FunctionalityNotYetImplemented(
                "This function still needs to be implemented."
            )

            # if custom_pushdata is False:
            #     script = OP_RETURN + get_op_pushdata_code(dest) + dest

            #     output_block += b"\x00\x00\x00\x00\x00\x00\x00\x00"

            # elif custom_pushdata is True:
            #     # manual control over number of bytes in each batch of pushdata
            #     if type(dest) != bytes:
            #         raise TypeError("custom pushdata must be of type: bytes")
            #     else:
            #         script = OP_RETURN + dest

            #     output_block += b"\x00\x00\x00\x00\x00\x00\x00\x00"

    @property
    def scriptLength(self):
        if not self._lockingScript:
            return None
        # This may not be in the right format
        return len(self._lockingScript)
